#!/usr/bin/env python3
"""
test_import_notable.py - Pytest unit tests for import_notable.py v1.9.9
Covers all functions for importing Notable Markdown notes to Zim Wiki,
including UTC timestamp handling and journal link deduplication.
Dependencies: pytest>=7.0, pyyaml==6.0.1, python-dateutil
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
    needs_update, import_md_file, validate_paths, main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_md(tmp_path):
    """Create a sample Markdown file with YAML front matter."""
    md_file = tmp_path / "test.md"
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
def zim_dir(tmp_path):
    """Create a mock Zim directory structure."""
    zim_root = tmp_path / "zim"
    journal = zim_root / "Journal" / "2023" / "10"
    raw_store = zim_root / "raw_ai_notes"
    journal.mkdir(parents=True)
    raw_store.mkdir(parents=True)
    return zim_root

def test_set_log_file(tmp_path):
    """Test setting the global log file."""
    log_file = tmp_path / "test.log"
    set_log_file(log_file)
    assert log_file == tmp_path / "test.log"

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

def test_log_message(tmp_path, capsys):
    """Test logging to console and file."""
    log_file = tmp_path / "test.log"
    set_log_file(log_file)
    set_log_level("INFO")
    log_message("Test message", "INFO")
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    assert log_file.read_text().endswith("Test message\n")

def test_log_error(tmp_path, capsys):
    """Test error logging."""
    log_file = tmp_path / "error.log"
    set_log_file(log_file)
    set_log_level("ERROR")
    log_error("Error message")
    captured = capsys.readouterr()
    assert "Error message" in captured.out
    assert log_file.read_text().endswith("Error message\n")

def test_log_warning(tmp_path, capsys):
    """Test warning logging."""
    log_file = tmp_path / "warning.log"
    set_log_file(log_file)
    set_log_level("WARNING")
    log_warning("Warning message")
    captured = capsys.readouterr()
    assert "Warning message" in captured.out
    assert log_file.read_text().endswith("Warning message\n")

def test_slugify(temp_dir):
    """Test slug generation with and without collisions."""
    used_slugs = set()
    assert slugify("Test Note", temp_dir, used_slugs) == "test_note"
    (temp_dir / "test_note.txt").touch()
    assert slugify("Test Note", temp_dir, used_slugs) == "test_note_1"
    used_slugs.add("test_note_1")
    assert slugify("Test Note", temp_dir, used_slugs) == "test_note_2"
    assert slugify("Invalid/Name!", temp_dir, used_slugs) == "invalid_name"
    assert slugify("", temp_dir, used_slugs) == "untitled"

def test_ensure_dir(tmp_path):
    """Test directory creation."""
    new_dir = tmp_path / "new" / "nested"
    ensure_dir(new_dir)
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
    assert body == "Body"
    assert metadata == {"title": "Test", "tags": ["tag1", "tag2"]}
    assert parse_yaml_front_matter("No YAML") == ("No YAML", {})

@patch("builtins.open", new_callable=mock_open, read_data="Content")
def test_read_file(mock_file):
    """Test reading file content."""
    path = Path("dummy.txt")
    content = read_file(path)
    assert content == "Content"
    # Test UnicodeDecodeError
    mock_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
    with patch("builtins.open", new_callable=mock_open, read_data="Content") as mock_latin:
        content = read_file(path)
        assert content == "Content"
        mock_latin.assert_called_with(path, encoding="latin-1")
    # Test other errors
    mock_file.side_effect = Exception("File error")
    content = read_file(path)
    assert content == ""

@patch("builtins.open", new_callable=mock_open)
def test_write_file(mock_file, tmp_path):
    """Test writing file content."""
    path = tmp_path / "test.txt"
    assert write_file(path, "Content")
    mock_file.assert_called_with(path, "w", encoding="utf-8")
    mock_file().write.assert_called_with("Content")
    # Test failure
    mock_file.side_effect = Exception("Write error")
    assert not write_file(path, "Content")

def test_append_file(tmp_dir):
    """Test appending to file."""
    path = tmp_dir / "test.txt"
    assert append_file(path, "Line1\n")
    assert append_file(path, "Line2\n")
    assert path.read_text(encoding="utf-8") == "Line1\nLine2\n"
    # Test append failure
    with patch("builtins.open", side_effect=Exception("Append error")):
        assert not append_file(path, "Line3\n")

@patch("subprocess.run")
def test_check_pandoc(mock_run):
    """Test Pandoc availability check."""
    assert check_pandoc()
    mock_run.assert_called_with(
        ["pandoc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )
    mock_run.side_effect = subprocess.CalledProcessError(1, ["pandoc"])
    assert not check_pandoc()
    mock_run.side_effect = FileNotFoundError
    assert not check_pandoc()

@patch("subprocess.run")
@patch("pathlib.PureWindowsPath")
def test_run_pandoc(mock_path, mock_run, tmp_path):
    """Test Pandoc conversion."""
    input_md = tmp_path / "input.md"
    output_txt = tmp_path / "output.txt"
    mock_path.return_value.as_posix.return_value = str(output_txt)
    assert run_pandoc(input_md, output_txt)
    mock_run.assert_called_with(
        ["pandoc", "-f", "markdown-smart", "-t", "zimwiki", "-o", str(output_txt), str(input_md)],
        check=True, capture_output=True, text=True
    )
    mock_run.side_effect = subprocess.CalledProcessError(1, ["pandoc"], stderr="Error")
    assert not run_pandoc(input_md, output_txt)
    mock_run.side_effect = FileNotFoundError
    assert not run_pandoc(input_md, output_txt)

@patch("import_notable.datetime")
def test_zim_header(mock_datetime):
    """Test Zim header generation."""
    mock_datetime.now.return_value.strftime.return_value = "2023-10-01T12:00:00+0000"
    header = zim_header("Test")
    assert "Content-Type: text/x-zim-wiki" in header
    assert "Wiki-Format: zim 0.6" in header
    assert "Creation-Date: 2023-10-01T12:00:00+0000" in header
    assert "====== Test ======" in header

def test_create_journal_page(tmp_dir):
    """Test creating a journal page."""
    page_path = tmp_dir / "2023" / "10" / "01.txt"
    with patch("import_notable.zim_header", return_value="Header\n"), \
         patch("import_notable.write_file", return_value=True):
        assert create_journal_page(page_path)
    assert create_journal_page(page_path)  # Already exists

def test_append_journal_link(tmp_dir):
    """Test appending journal links with deduplication."""
    page_path = tmp_dir / "2023" / "10" / "01.txt"
    page_path.parent.mkdir(parents=True)
    page_path.write_text("===== AI Notes =====\n", encoding="utf-8")
    assert append_journal_link(page_path, "Test Note", "raw_ai_notes:test_note")
    content = page_path.read_text(encoding="utf-8")
    assert "* [[raw_ai_notes:test_note|Test Note]]" in content
    # Test deduplication
    assert append_journal_link(page_path, "Test Note", "raw_ai_notes:test_note")
    content = page_path.read_text(encoding="utf-8")
    assert content.count("* [[raw_ai_notes:test_note|Test Note]]") == 1

def test_create_zim_note(tmp_dir):
    """Test creating a Zim note with header and tags."""
    note_path = tmp_dir / "raw_ai_notes" / "test_note.txt"
    with patch("import_notable.zim_header", return_value="Header\n"), \
         patch("import_notable.write_file") as mock_write:
        assert create_zim_note(note_path, "Test Note", "Content", ["tag1", "tag2"])
        mock_write.assert_called_with(
            note_path, "Header\nContent\n\n**Tags:** @tag1 @tag2\n"
        )
    # Test empty tags
    with patch("import_notable.zim_header", return_value="Header\n"), \
         patch("import_notable.write_file") as mock_write:
        assert create_zim_note(note_path, "Test Note", "Content", [])
        mock_write.assert_called_with(note_path, "Header\nContent\n\n")

def test_remove_duplicate_heading():
    """Test removing duplicate headings."""
    content = "====== Test Note ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == "Content"
    content = "====== Other Heading ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == content.strip()
    content = "====== Test Note’s Title ======\nContent"
    assert remove_duplicate_heading(content, "Test Note's Title", "test_note") == "Content"

def test_parse_timestamp():
    """Test parsing ISO 8601 timestamps and datetime objects."""
    ts = datetime(2023, 10, 1, tzinfo=timezone.utc)
    assert parse_timestamp(ts) == ts
    assert parse_timestamp("2023-10-01T12:00:00Z") == datetime(2023, 10, 1, 12, 0, tzinfo=timezone.utc)
    assert parse_timestamp("invalid") is None
    assert parse_timestamp(None) is None

@patch("import_notable.datetime")
def test_get_file_date(mock_datetime, sample_md):
    """Test getting file creation/modified dates."""
    mock_datetime.fromtimestamp.return_value = datetime(2023, 10, 3, tzinfo=timezone.utc)
    mock_datetime.now.return_value = datetime(2023, 10, 4, tzinfo=timezone.utc)
    metadata = {"created": "2023-10-01T12:00:00Z"}
    assert get_file_date(sample_md, metadata, "created") == datetime(2023, 10, 1, 12, 0, tzinfo=timezone.utc)
    metadata = {"modified": "invalid"}
    assert get_file_date(sample_md, metadata, "modified") == datetime(2023, 10, 3, tzinfo=timezone.utc)
    metadata = {}
    assert get_file_date(sample_md, metadata, "created") == datetime(2023, 10, 3, tzinfo=timezone.utc)

def test_needs_update(sample_md, tmp_dir):
    """Test checking if a file needs updating."""
    dest_path = tmp_dir / "test_note.txt"
    metadata = {"modified": "2023-10-02T12:00:00Z"}
    dest_path.touch()
    os.utime(dest_path, (1696161600, 1696161600))  # 2023-10-01T12:00:00Z
    assert needs_update(sample_md, dest_path, metadata)  # Modified is newer
    metadata = {"modified": "2023-10-01T11:00:00Z"}
    assert not needs_update(sample_md, dest_path, metadata)  # Modified is older
    metadata = {}
    assert needs_update(sample_md, tmp_dir / "nonexistent.txt", metadata)  # No dest file

def test_import_md_file(sample_md, zim_dir, tmp_dir):
    """Test importing a single Markdown file."""
    raw_store = zim_dir / "raw_ai_notes"
    journal_root = zim_dir / "Journal"
    used_slugs = set()
    with patch("import_notable.run_pandoc", return_value=True), \
         patch("import_notable.read_file", return_value="Content"), \
         patch("import_notable.write_file", return_value=True), \
         patch("import_notable.create_journal_page", return_value=True), \
         patch("import_notable.append_file", return_value=True), \
         patch("import_notable.zim_header", return_value="Header\n"):
        result = import_md_file(sample_md, raw_store, journal_root, None, tmp_dir, used_slugs)
        assert result == ImportStatus.SUCCESS
    # Test skip
    with patch("import_notable.needs_update", return_value=False):
        result = import_md_file(sample_md, raw_store, journal_root, None, tmp_dir, used_slugs)
        assert result == ImportStatus.SKIPPED
    # Test error
    with patch("import_notable.read_file", return_value=""):
        result = import_md_file(sample_md, raw_store, journal_root, None, tmp_dir, used_slugs)
        assert result == ImportStatus.ERROR

def test_validate_paths(tmp_dir):
    """Test path validation."""
    notable_dir = tmp_dir / "notable"
    zim_dir = tmp_dir / "zim"
    notable_dir.mkdir()
    zim_dir.mkdir()
    assert validate_paths(notable_dir, zim_dir)
    assert not validate_paths(tmp_dir / "nonexistent", zim_dir)
    assert not validate_paths(notable_dir, tmp_dir / "nonexistent")
    assert not validate_paths(tmp_dir / "file.txt", zim_dir)