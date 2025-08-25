#!/usr/bin/env python3
"""Updated tests focusing on the refactored timezone handling."""

# Standard
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

# Local libraries
from import_notable import (
    ImportStatus,
    calculate_journal_path,
    format_journal_link,
    import_md_file,
    utc_to_local,
)

# Third-party libraries
import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


# Test the core timezone conversion function
def test_utc_to_local_with_timezone():
    """Test UTC to local time conversion with timezone-aware datetime."""
    utc_date = datetime(2025, 8, 18, 16, 21, 28, tzinfo=timezone.utc)
    local_date = utc_to_local(utc_date)

    assert local_date.tzinfo is not None
    assert local_date.tzinfo != timezone.utc


def test_utc_to_local_naive_datetime():
    """Test with naive datetime (should assume UTC)."""
    naive_date = datetime(2025, 8, 18, 16, 21, 28)
    local_date = utc_to_local(naive_date)
    assert local_date.tzinfo is not None


def test_utc_to_local_none():
    """Test with None input."""
    assert utc_to_local(None) is None


def test_utc_to_local_empty():
    """Test with empty string."""
    assert utc_to_local("") == ""


# Test journal link formatting
def test_format_journal_link_with_timezone_conversion():
    """Test formatting journal links with timezone conversion."""
    utc_date = datetime(2025, 8, 18, 23, 21, 28, tzinfo=timezone.utc)

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_date = datetime(2025, 8, 18, 18, 21, 28)
        mock_utc_to_local.return_value = local_date

        result = format_journal_link(utc_date, "Created")
        expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
        assert result == expected
        mock_utc_to_local.assert_called_once_with(utc_date)


def test_format_journal_link_date_boundary():
    """Test journal links when UTC and local dates differ."""
    utc_date = datetime(2025, 8, 19, 2, 0, 0, tzinfo=timezone.utc)

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_date = datetime(2025, 8, 18, 21, 0, 0)
        mock_utc_to_local.return_value = local_date

        result = format_journal_link(utc_date, "Created")
        expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
        assert result == expected


# Test the new calculate_journal_path function
def test_calculate_journal_path_same_day():
    """Test journal path calculation when UTC and local are same day."""
    journal_dir = Path("journal")
    utc_time = datetime(2025, 8, 18, 16, 30, 0, tzinfo=timezone.utc)

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_time = datetime(2025, 8, 18, 11, 30, 0)  # 5 hours behind, same day
        mock_utc_to_local.return_value = local_time

        result = calculate_journal_path(utc_time, journal_dir)
        expected = journal_dir / "2025" / "08" / "18.txt"

        assert result == expected
        mock_utc_to_local.assert_called_once_with(utc_time)


def test_calculate_journal_path_timezone_boundary():
    """Test when UTC and local dates are different days."""
    journal_dir = Path("journal")
    utc_time = datetime(2025, 8, 19, 2, 0, 0, tzinfo=timezone.utc)  # 2 AM UTC

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_time = datetime(2025, 8, 18, 21, 0, 0)  # 9 PM previous day
        mock_utc_to_local.return_value = local_time

        result = calculate_journal_path(utc_time, journal_dir)
        expected = journal_dir / "2025" / "08" / "18.txt"  # Should use local date

        assert result == expected


def test_calculate_journal_path_forward_timezone():
    """Test when local time is next day compared to UTC."""
    journal_dir = Path("journal")
    utc_time = datetime(2025, 8, 18, 14, 0, 0, tzinfo=timezone.utc)  # 2 PM UTC

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_time = datetime(2025, 8, 19, 1, 0, 0)  # 1 AM next day (UTC+11)
        mock_utc_to_local.return_value = local_time

        result = calculate_journal_path(utc_time, journal_dir)
        expected = journal_dir / "2025" / "08" / "19.txt"  # Should use local date

        assert result == expected


def test_calculate_journal_path_year_boundary():
    """Test timezone conversion across year boundary."""
    journal_dir = Path("journal")
    utc_time = datetime(2025, 1, 1, 2, 0, 0, tzinfo=timezone.utc)  # 2 AM Jan 1

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_time = datetime(2024, 12, 31, 21, 0, 0)  # 9 PM Dec 31 previous year
        mock_utc_to_local.return_value = local_time

        result = calculate_journal_path(utc_time, journal_dir)
        expected = journal_dir / "2024" / "12" / "31.txt"  # Should use local date

        assert result == expected


# Simplified integration tests for import_md_file
def test_import_md_file_uses_calculate_journal_path(temp_dir):
    """Test that import_md_file uses the new calculate_journal_path function."""
    md_file = temp_dir / "test.md"
    raw_dir = temp_dir / "raw"
    journal_dir = temp_dir / "journal"
    used_slugs = set()

    # Create a test markdown file
    md_content = "---\ntitle: Test Note\n---\nTest content"
    md_file.write_text(md_content)

    expected_journal_path = journal_dir / "2025" / "08" / "18.txt"

    with patch("import_notable.calculate_journal_path") as mock_calc_path, patch(
        "import_notable.run_pandoc"
    ) as mock_pandoc, patch("import_notable.write_file") as mock_write_file, patch(
        "import_notable.create_zim_note"
    ) as mock_create_zim, patch(
        "import_notable.append_journal_link"
    ) as mock_append, patch(
        "import_notable.get_file_date"
    ) as mock_get_date, patch(
        "pathlib.Path.unlink"
    ) as mock_unlink:

        # Set up mocks
        mock_calc_path.return_value = expected_journal_path
        mock_pandoc.return_value = True
        mock_write_file.return_value = True
        mock_create_zim.return_value = True
        mock_append.return_value = True
        mock_unlink.return_value = None  # Mock the unlink method
        # Mock file date to avoid timestamp parsing errors
        mock_get_date.return_value = datetime(
            2025, 8, 18, 12, 0, 0, tzinfo=timezone.utc
        )

        # Mock read_file to handle both the markdown file and temp output file
        def mock_read_side_effect(path):
            if str(path).endswith(".md"):
                return md_content
            elif "temp" in str(path) and str(path).endswith(".txt"):
                return "converted zim content"
            else:
                return md_content

        with patch("import_notable.read_file", side_effect=mock_read_side_effect):
            result = import_md_file(md_file, raw_dir, journal_dir, temp_dir, used_slugs)

        assert result == ImportStatus.SUCCESS

        # Verify calculate_journal_path was called
        mock_calc_path.assert_called_once()
        # Verify append_journal_link was called with the calculated path
        mock_append.assert_called_once()
        assert mock_append.call_args[0][0] == expected_journal_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
