#!/usr/bin/env python3
"""
test_import_notable.py - Pytest unit tests for import_notable.py v1.9.9

Part of the Notable-to-Zim project.

Tests all functions in import_notable.py to ensure correctness before refactoring.
Covers UTC timestamp handling, journal link deduplication, and Pandoc integration.
Uses pytest fixtures and mocking to isolate dependencies.

Dependencies:
- pytest>=7.0
- pyyaml==6.0.1
- python-dateutil
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import yaml
import os
import sys
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
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_md(temp_dir):
    """Create a sample Markdown file with YAML front matter."""
    sample_md = temp_dir / "notable" / "test_note.md"
    sample_md.parent.mkdir()
    content = """---
title: Test Note
tags: [test]
created: '2025-08-18T18:10:50.127Z'
modified: '2025-08-19T15:00:00.000Z'
---
# Test Note
Content here.
"""
    sample_md.write_text(content, encoding="utf-8")
    return sample_md

@pytest.fixture
def zim_dir(temp_dir):
    """Create a Zim directory structure."""
    zim_dir = temp_dir / "zim"
    zim_dir.mkdir()
    return zim_dir

def test_set_log_file(temp_dir):
    """Test setting the global log file."""
    log_file = temp_dir / "test.log"
    set_log_file(log_file)
    from import_notable import _log_file
    assert _log_file == log_file

def test_set_log_level():
    """Test setting the log level."""
    set_log_level("DEBUG")
    from import_notable import _log_level
    assert _log_level == LogLevel.DEBUG
    with pytest.raises(ValueError, match="Invalid log level: INVALID"):
        set_log_level("INVALID")

@patch("import_notable.print")
@patch("import_notable.append_file")
def test_log_message(mock_append_file, mock_print, temp_dir):
    """Test logging messages to console and file."""
    log_file = temp_dir / "test.log"
    set_log_file(log_file)
    set_log_level("INFO")
    log_message("Test message", "INFO")
    mock_print.assert_called_once()
    mock_append_file.assert_called_once()
    set_log_level("ERROR")
    log_message("Test info message", "INFO")
    assert mock_print.call_count == 1  # Not called again due to level
    assert mock_append_file.call_count == 2  # Still called for file

def test_log_error():
    """Test log_error calls log_message with ERROR level."""
    with patch("import_notable.log_message") as mock_log:
        log_error("Error message")
        mock_log.assert_called_with("Error message", "ERROR")

def test_log_warning():
    """Test log_warning calls log_message with WARNING level."""
    with patch("import_notable.log_message") as mock_log:
        log_warning("Warning message")
        mock_log.assert_called_with("Warning message", "WARNING")

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
tags: [a, b]
---
Body
"""
    body, metadata = parse_yaml_front_matter(content)
    assert body == "Body\n"
    assert metadata == {"title": "Test", "tags": ["a", "b"]}
    # Test invalid YAML
    content = """---
invalid: yaml: here
---
Body
"""
    body, metadata = parse_yaml_front_matter(content)
    assert body == content
    assert metadata == {}
    # Test no YAML
    content = "No YAML"
    body, metadata = parse_yaml_front_matter(content)
    assert body == content
    assert metadata == {}

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

def test_write_file(temp_dir):
    """Test writing file content."""
    path = temp_dir / "test.txt"
    assert write_file(path, "Content")
    assert path.read_text(encoding="utf-8") == "Content"
    # Test write failure
    with patch("pathlib.Path.write_text", side_effect=Exception("Write error")):
        assert not write_file(path, "Content")

def test_append_file(temp_dir):
    """Test appending to file."""
    path = temp_dir / "test.txt"
    assert append_file(path, "Line1\n")
    assert append_file(path, "Line2\n")
    assert path.read_text(encoding="utf-8") == "Line1\nLine2\n"
    # Test append failure
    with patch("builtins.open", side_effect=Exception("Append error")):
        assert not append_file(path, "Line3\n")

@patch("subprocess.run")
def test_check_pandoc(mock_run):
    """Test Pandoc availability check."""
    mock_run.return_value = MagicMock()
    assert check_pandoc()
    mock_run.side_effect = subprocess.CalledProcessError(1, ["pandoc", "--version"])
    assert not check_pandoc()
    mock_run.side_effect = FileNotFoundError
    assert not check_pandoc()

@patch("subprocess.run")
@patch("import_notable.PureWindowsPath")
def test_run_pandoc(mock_pure_path, mock_run, temp_dir):
    """Test Pandoc conversion."""
    mock_pure_path.return_value.as_posix.return_value = "output.txt"
    input_md = temp_dir / "input.md"
    output_txt = temp_dir / "output.txt"
    mock_run.return_value = MagicMock()
    assert run_pandoc(input_md, output_txt)
    mock_run.assert_called_with(
        ["pandoc", "-f", "markdown-smart", "-t", "zimwiki", "-o", "output.txt", str(input_md)],
        check=True, capture_output=True, text=True
    )
    # Test Pandoc failure
    mock_run.side_effect = subprocess.CalledProcessError(1, ["pandoc"], stderr="Error")
    assert not run_pandoc(input_md, output_txt)
    # Test Pandoc not found
    mock_run.side_effect = FileNotFoundError
    assert not run_pandoc(input_md, output_txt)

@patch("import_notable.datetime")
def test_zim_header(mock_datetime):
    """Test Zim header generation."""
    mock_datetime.now.return_value.strftime.return_value = "2025-08-19T12:00:00+0530"
    header = zim_header("Test Title")
    expected = (
        "Content-Type: text/x-zim-wiki\n"
        "Wiki-Format: zim 0.6\n"
        "Creation-Date: 2025-08-19T12:00:00+0530\n"
        "====== Test Title ======\n\n"
    )
    assert header == expected

def test_create_journal_page(temp_dir):
    """Test creating a new journal page."""
    page_path = temp_dir / "Journal" / "2025" / "08" / "19.txt"
    with patch("import_notable.zim_header") as mock_zim_header, \
         patch("import_notable.write_file") as mock_write:
        mock_zim_header.return_value = "Header"
        assert create_journal_page(page_path)
        mock_zim_header.assert_called_with("Tuesday 19 Aug 2025")
        mock_write.assert_called_with(page_path, "Header")
    # Test existing page
    page_path.parent.mkdir(parents=True)
    page_path.touch()
    assert create_journal_page(page_path)

def test_append_journal_link(temp_dir):
    """Test appending journal links with deduplication."""
    page_path = temp_dir / "Journal" / "2025" / "08" / "19.txt"
    page_path.parent.mkdir(parents=True)
    page_path.write_text("===== AI Notes =====\n", encoding="utf-8")
    assert append_journal_link(page_path, "Test Note", "raw_ai_notes:test_note")
    content = page_path.read_text(encoding="utf-8")
    assert "* [[raw_ai_notes:test_note|Test Note]]\n" in content
    # Test deduplication
    with patch("import_notable.log_message") as mock_log:
        assert append_journal_link(page_path, "Test Note", "raw_ai_notes:test_note")
        mock_log.assert_called_with(
            f"Journal link already exists in {page_path}: * [[raw_ai_notes:test_note|Test Note]]",
            "DEBUG"
        )
    # Test new section creation
    empty_page = temp_dir / "Journal" / "2025" / "08" / "20.txt"
    with patch("import_notable.create_journal_page", return_value=True):
        assert append_journal_link(empty_page, "Test Note", "raw_ai_notes:test_note")
        content = empty_page.read_text(encoding="utf-8")
        assert "===== AI Notes =====\n* [[raw_ai_notes:test_note|Test Note]]\n" in content

def test_create_zim_note(temp_dir):
    """Test creating a Zim note with header and tags."""
    note_path = temp_dir / "raw_ai_notes" / "test_note.txt"
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
        mock_write.assert_called_with(note_path, "Header\nContent\n")

def test_remove_duplicate_heading():
    """Test removing duplicate level-1 headings."""
    content = "====== Test Note ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == "Content"
    content = "====== test_note ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == "Content"
    # Test with curly apostrophes
    content = "====== Test’s Note ======\nContent"
    assert remove_duplicate_heading(content, "Test's Note", "test_s_note") == "Content"
    # Test no duplicate
    content = "====== Other Title ======\nContent"
    assert remove_duplicate_heading(content, "Test Note", "test_note") == "Content"

def test_parse_timestamp():
    """Test parsing UTC timestamps."""
    ts = parse_timestamp("2025-08-19T15:00:00.000Z")
    assert ts == datetime(2025, 8, 19, 15, 0, tzinfo=timezone.utc)
    ts = parse_timestamp(datetime(2025, 8, 19, 15, 0))
    assert ts == datetime(2025, 8, 19, 15, 0, tzinfo=timezone.utc)
    ts = parse_timestamp("invalid")
    assert ts is None
    ts = parse_timestamp(123)
    assert ts is None

@patch("import_notable.datetime")
@patch("pathlib.Path.stat")
def test_get_file_date(mock_stat, mock_datetime):
    """Test getting file dates from YAML or filesystem."""
    mock_stat.return_value.st_mtime = 1629219600  # 2021-08-17T15:00:00Z
    mock_stat.return_value.st_ctime = 1629219600
    mock_datetime.now.return_value = datetime(2025, 8, 19, 15, 0, tzinfo=timezone.utc)
    metadata = {"created": "2025-08-18T18:10:50.127Z"}
    ts = get_file_date(Path("test.md"), metadata, "created")
    assert ts == datetime(2025, 8, 18, 18, 10, 50, 127000, tzinfo=timezone.utc)
    # Test fallback to filesystem
    metadata = {}
    ts = get_file_date(Path("test.md"), metadata, "modified")
    assert ts == datetime.fromtimestamp(1629219600, tz=timezone.utc)
    # Test invalid timestamp
    metadata = {"created": "invalid"}
    ts = get_file_date(Path("test.md"), metadata, "created")
    assert ts == datetime.fromtimestamp(1629219600, tz=timezone.utc)

@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_needs_update(mock_stat, mock_exists):
    """Test checking if a file needs updating based on UTC timestamps."""
    mock_exists.return_value = False
    assert needs_update(Path("source.md"), Path("dest.txt"), {})
    mock_exists.return_value = True
    mock_stat.return_value.st_mtime = 1724169600  # 2025-08-20T16:00:00Z
    metadata = {"modified": "2025-08-20T17:00:00.000Z"}
    assert needs_update(Path("source.md"), Path("dest.txt"), metadata)
    metadata = {"modified": "2025-08-20T15:00:00.000Z"}
    assert not needs_update(Path("source.md"), Path("dest.txt"), metadata)
    # Test fallback to filesystem
    mock_stat.side_effect = [
        MagicMock(st_mtime=1724169600),  # Source: 2025-08-20T16:00:00Z
        MagicMock(st_mtime=1724166000)   # Dest: 2025-08-20T15:00:00Z
    ]
    metadata = {}
    assert needs_update(Path("source.md"), Path("dest.txt"), metadata)

@patch("import_notable.read_file")
@patch("import_notable.write_file")
@patch("import_notable.run_pandoc")
@patch("import_notable.append_journal_link")
@patch("import_notable.needs_update")
@patch("import_notable.tempfile")
def test_import_md_file(mock_tempfile, mock_needs_update, mock_append_journal_link,
                        mock_run_pandoc, mock_write_file, mock_read_file, temp_dir, sample_md):
    """Test importing a Markdown file."""
    mock_read_file.side_effect = [
        sample_md.read_text(encoding="utf-8"), "Converted content"
    ]
    mock_write_file.return_value = True
    mock_run_pandoc.return_value = True
    mock_append_journal_link.return_value = True
    mock_needs_update.return_value = True
    mock_tempfile.mkstemp.return_value = (123, str(temp_dir / "temp.md"))
    mock_tempfile.tempdir = str(temp_dir)
    used_slugs = set()
    result = import_md_file(
        sample_md, temp_dir / "raw_ai_notes", temp_dir / "Journal",
        temp_dir / "test.log", temp_dir, used_slugs
    )
    assert result == ImportStatus.SUCCESS
    assert "test_note" in used_slugs
    mock_append_journal_link.assert_called()
    # Test skip
    mock_needs_update.return_value = False
    result = import_md_file(
        sample_md, temp_dir / "raw_ai_notes", temp_dir / "Journal",
        temp_dir / "test.log", temp_dir, used_slugs
    )
    assert result == ImportStatus.SKIPPED

def test_validate_paths(temp_dir, sample_md):
    """Test path validation."""
    notable_dir = sample_md.parent
    zim_dir = temp_dir / "zim"
    assert validate_paths(notable_dir, zim_dir)
    assert not validate_paths(temp_dir / "nonexistent", zim_dir)
    assert not validate_paths(sample_md, zim_dir)  # Not a dir
    assert not validate_paths(notable_dir, temp_dir / "nonexistent")
    assert not validate_paths(notable_dir, sample_md)  # Not a dir

@patch("import_notable.check_pandoc", return_value=True)
@patch("import_notable.validate_paths", return_value=True)
@patch("import_notable.import_md_file")
@patch("import_notable.read_file")
@patch("import_notable.write_file")
@patch("import_notable.append_file")
@patch("sys.argv", ["script.py", "--notable-dir", "notable", "--zim-dir", "zim", "--log-file", "test.log", "--log-level", "DEBUG"])
def test_main(mock_append_file, mock_write_file, mock_read_file, mock_import_md_file,
              mock_validate_paths, mock_check_pandoc, temp_dir, sample_md):
    """Test main function."""
    mock_read_file.return_value = sample_md.read_text(encoding="utf-8")
    mock_write_file.return_value = True
    mock_append_file.return_value = True
    mock_import_md_file.return_value = ImportStatus.SUCCESS
    with patch("pathlib.Path.glob", return_value=[sample_md]):
        main()
    mock_import_md_file.assert_called()

if __name__ == "__main__":
    pytest.main(["-v"])