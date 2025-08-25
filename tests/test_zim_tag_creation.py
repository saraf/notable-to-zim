#!/usr/bin/env python3
"""Tests for Zim tag creation."""

from import_notable import create_tag_string_for_zim

import pytest


def test_empty_list():
    """Test empty list input."""
    assert create_tag_string_for_zim([]) == ""


def test_list_with_empty_strings():
    """Test list with empty strings."""
    assert create_tag_string_for_zim(["", ""]) == ""


def test_single_tag_normal():
    """Test single normal tag."""
    assert create_tag_string_for_zim(["tag"]) == "@tag"


def test_strip_leading_and_trailing_spaces():
    """Test stripping leading and trailing spaces."""
    assert create_tag_string_for_zim(["  tag  "]) == "@tag"


def test_multiple_tags_normal():
    """Test multiple normal tags."""
    assert create_tag_string_for_zim(["tag", "another"]) == "@tag @another"


def test_tag_with_hyphen():
    """Test tag with hyphen."""
    assert create_tag_string_for_zim(["tag-name"]) == "@tag_name"


def test_tag_with_space():
    """Test tag with space."""
    assert create_tag_string_for_zim(["tag name"]) == "@tag_name"


def test_tag_with_slash():
    """Test tag with slash."""
    assert create_tag_string_for_zim(["parent/child"]) == "@child"


def test_tag_with_multiple_slashes():
    """Test tag with multiple slashes."""
    assert create_tag_string_for_zim(["a/b/c"]) == "@c"


def test_tag_with_special_characters():
    """Test tag with special characters."""
    assert (
        create_tag_string_for_zim(["tag@name", "tag$name", "tag%name"])
        == "@tagname @tag_name @tag_name"
    )


def test_tag_with_quotes():
    """Test tag with quotes."""
    assert (
        create_tag_string_for_zim(["'tag name'", '"tag name"']) == "@tag_name @tag_name"
    )


def test_tag_with_period():
    """Test tag with period."""
    assert create_tag_string_for_zim(["tag.name"]) == "@tag_name"


def test_tag_with_comma():
    """Test tag with comma."""
    assert create_tag_string_for_zim(["tag,name"]) == "@tag_name"


def test_tag_with_colon():
    """Test tag with colon."""
    assert create_tag_string_for_zim(["tag:name"]) == "@tag_name"


def test_tag_with_semicolon():
    """Test tag with semicolon."""
    assert create_tag_string_for_zim(["tag;name"]) == "@tag_name"


def test_tag_with_question_mark():
    """Test tag with question mark."""
    assert create_tag_string_for_zim(["tag?name"]) == "@tag_name"


def test_tag_with_exclamation_mark():
    """Test tag with exclamation mark."""
    assert create_tag_string_for_zim(["tag!name"]) == "@tag_name"


def test_tag_with_plus_sign():
    """Test tag with plus sign."""
    assert create_tag_string_for_zim(["tag+name"]) == "@tag_name"


def test_tag_with_ampersand():
    """Test tag with ampersand."""
    assert create_tag_string_for_zim(["tag&name"]) == "@tag_name"


def test_tag_with_dollar_sign():
    """Test tag with dollar sign."""
    assert create_tag_string_for_zim(["tag$name"]) == "@tag_name"


def test_tag_with_percent_sign():
    """Test tag with percent sign."""
    assert create_tag_string_for_zim(["tag%name"]) == "@tag_name"


def test_tag_with_hash_sign():
    """Test tag with hash sign."""
    assert create_tag_string_for_zim(["tag#name"]) == "@tag_name"


def test_tag_with_backslash():
    """Test tag with backslash."""
    assert create_tag_string_for_zim(["tag\\name"]) == "@tag_name"


def test_mixed_tags_and_empty():
    """Test mixed tags and empty strings."""
    assert (
        create_tag_string_for_zim(["tag-name", "", "  spaced ", "hyphen-ated/slashed"])
        == "@tag_name @spaced @slashed"
    )


def test_tags_with_only_special_characters():
    """Test tags with only special characters."""
    assert create_tag_string_for_zim(["!@#$%^&*()"]) == ""


def test_tags_with_long_complex_mix():
    """Test tags with long complex mix."""
    assert (
        create_tag_string_for_zim(["complex/tag-name;with lots*of_stuff"])
        == "@tag_name_with_lots_of_stuff"
    )


def test_tags_with_multiple_issues():
    """Test tags with multiple issues."""
    assert (
        create_tag_string_for_zim([" grand/child's-tag.name! "]) == "@childs_tag_name_"
    )


def test_tag_only_slash():
    """Test tag with only slash."""
    assert create_tag_string_for_zim(["/"]) == ""


def test_tag_multiple_empty_after_split():
    """Test tag with multiple empty after split."""
    assert create_tag_string_for_zim(["/", "sub/"]) == ""


def test_tag_with_numbers():
    """Test tag with numbers."""
    assert create_tag_string_for_zim(["tag123", "a1/b2/c3"]) == "@tag123 @c3"


def test_unicode_normalization():
    """Test Unicode normalization."""
    assert create_tag_string_for_zim(["café", "naïve"]) == "@cafe @naive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
