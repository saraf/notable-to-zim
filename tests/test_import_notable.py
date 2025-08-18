import pytest
from datetime import datetime
from pathlib import Path
from import_notable import slugify, parse_yaml_front_matter, needs_update, import_md_file, ImportStatus

@pytest.fixture
def temp_notable_dir(tmp_path):
    """Create a temporary directory for Notable Markdown files."""
    return tmp_path / "notable"

@pytest.fixture
def temp_zim_dir(tmp_path):
    """Create a temporary directory for Zim notebook."""
    return tmp_path / "zim"

def test_slugify_unique_titles(mocker):
    """Test slugify generates unique slugs for duplicate titles."""
    dest_dir = Path("/tmp/zim/raw_ai_notes")
    used_slugs = set()
    
    # Mock Path.exists
    mocker.patch.object(Path, 'exists', side_effect=lambda: False)
    
    slug1 = slugify("Untitled", dest_dir, used_slugs)
    assert slug1 == "untitled"
    assert used_slugs == {"untitled"}
    
    slug2 = slugify("Untitled", dest_dir, used_slugs)
    assert slug2 == "untitled_2"
    assert used_slugs == {"untitled", "untitled_2"}

def test_parse_yaml_front_matter():
    """Test parsing YAML front matter."""
    content = """---
title: Test Note
tags: [test]
created: 2025-07-24T12:55:26.779Z
---
# Test Note
Content here.
"""
    body, metadata = parse_yaml_front_matter(content)
    assert body.strip() == "# Test Note\nContent here."
    assert metadata == {
        "title": "Test Note",
        "tags": ["test"],
        "created": "2025-07-24T12:55:26.779Z"
    }

def test_needs_update_new_file(mocker):
    """Test needs_update for a non-existent destination file."""
    source_path = Path("note.md")
    dest_path = Path("note.txt")
    
    # Mock Path.exists to simulate new file
    mocker.patch.object(Path, 'exists', return_value=False)
    
    assert needs_update(source_path, dest_path, {"modified": "2025-07-24T13:00:00Z"}) is True

def test_import_md_file_with_datetime_yaml(mocker, temp_notable_dir, temp_zim_dir):
    """Test importing a file with datetime object in YAML front matter."""
    md_file = temp_notable_dir / 'datetime_note.md'
    content = """---
title: Datetime Note
tags: [test]
created: 2025-07-24 12:55:26.779000+00:00
modified: 2025-07-24 13:00:44.505000+00:00
---
# Datetime Note
Content here.
"""
    md_file.write_text(content)
    raw_store = temp_zim_dir / 'raw_ai_notes'
    journal_root = temp_zim_dir / 'Journal'
    
    # Mock subprocess.run
    mocker.patch('import_notable.subprocess.run', side_effect=lambda cmd, **kwargs: Path(cmd[-3]).write_text(Path(cmd[-1]).read_text() + " (Zim formatted)"))
    # Mock get_file_date
    mocker.patch('import_notable.get_file_date', return_value=datetime(2025, 8, 18))
    
    result = import_md_file(md_file, raw_store, journal_root)
    assert result == ImportStatus.SUCCESS
    
    # Verify output
    note_file = raw_store / 'datetime_note.txt'
    assert note_file.exists()
    content = note_file.read_text()
    assert "====== Datetime Note ======" in content
    assert "# Datetime Note" in content
    assert "**Tags:** @test" in content
    
    # Verify journal
    journal_page = journal_root / '2025' / '08' / '18.txt'
    assert journal_page.exists()
    journal_content = journal_page.read_text()
    assert "===== AI Notes =====" in journal_content
    assert "[[raw_ai_notes:datetime_note|Datetime Note]]" in journal_content

def test_import_md_files_with_duplicate_titles(mocker, temp_notable_dir, temp_zim_dir):
    """Test importing files with identical YAML titles but different filenames."""
    md_file1 = temp_notable_dir / 'Untitled.md'
    md_file2 = temp_notable_dir / 'Untitled (2).md'
    
    content1 = """---
title: Untitled
tags: [test]
created: 2025-07-24T12:55:26.779Z
modified: 2025-07-24T13:00:44.505Z
---
# Untitled
Content of first note.
"""
    content2 = """---
title: Untitled
tags: [test2]
created: 2025-07-24T12:55:27.779Z
modified: 2025-07-24T13:00:45.505Z
---
# Untitled (2)
Content of second note.
"""
    md_file1.write_text(content1)
    md_file2.write_text(content2)
    
    raw_store = temp_zim_dir / 'raw_ai_notes'
    journal_root = temp_zim_dir / 'Journal'
    
    # Mock subprocess.run
    mocker.patch('import_notable.subprocess.run', side_effect=lambda cmd, **kwargs: Path(cmd[-3]).write_text(Path(cmd[-1]).read_text() + " (Zim formatted)"))
    # Mock get_file_date
    mocker.patch('import_notable.get_file_date', return_value=datetime(2025, 8, 18))
    
    # Import both files
    used_slugs = set()
    result1 = import_md_file(md_file1, raw_store, journal_root, used_slugs=used_slugs)
    result2 = import_md_file(md_file2, raw_store, journal_root, used_slugs=used_slugs)
    
    assert result1 == ImportStatus.SUCCESS
    assert result2 == ImportStatus.SUCCESS
    
    # Verify output files
    note_file1 = raw_store / 'untitled.txt'
    note_file2 = raw_store / 'untitled_2.txt'
    assert note_file1.exists()
    assert note_file2.exists()
    
    content1 = note_file1.read_text()
    content2 = note_file2.read_text()
    assert "====== Untitled ======" in content1
    assert "Content of first note" in content1
    assert "**Tags:** @test" in content1
    assert "====== Untitled ======" in content2
    assert "Content of second note" in content2
    assert "**Tags:** @test2" in content2
    
    # Verify journal
    journal_page = journal_root / '2025' / '08' / '18.txt'
    assert journal_page.exists()
    journal_content = journal_page.read_text()
    assert "===== AI Notes =====" in journal_content
    assert "[[raw_ai_notes:untitled|Untitled]]" in journal_content
    assert "[[raw_ai_notes:untitled_2|Untitled]]" in journal_content