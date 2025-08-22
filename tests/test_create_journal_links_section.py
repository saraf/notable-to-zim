#!/usr/bin/env python3
"""
Test for create_journal_links_section function - Step 2 of TDD implementation
"""

import pytest
from datetime import datetime, timezone
from import_notable import create_journal_links_section


def test_create_journal_links_section_both_dates():
    """Test creating journal links section with both created and modified dates."""
    created = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    modified = datetime(2025, 8, 20, 11, 22, 15, tzinfo=timezone.utc)

    result = create_journal_links_section(created, modified)
    expected = (
        "\n**Journal Links:**\n"
        "* [[Journal:2025:08:18|Created on August 18 2025]]\n"
        "* [[Journal:2025:08:20|Modified on August 20 2025]]\n"
    )
    assert result == expected


def test_create_journal_links_section_created_only():
    """Test creating journal links section with only created date."""
    created = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)

    result = create_journal_links_section(created, None)
    expected = (
        "\n**Journal Links:**\n" "* [[Journal:2025:08:18|Created on August 18 2025]]\n"
    )
    assert result == expected


def test_create_journal_links_section_modified_only():
    """Test creating journal links section with only modified date."""
    modified = datetime(2025, 8, 20, 11, 22, 15, tzinfo=timezone.utc)

    result = create_journal_links_section(None, modified)
    expected = (
        "\n**Journal Links:**\n" "* [[Journal:2025:08:20|Modified on August 20 2025]]\n"
    )
    assert result == expected


def test_create_journal_links_section_same_dates():
    """Test creating journal links section when created and modified dates are identical."""
    same_date = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)

    result = create_journal_links_section(same_date, same_date)
    expected = (
        "\n**Journal Links:**\n" "* [[Journal:2025:08:18|Created on August 18 2025]]\n"
    )
    assert result == expected

    # Verify only one link is present (no duplicates)
    lines = result.strip().split("\n")
    link_lines = [line for line in lines if line.startswith("* [[")]
    assert len(link_lines) == 1
    assert "Created on" in link_lines[0]
    assert "Modified on" not in result


def test_create_journal_links_section_no_dates():
    """Test creating journal links section with no dates."""
    result = create_journal_links_section(None, None)
    assert result == ""


def test_create_journal_links_section_edge_cases():
    """Test edge cases with invalid date inputs."""
    # Both dates are invalid but not None
    result = create_journal_links_section("invalid", 12345)
    assert result == ""

    # One valid, one invalid
    valid_date = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    result = create_journal_links_section(valid_date, "invalid")
    expected = (
        "\n**Journal Links:**\n" "* [[Journal:2025:08:18|Created on August 18 2025]]\n"
    )
    assert result == expected


def test_create_journal_links_section_different_years():
    """Test with dates in different years."""
    created = datetime(2024, 12, 31, 11, 21, 28, tzinfo=timezone.utc)
    modified = datetime(2025, 1, 1, 11, 22, 15, tzinfo=timezone.utc)

    result = create_journal_links_section(created, modified)
    expected = (
        "\n**Journal Links:**\n"
        "* [[Journal:2024:12:31|Created on December 31 2024]]\n"
        "* [[Journal:2025:01:01|Modified on January 01 2025]]\n"
    )
    assert result == expected


def test_create_journal_links_section_timezone_handling():
    """Test with different timezone inputs."""
    # Both UTC
    created_utc = datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)
    # Timezone-naive (should still work)
    modified_naive = datetime(2025, 8, 20, 11, 22, 15)

    result = create_journal_links_section(created_utc, modified_naive)
    expected = (
        "\n**Journal Links:**\n"
        "* [[Journal:2025:08:18|Created on August 18 2025]]\n"
        "* [[Journal:2025:08:20|Modified on August 20 2025]]\n"
    )
    assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
