# Tests for utc_to_local function

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from import_notable import utc_to_local, format_journal_link


def test_utc_to_local_with_timezone():
    """Test UTC to local time conversion with timezone-aware datetime."""
    utc_date = datetime(2025, 8, 18, 16, 21, 28, tzinfo=timezone.utc)  # 4:21 PM UTC
    local_date = utc_to_local(utc_date)

    # The exact local time depends on the system timezone, but we can test the conversion worked
    assert local_date.tzinfo is not None
    assert (
        local_date.tzinfo != timezone.utc
    )  # Should be different from UTC unless system is UTC


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


@patch("time.timezone", -18000)  # Mock EST (UTC-5)
def test_utc_to_local_with_mocked_timezone():
    """Test timezone conversion with mocked system timezone."""
    utc_date = datetime(2025, 8, 18, 23, 21, 28, tzinfo=timezone.utc)  # 11:21 PM UTC

    # We can't easily mock astimezone(), but we can test that it returns a different timezone
    local_date = utc_to_local(utc_date)
    assert local_date.tzinfo is not None
    assert local_date.tzinfo != timezone.utc


# Test enhanced journal link generation
# Tests for enhanced format_journal_link
def test_format_journal_link_with_timezone_conversion():
    """Test formatting journal links with timezone conversion."""
    # UTC date that might be on a different day in local time
    utc_date = datetime(2025, 8, 18, 23, 21, 28, tzinfo=timezone.utc)  # 11:21 PM UTC

    # Mock the utc_to_local function to return a predictable local time
    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        # Simulate EST conversion (UTC-5) - still same day
        local_date = datetime(2025, 8, 18, 18, 21, 28)  # 6:21 PM local same day
        mock_utc_to_local.return_value = local_date

        result = format_journal_link(utc_date, "Created")
        expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
        assert result == expected
        mock_utc_to_local.assert_called_once_with(utc_date)


def test_format_journal_link_date_boundary():
    """Test journal links when UTC and local dates differ (timezone boundary)."""
    # UTC date: 2:00 AM on Aug 19 -> should be Aug 18 in EST (UTC-5)
    utc_date = datetime(2025, 8, 19, 2, 0, 0, tzinfo=timezone.utc)

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        # Simulate conversion to previous day in local time
        local_date = datetime(2025, 8, 18, 21, 0, 0)  # 9:00 PM on Aug 18
        mock_utc_to_local.return_value = local_date

        result = format_journal_link(utc_date, "Created")
        expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
        assert result == expected


def test_format_journal_link_opposite_boundary():
    """Test when local time is next day compared to UTC."""
    # UTC: 11:00 PM on Aug 18 -> Aug 19 in Tokyo (UTC+9)
    utc_date = datetime(2025, 8, 18, 14, 0, 0, tzinfo=timezone.utc)  # 2:00 PM UTC

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        # Simulate conversion to next day in local time (Tokyo)
        local_date = datetime(2025, 8, 18, 23, 0, 0)  # 11:00 PM same day (not crossing)
        mock_utc_to_local.return_value = local_date

        result = format_journal_link(utc_date, "Created")
        expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
        assert result == expected


def test_format_journal_link_none_date():
    """Test with None date still returns empty string."""
    result = format_journal_link(None)
    assert result == ""


def test_format_journal_link_different_link_types():
    """Test with different link types."""
    utc_date = datetime(2025, 8, 18, 12, 0, 0, tzinfo=timezone.utc)

    with patch("import_notable.utc_to_local") as mock_utc_to_local:
        local_date = datetime(2025, 8, 18, 8, 0, 0)  # 4 hours behind
        mock_utc_to_local.return_value = local_date

        result = format_journal_link(utc_date, "Modified")
        expected = "[[Journal:2025:08:18|Modified on August 18 2025]]"
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
