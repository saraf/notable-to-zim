#!/usr/bin/env python3
"""Test for format_journal_link function."""
# Standard Library Imports
from datetime import datetime, timezone

# Local Application/Library-specific Imports
from import_notable import format_journal_link

# Third-party Imports
import pytest


# -------------- Test Cases for format_journal_link Function --------
def test_format_journal_link_created():
    """Test formatting a created journal link."""
    date = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    result = format_journal_link(date, "Created")
    expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
    assert result == expected


def test_format_journal_link_modified():
    """Test formatting a modified journal link."""
    date = datetime(2025, 8, 20, 11, 22, 15, tzinfo=timezone.utc)
    result = format_journal_link(date, "Modified")
    expected = "[[Journal:2025:08:20|Modified on August 20 2025]]"
    assert result == expected


def test_format_journal_link_none_date():
    """Test formatting with None date returns empty string."""
    result = format_journal_link(None)
    assert result == ""


def test_format_journal_link_different_months():
    """Test formatting with different months."""
    # January
    jan_date = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = format_journal_link(jan_date, "Created")
    expected = "[[Journal:2025:01:01|Created on January 01 2025]]"
    assert result == expected

    # December
    dec_date = datetime(2025, 12, 31, 15, 30, 0, tzinfo=timezone.utc)
    result = format_journal_link(dec_date, "Modified")
    expected = "[[Journal:2025:12:31|Modified on December 31 2025]]"
    assert result == expected


def test_format_journal_link_leap_year():
    """Test formatting with leap year date."""
    leap_date = datetime(2024, 2, 29, 10, 0, 0, tzinfo=timezone.utc)
    result = format_journal_link(leap_date, "Created")
    expected = "[[Journal:2024:02:29|Created on February 29 2024]]"
    assert result == expected


def test_format_journal_link_default_type():
    """Test formatting with default link type (Created)."""
    date = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    result = format_journal_link(date)  # No link_type specified
    expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
    assert result == expected


def test_format_journal_link_edge_cases():
    """Test edge cases and error handling."""
    # Empty string link_type
    date = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    result = format_journal_link(date, "")
    expected = "[[Journal:2025:08:18| on August 18 2025]]"
    assert result == expected

    # None link_type - assume default to "Created"
    result = format_journal_link(date, None)
    expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
    assert result == expected

    # Weird link_type
    result = format_journal_link(date, "Updated")
    expected = "[[Journal:2025:08:18|Updated on August 18 2025]]"
    assert result == expected


def test_format_journal_link_invalid_date_types():
    """Test behavior with invalid date types."""
    # String that looks like a date
    result = format_journal_link("2025-08-18", "Created")
    assert result == ""

    # Integer
    result = format_journal_link(1234567890, "Created")
    assert result == ""

    # Empty string
    result = format_journal_link("", "Created")
    assert result == ""

    # Boolean False (falsy but not None)
    result = format_journal_link(False, "Created")
    assert result == ""


def test_format_journal_link_timezone_naive():
    """Test behavior with timezone-naive datetime."""
    # This is a design decision - should we accept timezone-naive dates?
    naive_date = datetime(2025, 8, 18, 11, 21, 28)  # No tzinfo
    result = format_journal_link(naive_date, "Created")
    expected = "[[Journal:2025:08:18|Created on August 18 2025]]"
    assert result == expected  # Should work fine


def test_format_journal_link_extreme_dates():
    """Test with extreme date values."""
    # Very old date
    old_date = datetime(1900, 1, 1, tzinfo=timezone.utc)
    result = format_journal_link(old_date, "Created")
    expected = "[[Journal:1900:01:01|Created on January 01 1900]]"
    assert result == expected

    # Far future date
    future_date = datetime(2099, 12, 31, tzinfo=timezone.utc)
    result = format_journal_link(future_date, "Created")
    expected = "[[Journal:2099:12:31|Created on December 31 2099]]"
    assert result == expected


# ------------------------ End Test Cases ------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
