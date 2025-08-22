#!/usr/bin/env python3
"""
Test for enhanced import_md_file function - Step 4 of TDD implementation
"""

import pytest
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from import_notable import import_md_file, ImportStatus


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
            sample_md, raw_store, journal_root, None, temp_dir, used_slugs
        )
        assert result == ImportStatus.SUCCESS


def test_import_md_file_without_metadata_dates(sample_md, zim_dirs):
    """Test importing a markdown file without dates in metadata (fallback to file dates)."""
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
            sample_md, raw_store, journal_root, None, temp_dir, used_slugs
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
            sample_md, raw_store, journal_root, None, temp_dir, used_slugs
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
            sample_md, raw_store, journal_root, None, temp_dir, used_slugs
        )
        assert result == ImportStatus.SUCCESS


def test_import_md_file_backward_compatibility(sample_md, zim_dirs):
    """Test that existing functionality still works unchanged."""
    raw_store, journal_root, temp_dir = zim_dirs
    used_slugs = set()

    md_content = """---
title: Test Note
tags: [test]
---
# Test Note
Backward compatibility test.
"""

    def mock_read_file(path):
        return md_content if path == sample_md else "Backward compatibility test."

    # Track calls to create_zim_note to ensure
