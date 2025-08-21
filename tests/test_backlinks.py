#!/usr/bin/env python3
"""
Test for format_journal_link function - Step 1 of TDD implementation
"""

import pytest
from datetime import datetime, timezone
from import_notable import format_journal_link

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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])