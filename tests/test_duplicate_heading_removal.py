#!/usr/bin/env python3
"""Test for duplicate heading removal."""

from import_notable import remove_duplicate_heading

import pytest


# Test cases for the fix
def test_remove_duplicate_heading_underscore_variations():
    """Test handling of underscore variations in titles and slugs."""
    # Test case 1: Title has underscores removed, slug has underscores

    # Notable removed underscores
    title = "Refactor timezone calculations outside importmdfile"

    # Slug keeps underscores
    slug = "refactor_timezone_calculations_outside_import_md_file"
    content = (
        "====== Refactor timezone calculations outside "
        "importmdfile ======\n\nContent here"
    )

    result = remove_duplicate_heading(content, title, slug)
    assert result == "Content here"

    # Test case 2: Both title and slug have underscores
    title = "Test_Title_With_Underscores"
    slug = "test_title_with_underscores"
    content = "====== Test Title With Underscores ======\n\nContent here"

    result = remove_duplicate_heading(content, title, slug)
    assert result == "Content here"

    # Test case 3: Title matches slug variation (underscores removed)
    title = "Another Test Case"
    slug = "another_test_case"
    content = "====== Another Test Case ======\n\nContent here"

    result = remove_duplicate_heading(content, title, slug)
    assert result == "Content here"

    # Test case 4: No duplicate heading (should keep content as-is)
    title = "Different Title"
    slug = "different_slug"
    content = "====== Some Other Heading ======\n\nContent here"

    result = remove_duplicate_heading(content, title, slug)
    assert result == content


# Enhanced test to verify the actual bug case
def test_notable_underscore_bug_case():
    """Test the specific case described in the bug report."""
    # Original title: "**Refactor timezone calculations outside import_md_file**"
    # Notable's processed title: "Refactor timezone calculations outside importmdfile"
    # Slug would be: "refactor_timezone_calculations_outside_importmdfile"

    title = "Refactor timezone calculations outside importmdfile"
    slug = "refactor_timezone_calculations_outside_importmdfile"

    # Pandoc might generate this heading from the markdown
    content = (
        "====== Refactor timezone calculations "
        "outside importmdfile ======\n\nActual content here"
    )

    result = remove_duplicate_heading(content, title, slug)
    assert result == "Actual content here"

    # Test another variation where the heading has spaces instead of being concatenated
    # content_with_spaces = (
    #    "====== Refactor timezone "
    #    "calculations outside import_md_file ======\n\nActual content here"
    # )

    # result2 = remove_duplicate_heading(content_with_spaces, title, slug)
    # assert result2 == "Actual content here"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
