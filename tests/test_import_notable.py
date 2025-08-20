#!/usr/bin/env python3
"""
Fixed test cases for import_notable.py
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import yaml
import os
import sys
import subprocess
from import_notable import (
    ImportStatus, LogLevel, set_log_file, set_log_level, log_message, log_error, log_warning,
    slugify, ensure_dir, parse_yaml_front_matter, read_file, write_file, append_file,
    check_pandoc, run_pandoc, zim_header, create_journal_page, append_journal_link,
    create_zim_note, remove_duplicate_heading, parse_timestamp, get_file_date,
    needs_update, import_md_file, main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_md(temp_dir):
    """Create a sample Markdown file with YAML front matter."""
    md_file = temp_dir / "test.md"
    content = """---
title: Test Note
tags: [tag1, tag2]
created: 2023-10-01T12:00:00Z
modified: 2023-10-02T12:00:00Z
---
# Test Note
Content
"""
    md_file.write_text(content, encoding="utf-8")
    return md_file

@pytest.fixture
def zim_dir(temp_dir):
    """Create a mock Zim directory structure."""
    zim_root = temp_dir / "zim"
    journal = zim_root / "Journal" / "2023" / "10"
    raw_store = zim_root / "raw_ai_notes"
    journal.mkdir(parents=True)
    raw_store.mkdir(parents=True)
    return zim_root

@pytest.fixture
def mock_datetime():
    """Mock datetime module while preserving isinstance functionality."""
    original_datetime = datetime
    
    # Create a mock datetime class that behaves like the original for isinstance
    class MockDatetimeClass(datetime):
        @classmethod
        def now(cls, tz=None):
            return original_datetime(2023, 10, 4, tzinfo=timezone.utc)
        
        @classmethod
        def fromtimestamp(cls, timestamp, tz=None):
            return original_datetime(2023, 10, 3, tzinfo=timezone.utc)
    
    # Copy all the original datetime attributes to our mock
    for attr_name in dir(original_datetime):
        if not hasattr(MockDatetimeClass, attr_name):
            setattr(MockDatetimeClass, attr_name, getattr(original_datetime, attr_name))
    
    with patch('import_notable.datetime', MockDatetimeClass):
        yield MockDatetimeClass
        
def test_set_log_file(temp_dir):
    """Test setting the global log file."""
    log_file = temp_dir / "test.log"
    set_log_file(log_file)
    assert log_file == temp_dir / "test.log"

def test_set_log_level():
    """Test setting the global log level."""
    set_log_level("DEBUG")
    assert log_message("Test", "DEBUG") is None
    set_log_level("ERROR")
    with patch("builtins.print") as mock_print:
        log_message("Test", "INFO")
        mock_print.assert_not_called()
    with pytest.raises(ValueError):
        set_log_level("INVALID")

def test_log_message(temp_dir, capsys):
    """Test logging to console and file."""
    log_file = temp_dir / "test.log"
    set_log_file(log_file)
    set_log_level("INFO")
    log_message("Test message", "INFO")
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    assert log_file.read_text().endswith("Test message\n")

def test_log_error(temp_dir, capsys):
    """Test error logging."""
    log_file = temp_dir / "error.log"
    set_log_file(log_file)
    set_log_level("ERROR")
    log_error("Error message")
    captured = capsys.readouterr()
    assert "Error message" in captured.out
    assert log_file.read_text().endswith("Error message\n")

def test_log_warning(temp_dir, capsys):
    """Test warning logging."""
    log_file = temp_dir / "warning.log"
    set_log_file(log_file)
    set_log_level("WARNING")
    log_warning("Warning message")
    captured = capsys.readouterr()
    assert "Warning message" in captured.out
    assert log_file.read_text().endswith("Warning message\n")

def test_slugify(temp_dir):
    """Test slug generation and uniqueness."""
    used_slugs = set()
    assert slugify("Test Note", temp_dir, used_slugs) == "test_note"
    (temp_dir / "test_note.txt").touch()
    assert slugify("Test Note", temp_dir, used_slugs) == "test_note_1"
    used_slugs.add("test_note_1")
    assert slugify("Test Note", temp_dir, used_slugs) == "test_note_2"

def test_ensure_dir(temp_dir):
    """Test directory creation."""
    new_dir = temp_dir / "new" / "subdir"
    ensure_dir(new_dir)
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_parse_yaml_front_matter():
    """Test parsing YAML front matter."""
    content = """---
title: Test
tags: [tag1, tag2]
---
Body
"""
    body, metadata = parse_yaml_front_matter(content)
    assert body == "Body\n"
    assert metadata == {"title": "Test", "tags": ["tag1", "tag2"]}
    assert parse_yaml_front_matter("No YAML") == ("No YAML", {})

def test_read_file(temp_dir):
    """Test reading file content."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("Content", encoding="utf-8")
    assert read_file(file_path) == "Content"
    assert read_file(temp_dir / "nonexistent.txt") == ""

def test_write_file(temp_dir):
    """Test writing to a file."""
    file_path = temp_dir / "new" / "test.txt"
    assert write_file(file_path, "Content")
    assert file_path.read_text(encoding="utf-8") == "Content"
    with patch("import_notable.Path.open", side_effect=OSError("Error")):
        assert not write_file(file_path, "Content")

def test_append_file(temp_dir):
    """Test appending content to a file."""
    file_path = temp_dir / "test.txt"
    content = "Test content\n"
    assert append_file(file_path, content)
    assert file_path.read_text(encoding="utf-8") == content
    assert append_file(file_path, content)
    assert file_path.read_text(encoding="utf-8") == content + content

def test_check_pandoc():
    """Test checking for Pandoc installation."""
    with patch("subprocess.run", return_value=True):
        assert check_pandoc()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert not check_pandoc()

def test_run_pandoc(temp_dir):
    """Test Pandoc conversion."""
    input_path = temp_dir / "input.md"
    output_path = temp_dir / "output.txt"
    input_path.write_text("Content", encoding="utf-8")
    with patch("subprocess.run", return_value=True):
        assert run_pandoc(input_path, output_path)
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd", stderr="Error")):
        assert not run_pandoc(input_path, output_path)

def test_zim_header():
    """Test generating Zim header."""
    with patch("import_notable.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2023-10-01 12:00:00"
        header = zim_header("Test")
        assert "Content-Type: text/x-zim-wiki" in header
        assert "Wiki-Format: zim 0.6" in header
        assert "Creation-Date: 2023-10-01 12:00:00" in header
        assert "====== Test ======" in header

def test_create_journal_page(temp_dir):
    """Test creating a journal page."""
    page_path = temp_dir / "journal.txt"
    with patch("import_notable.write_file", return_value=True):
        assert create_journal_page(page_path)
    with patch("import_notable.write_file", return_value=False):
        assert not create_journal_page(page_path)

def test_append_journal_link(temp_dir):
    """Test appending journal links."""
    page_path = temp_dir / "journal.txt"
    assert append_journal_link(page_path, "Test", "raw_ai_notes:test")
    assert "* [[raw_ai_notes:test|Test]]" in page_path.read_text(encoding="utf-8")
    # Test deduplication
    assert append_journal_link(page_path, "Test", "raw_ai_notes:test")
    content = page_path.read_text(encoding="utf-8")
    assert content.count("* [[raw_ai_notes:test|Test]]") == 1

def test_create_zim_note(temp_dir):
    """Test creating a Zim note."""
    note_path = temp_dir / "note.txt"
    assert create_zim_note(note_path, "Test", "Content", ["tag1", "tag2"])
    content = note_path.read_text(encoding="utf-8")
    assert "Content-Type: text/x-zim-wiki" in content
    assert "@tag:tag1 @tag:tag2" in content
    assert "Content" in content

def test_remove_duplicate_heading():
    """Test removing duplicate headings."""
    content = "====== Test Note ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == "Content"
    content = "====== Other ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == content

def test_parse_timestamp():
    """Test parsing ISO 8601 timestamps and datetime objects."""
    ts = datetime(2023, 10, 1, tzinfo=timezone.utc)
    assert parse_timestamp(ts) == ts
    assert parse_timestamp("2023-10-01T12:00:00Z") == datetime(2023, 10, 1, 12, 0, tzinfo=timezone.utc)
    assert parse_timestamp("invalid") is None
    assert parse_timestamp(None) is None

def test_get_file_date(mock_datetime, sample_md):
    """Test getting file creation/modified dates."""
    # The mock_datetime fixture already sets up the return values
    # No need to modify mock_datetime.fromtimestamp.return_value
    
    # Test with valid metadata
    metadata = {"created": "2023-10-01T12:00:00Z"}
    result = get_file_date(sample_md, metadata, "created")
    assert result == datetime(2023, 10, 1, 12, 0, tzinfo=timezone.utc)
    
    # Test with invalid metadata - should fall back to file timestamp
    metadata = {"modified": "invalid"}
    result = get_file_date(sample_md, metadata, "modified")
    assert result == datetime(2023, 10, 3, tzinfo=timezone.utc)
    
    # Test with empty metadata - should fall back to file timestamp
    metadata = {}
    result = get_file_date(sample_md, metadata, "created")
    assert result == datetime(2023, 10, 3, tzinfo=timezone.utc)
    
def test_needs_update(sample_md, temp_dir):
    """Test checking if a file needs updating."""
    dest_path = temp_dir / "test_note.txt"
    metadata = {"modified": "2023-10-02T12:00:00Z"}
    dest_path.touch()
    os.utime(dest_path, (1696161600, 1696161600))  # 2023-10-01T12:00:00Z
    assert needs_update(sample_md, dest_path, metadata)  # Modified is newer
    metadata = {"modified": "2023-10-01T11:00:00Z"}
    assert not needs_update(sample_md, dest_path, metadata)  # Modified is older
    metadata = {}
    assert needs_update(sample_md, temp_dir / "nonexistent.txt", metadata)  # No dest file

def test_import_md_file(sample_md, zim_dir, temp_dir):
    """Test importing a single Markdown file."""
    raw_store = zim_dir / "raw_ai_notes"
    journal_root = zim_dir / "Journal"
    used_slugs = set()
    
    # Create temporary files that will be "created" by run_pandoc
    temp_input = temp_dir / "test_note.md"
    temp_output = temp_dir / "test_note.txt"
    
    # Mock the file operations to avoid actual file creation/deletion issues
    def mock_write_file(path, content):
        # Actually create the temp files when they're supposed to be created
        if "test_note.md" in str(path) or "test_note.txt" in str(path):
            path.touch()
        return True
    
    def mock_read_file(path):
        if "test_note.txt" in str(path):
            return "Content"
        # For the original sample_md file, read the actual content
        if path == sample_md:
            return sample_md.read_text()
        return "Content"
    
    def mock_unlink(self):
        # Only unlink if file exists
        if self.exists():
            os.unlink(self)
    
    with patch("import_notable.run_pandoc", return_value=True), \
         patch("import_notable.read_file", side_effect=mock_read_file), \
         patch("import_notable.write_file", side_effect=mock_write_file), \
         patch("import_notable.create_journal_page", return_value=True), \
         patch("import_notable.append_file", return_value=True), \
         patch("import_notable.zim_header", return_value="Header\n"), \
         patch.object(Path, 'unlink', mock_unlink):
        
        result = import_md_file(sample_md, raw_store, journal_root, None, temp_dir, used_slugs)
        assert result == ImportStatus.SUCCESS
    
    # Test skip case
    with patch("import_notable.needs_update", return_value=False):
        result = import_md_file(sample_md, raw_store, journal_root, None, temp_dir, used_slugs)
        assert result == ImportStatus.SKIPPED
    
    # Test error case - empty file content
    with patch("import_notable.read_file", return_value=""):
        result = import_md_file(sample_md, raw_store, journal_root, None, temp_dir, used_slugs)
        assert result == ImportStatus.ERROR