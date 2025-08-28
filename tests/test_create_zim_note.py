#!/usr/bin/env python3
"""Test for enhanced create_zim_note function - Step 3 of TDD implementation."""

# Standard Library Imports
from datetime import datetime, timezone
from unittest.mock import patch

# Local application/library imports
from import_notable import create_zim_note

# Third-party imports
import pytest


@pytest.fixture
def temp_note_path(tmp_path):
    """Create a temporary note path for testing."""
    return tmp_path / "test_note.txt"


def test_create_zim_note_with_journal_links(temp_note_path):
    """Test creating a Zim note with journal links."""
    title = "Test Note"
    content = "This is test content."
    tags = ["tag1", "tag2"]
    created = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    modified = datetime(2025, 8, 20, 11, 22, 15, tzinfo=timezone.utc)

    # Mock the helper functions to isolate what we're testing
    with patch(
        "import_notable.remove_duplicate_heading", return_value=content
    ) as mock_remove, patch(
        "import_notable.create_tag_string_for_zim", return_value="@tag1 @tag2"
    ) as mock_tags, patch(
        "import_notable.zim_header",
        return_value="Content-Type: text/x-zim-wiki\nWiki-Format: zim 0.6"
        "\n\n====== Test Note ======\n",
    ) as mock_header, patch(
        "import_notable.write_file", return_value=True
    ) as mock_write:

        result = create_zim_note(
            temp_note_path, title, content, tags, created, modified
        )

        assert result is True
        mock_write.assert_called_once()

        # Check the content that was written
        written_content = mock_write.call_args[0][1]

        # Verify all components are present
        assert "Content-Type: text/x-zim-wiki" in written_content
        assert "====== Test Note ======" in written_content
        assert "@tag1 @tag2" in written_content
        assert "[[Journal:2025:08:18|Created on August 18 2025]]" in written_content
        assert "[[Journal:2025:08:20|Modified on August 20 2025]]" in written_content
        assert "This is test content." in written_content

        # Verify helper functions were called correctly
        mock_remove.assert_called_once_with(content, title, temp_note_path.stem)
        mock_tags.assert_called_once_with(tags)
        mock_header.assert_called_once_with(title)


def test_create_zim_note_without_journal_links(temp_note_path):
    """Test creating a Zim note without journal links (backward compatibility)."""
    title = "Test Note"
    content = "This is test content."
    tags = ["tag1"]

    with patch("import_notable.remove_duplicate_heading", return_value=content), patch(
        "import_notable.create_tag_string_for_zim", return_value="@tag1"
    ), patch(
        "import_notable.zim_header", return_value="Header\n====== Test Note ======\n"
    ), patch(
        "import_notable.write_file", return_value=True
    ) as mock_write:

        # Call without journal dates (backward compatibility)
        result = create_zim_note(temp_note_path, title, content, tags)

        assert result is True
        written_content = mock_write.call_args[0][1]

        # Should not contain journal links
        assert "Journal Links:" not in written_content
        assert "[[Journal:" not in written_content
        assert "@tag1" in written_content


def test_create_zim_note_with_only_created_date(temp_note_path):
    """Test creating a Zim note with only created date."""
    title = "Test Note"
    content = "This is test content."
    tags = []
    created = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)

    with patch("import_notable.remove_duplicate_heading", return_value=content), patch(
        "import_notable.create_tag_string_for_zim", return_value=""
    ), patch(
        "import_notable.zim_header", return_value="Header\n====== Test Note ======\n"
    ), patch(
        "import_notable.write_file", return_value=True
    ) as mock_write:

        result = create_zim_note(
            temp_note_path, title, content, tags, created_date=created
        )

        assert result is True
        written_content = mock_write.call_args[0][1]

        # Should contain created link but not modified
        assert "[[Journal:2025:08:18|Created on August 18 2025]]" in written_content
        assert "Modified on" not in written_content


def test_create_zim_note_with_same_dates(temp_note_path):
    """Test creating a Zim note when created and modified dates are the same."""
    title = "Test Note"
    content = "This is test content."
    tags = ["test"]
    same_date = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)

    with patch("import_notable.remove_duplicate_heading", return_value=content), patch(
        "import_notable.create_tag_string_for_zim", return_value="@test"
    ), patch(
        "import_notable.zim_header", return_value="Header\n====== Test Note ======\n"
    ), patch(
        "import_notable.write_file", return_value=True
    ) as mock_write:

        result = create_zim_note(
            temp_note_path, title, content, tags, same_date, same_date
        )

        assert result is True
        written_content = mock_write.call_args[0][1]

        # Should only show created link, not modified (no duplicates)
        assert "[[Journal:2025:08:18|Created on August 18 2025]]" in written_content
        assert "Modified on" not in written_content

        # Count occurrences to ensure no duplicates
        assert written_content.count("Journal:2025:08:18") == 1


def test_create_zim_note_content_structure(temp_note_path):
    """Test that content is structured right: header, tags, journal links, content."""
    title = "Test Note"
    content = "This is test content."
    tags = ["tag1", "tag2"]
    created = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    modified = datetime(2025, 8, 20, 11, 22, 15, tzinfo=timezone.utc)

    with patch("import_notable.remove_duplicate_heading", return_value=content), patch(
        "import_notable.create_tag_string_for_zim", return_value="@tag1 @tag2"
    ), patch("import_notable.zim_header", return_value="HEADER\n"), patch(
        "import_notable.write_file", return_value=True
    ) as mock_write:

        result = create_zim_note(
            temp_note_path, title, content, tags, created, modified
        )
        assert result is True

        written_content = mock_write.call_args[0][1]

        # Split into sections and verify order
        lines = written_content.split("\n")

        # Find key sections
        header_idx = next(i for i, line in enumerate(lines) if "HEADER" in line)
        content_idx = next(
            i for i, line in enumerate(lines) if "This is test content" in line
        )
        journal_idx = next(
            i for i, line in enumerate(lines) if "Journal Links:" in line
        )
        tags_idx = next(i for i, line in enumerate(lines) if "@tag1 @tag2" in line)

        # Verify order: header -> tags -> journal links -> content
        assert header_idx < tags_idx < journal_idx < content_idx


def test_create_zim_note_write_failure(temp_note_path):
    """Test handling of write failure."""
    title = "Test Note"
    content = "This is test content."
    tags = []

    with patch("import_notable.remove_duplicate_heading", return_value=content), patch(
        "import_notable.create_tag_string_for_zim", return_value=""
    ), patch("import_notable.zim_header", return_value="Header\n"), patch(
        "import_notable.write_file", return_value=False
    ):  # Simulate write failure

        result = create_zim_note(temp_note_path, title, content, tags)

        assert result is False


def test_create_zim_note_invalid_dates(temp_note_path):
    """Test behavior with invalid date inputs."""
    title = "Test Note"
    content = "This is test content."
    tags = []

    with patch("import_notable.remove_duplicate_heading", return_value=content), patch(
        "import_notable.create_tag_string_for_zim", return_value=""
    ), patch("import_notable.zim_header", return_value="Header\n"), patch(
        "import_notable.write_file", return_value=True
    ) as mock_write:

        # Pass invalid dates (should be handled gracefully)
        result = create_zim_note(temp_note_path, title, content, tags, "invalid", 12345)

        assert result is True
        written_content = mock_write.call_args[0][1]

        # Should not contain journal links due to invalid dates
        assert "Journal Links:" not in written_content
        assert "[[Journal:" not in written_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
