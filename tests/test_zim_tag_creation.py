import pytest
from import_notable import create_tag_string_for_zim


def test_empty_list():
    assert create_tag_string_for_zim([]) == ""


def test_list_with_empty_strings():
    assert create_tag_string_for_zim(["", ""]) == ""


def test_single_tag_normal():
    assert create_tag_string_for_zim(["tag"]) == "@tag"


def test_strip_leading_and_trailing_spaces():
    assert create_tag_string_for_zim(["  tag  "]) == "@tag"


def test_multiple_tags_normal():
    assert create_tag_string_for_zim(["tag", "another"]) == "@tag @another"


def test_tag_with_hyphen():
    assert create_tag_string_for_zim(["tag-name"]) == "@tag_name"


def test_tag_with_space():
    assert create_tag_string_for_zim(["tag name"]) == "@tag_name"


def test_tag_with_slash():
    assert create_tag_string_for_zim(["parent/child"]) == "@child"


def test_tag_with_multiple_slashes():
    assert create_tag_string_for_zim(["a/b/c"]) == "@c"


def test_tag_with_special_characters():
    assert (
        create_tag_string_for_zim(["tag@name", "tag$name", "tag%name"])
        == "@tagname @tag_name @tag_name"
    )


def test_tag_with_quotes():
    assert (
        create_tag_string_for_zim(["'tag name'", '"tag name"']) == "@tag_name @tag_name"
    )


def test_tag_with_period():
    assert create_tag_string_for_zim(["tag.name"]) == "@tag_name"


def test_tag_with_comma():
    assert create_tag_string_for_zim(["tag,name"]) == "@tag_name"


def test_tag_with_colon():
    assert create_tag_string_for_zim(["tag:name"]) == "@tag_name"


def test_tag_with_semicolon():
    assert create_tag_string_for_zim(["tag;name"]) == "@tag_name"


def test_tag_with_question_mark():
    assert create_tag_string_for_zim(["tag?name"]) == "@tag_name"


def test_tag_with_exclamation_mark():
    assert create_tag_string_for_zim(["tag!name"]) == "@tag_name"


def test_tag_with_plus_sign():
    assert create_tag_string_for_zim(["tag+name"]) == "@tag_name"


def test_tag_with_ampersand():
    assert create_tag_string_for_zim(["tag&name"]) == "@tag_name"


def test_tag_with_dollar_sign():
    assert create_tag_string_for_zim(["tag$name"]) == "@tag_name"


def test_tag_with_percent_sign():
    assert create_tag_string_for_zim(["tag%name"]) == "@tag_name"


def test_tag_with_hash_sign():
    assert create_tag_string_for_zim(["tag#name"]) == "@tag_name"


def test_tag_with_backslash():
    assert create_tag_string_for_zim(["tag\\name"]) == "@tag_name"


def test_mixed_tags_and_empty():
    assert (
        create_tag_string_for_zim(["tag-name", "", "  spaced ", "hyphen-ated/slashed"])
        == "@tag_name @spaced @slashed"
    )


def test_tags_with_only_special_characters():
    assert create_tag_string_for_zim(["!@#$%^&*()"]) == ""


def test_tags_with_long_complex_mix():
    assert (
        create_tag_string_for_zim(["complex/tag-name;with lots*of_stuff"])
        == "@tag_name_with_lots_of_stuff"
    )


def test_tags_with_multiple_issues():
    assert (
        create_tag_string_for_zim([" grand/child's-tag.name! "]) == "@childs_tag_name_"
    )


def test_tag_only_slash():
    assert create_tag_string_for_zim(["/"]) == ""


def test_tag_multiple_empty_after_split():
    assert create_tag_string_for_zim(["/", "sub/"]) == ""


def test_tag_with_numbers():
    assert create_tag_string_for_zim(["tag123", "a1/b2/c3"]) == "@tag123 @c3"


def test_unicode_normalization():
    assert create_tag_string_for_zim(["café", "naïve"]) == "@cafe @naive"
