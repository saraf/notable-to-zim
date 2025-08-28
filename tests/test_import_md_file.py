#!/usr/bin/env python3
"""Test for enhanced import_md_file function."""

import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from import_notable import ImportStatus, import_md_file

import pytest


@pytest.fixture
def sample_md(tmp_path):
    """Create a sample markdown file for testing."""
    md_file = tmp_path / "test_note.md"
    return md_file


@pytest.fixture
def zim_dirs(tmp_path):
    """Create Zim directory structure."""
    zim_dir = tmp_path / "zim"
    raw_store = zim_dir / "raw_ai_notes"
    journal_root = zim_dir / "Journal"
    temp_dir = tmp_path / "temp"

    raw_store.mkdir(parents=True)
    journal_root.mkdir(parents=True)
    temp_dir.mkdir(parents=True)

    return raw_store, journal_root, temp_dir


def test_import_md_file_with_metadata_dates(sample_md, zim_dirs):
    """Test importing a markdown file with created/modified dates in metadata."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    # Mock file content with timestamps in metadata
    md_content = """---
title: Test Note
tags: [tag1, tag2]
created: 2025-08-18T11:21:28.694Z
modified: 2025-08-20T11:22:15.360Z
---
# Test Note
This is the content.
"""

    def mock_read_file(path):
        if path == sample_md:
            return md_content
        elif "test_note.txt" in str(path):
            return "This is the content."
        return "Content"

    def mock_create_zim_note(
        note_path, title, content, tags, created_date=None, modified_date=None
    ):
        # Verify that dates are passed correctly
        assert created_date is not None
        assert modified_date is not None
        assert created_date.year == 2025
        assert created_date.month == 8
        assert created_date.day == 18
        assert modified_date.year == 2025
        assert modified_date.month == 8
        assert modified_date.day == 20
        return True

    def mock_unlink(self):
        if self.exists():
            os.unlink(self)

    with patch("import_notable.run_pandoc", return_value=True), patch(
        "import_notable.read_file", side_effect=mock_read_file
    ), patch("import_notable.write_file", return_value=True), patch(
        "import_notable.create_zim_note", side_effect=mock_create_zim_note
    ), patch(
        "import_notable.append_journal_link", return_value=True
    ), patch.object(
        Path, "unlink", mock_unlink
    ):

        result = import_md_file(
            sample_md, raw_store, journal_root, temp_dir, used_slugs
        )
        assert result == ImportStatus.SUCCESS


def test_import_md_file_without_metadata_dates(sample_md, zim_dirs):
    """Importing a markdown file without dates in metadata (fallback: file dates)."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    # Mock file content without timestamps
    md_content = """---
title: Test Note
tags: [tag1]
---
# Test Note
Content without dates.
"""

    def mock_read_file(path):
        return md_content if path == sample_md else "Content without dates."

    def mock_get_file_date(md_file, metadata, date_type):
        # Mock file system dates
        if date_type == "created":
            return datetime(2025, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
        else:  # modified
            return datetime(2025, 8, 16, 12, 0, 0, tzinfo=timezone.utc)

    def mock_create_zim_note(
        note_path, title, content, tags, created_date=None, modified_date=None
    ):
        # Should still receive dates (from file system)
        assert created_date is not None
        assert modified_date is not None
        assert created_date.day == 15  # From mock_get_file_date
        assert modified_date.day == 16  # From mock_get_file_date
        return True

    def mock_unlink(self):
        if self.exists():
            os.unlink(self)

    with patch("import_notable.run_pandoc", return_value=True), patch(
        "import_notable.read_file", side_effect=mock_read_file
    ), patch("import_notable.write_file", return_value=True), patch(
        "import_notable.get_file_date", side_effect=mock_get_file_date
    ), patch(
        "import_notable.create_zim_note", side_effect=mock_create_zim_note
    ), patch(
        "import_notable.append_journal_link", return_value=True
    ), patch.object(
        Path, "unlink", mock_unlink
    ):

        result = import_md_file(
            sample_md, raw_store, journal_root, temp_dir, used_slugs
        )
        assert result == ImportStatus.SUCCESS


def test_import_md_file_mixed_date_sources(sample_md, zim_dirs):
    """Test importing with some dates in metadata, others from file system."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    # Mock file content with only created date in metadata
    md_content = """---
title: Test Note
created: 2025-08-18T11:21:28.694Z
---
# Test Note
Mixed date sources.
"""

    def mock_read_file(path):
        return md_content if path == sample_md else "Mixed date sources."

    def mock_get_file_date(md_file, metadata, date_type):
        # Should only be called for modified date (since created is in metadata)
        if date_type == "modified":
            return datetime(2025, 8, 19, 14, 0, 0, tzinfo=timezone.utc)
        # Should not be called for created (it's in metadata)
        return datetime(2025, 8, 18, 11, 21, 28, tzinfo=timezone.utc)

    def mock_create_zim_note(
        note_path, title, content, tags, created_date=None, modified_date=None
    ):
        # Created should be from metadata, modified from file system
        assert created_date is not None
        assert modified_date is not None
        assert created_date.day == 18  # From metadata
        assert created_date.hour == 11  # From metadata
        assert modified_date.day == 19  # From file system
        assert modified_date.hour == 14  # From file system
        return True

    def mock_unlink(self):
        if self.exists():
            os.unlink(self)

    with patch("import_notable.run_pandoc", return_value=True), patch(
        "import_notable.read_file", side_effect=mock_read_file
    ), patch("import_notable.write_file", return_value=True), patch(
        "import_notable.get_file_date", side_effect=mock_get_file_date
    ), patch(
        "import_notable.create_zim_note", side_effect=mock_create_zim_note
    ), patch(
        "import_notable.append_journal_link", return_value=True
    ), patch.object(
        Path, "unlink", mock_unlink
    ):

        result = import_md_file(
            sample_md, raw_store, journal_root, temp_dir, used_slugs
        )
        assert result == ImportStatus.SUCCESS


def test_import_md_file_invalid_metadata_dates(sample_md, zim_dirs):
    """Test importing with invalid dates in metadata (should fallback to file dates)."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    # Mock file content with invalid timestamps
    md_content = """---
title: Test Note
created: invalid-date
modified: also-invalid
---
# Test Note
Invalid metadata dates.
"""

    def mock_read_file(path):
        return md_content if path == sample_md else "Invalid metadata dates."

    def mock_get_file_date(md_file, metadata, date_type):
        # Should be called for both dates since metadata dates are invalid
        if date_type == "created":
            return datetime(2025, 8, 10, 10, 0, 0, tzinfo=timezone.utc)
        else:
            return datetime(2025, 8, 11, 12, 0, 0, tzinfo=timezone.utc)

    def mock_create_zim_note(
        note_path, title, content, tags, created_date=None, modified_date=None
    ):
        # Should receive fallback dates from file system
        assert created_date is not None
        assert modified_date is not None
        assert created_date.day == 10  # From file system
        assert modified_date.day == 11  # From file system
        return True

    def mock_unlink(self):
        if self.exists():
            os.unlink(self)

    with patch("import_notable.run_pandoc", return_value=True), patch(
        "import_notable.read_file", side_effect=mock_read_file
    ), patch("import_notable.write_file", return_value=True), patch(
        "import_notable.get_file_date", side_effect=mock_get_file_date
    ), patch(
        "import_notable.create_zim_note", side_effect=mock_create_zim_note
    ), patch(
        "import_notable.append_journal_link", return_value=True
    ), patch.object(
        Path, "unlink", mock_unlink
    ):

        result = import_md_file(
            sample_md, raw_store, journal_root, temp_dir, used_slugs
        )
        assert result == ImportStatus.SUCCESS


def test_import_md_file_creates_dual_journal_entries(sample_md, zim_dirs):
    """Test that importing creates journal entries for BOTH created AND modified dates when different."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    # Mock file content with different created/modified dates
    md_content = """---
title: Aalhad Saraf - profile
tags: [agri-iot]
created: '2025-05-16T09:45:42.464Z'
modified: '2025-05-19T08:05:07.178Z'
---
# Aalhad Saraf - profile
This is the profile content.
"""

    def mock_read_file(path):
        if path == sample_md:
            return md_content
        elif "aalhad_saraf___profile.txt" in str(path):
            return "This is the profile content."
        return "Content"

    def mock_unlink(self):
        if self.exists():
            os.unlink(self)

    # Track calls to append_journal_link to verify both dates are processed
    journal_calls = []

    def mock_append_journal_link(
        page_path, title, link, journal_date=None, section_title="AI Notes"
    ):
        # Capture the journal date for verification
        journal_calls.append(
            {
                "page_path": page_path,
                "title": title,
                "link": link,
                "journal_date": journal_date,
                "section_title": section_title,
            }
        )
        return True

    with patch("import_notable.run_pandoc", return_value=True), patch(
        "import_notable.read_file", side_effect=mock_read_file
    ), patch("import_notable.write_file", return_value=True), patch(
        "import_notable.create_zim_note", return_value=True
    ), patch(
        "import_notable.append_journal_link", side_effect=mock_append_journal_link
    ), patch.object(
        Path, "unlink", mock_unlink
    ):

        result = import_md_file(
            sample_md, raw_store, journal_root, temp_dir, used_slugs
        )

        # Should succeed
        assert result == ImportStatus.SUCCESS

        # CRITICAL: Should create TWO journal entries, not one
        assert (
            len(journal_calls) == 2
        ), f"Expected 2 journal entries, got {len(journal_calls)}"

        # Verify the journal dates are correct
        journal_dates = [call["journal_date"] for call in journal_calls]

        # Should have entries for both May 16 and May 19, 2025
        dates_found = set()
        for date in journal_dates:
            if date:
                dates_found.add((date.year, date.month, date.day))

        expected_dates = {(2025, 5, 16), (2025, 5, 19)}
        assert (
            dates_found == expected_dates
        ), f"Expected dates {expected_dates}, got {dates_found}"

        # Verify both entries point to the same note
        links = [call["link"] for call in journal_calls]
        assert all(link == "raw_ai_notes:aalhad_saraf_-_profile" for link in links)

        # Verify both entries have the same title and section
        titles = [call["title"] for call in journal_calls]
        assert all(title == "Aalhad Saraf - profile" for title in titles)

        sections = [call["section_title"] for call in journal_calls]
        assert all(section == "AI Notes" for section in sections)


def test_import_md_file_single_journal_entry_when_dates_same(sample_md, zim_dirs):
    """Test that only one journal entry is created when created and modified dates are the same."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    # Mock file content with same created/modified dates
    md_content = """---
title: Test Note
tags: [test]
created: '2025-05-16T09:45:42.464Z'
modified: '2025-05-16T09:45:42.464Z'
---
# Test Note
Same dates test.
"""

    def mock_read_file(path):
        if path == sample_md:
            return md_content
        return "Same dates test."

    def mock_unlink(self):
        if self.exists():
            os.unlink(self)

    journal_calls = []

    def mock_append_journal_link(
        page_path, title, link, journal_date=None, section_title="AI Notes"
    ):
        journal_calls.append({"journal_date": journal_date})
        return True

    with patch("import_notable.run_pandoc", return_value=True), patch(
        "import_notable.read_file", side_effect=mock_read_file
    ), patch("import_notable.write_file", return_value=True), patch(
        "import_notable.create_zim_note", return_value=True
    ), patch(
        "import_notable.append_journal_link", side_effect=mock_append_journal_link
    ), patch.object(
        Path, "unlink", mock_unlink
    ):

        result = import_md_file(
            sample_md, raw_store, journal_root, temp_dir, used_slugs
        )

        assert result == ImportStatus.SUCCESS

        # Should create only ONE journal entry when dates are the same
        assert (
            len(journal_calls) == 1
        ), f"Expected 1 journal entry when dates are same, got {len(journal_calls)}"
