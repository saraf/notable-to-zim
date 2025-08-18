# In tests/test_import_notable.py
from datetime import datetime

@patch('import_notable.subprocess.run')
@patch('import_notable.get_file_date', return_value=datetime(2025, 8, 18))
def test_import_md_files_with_duplicate_titles(mock_pandoc, mock_date, temp_notable_dir, temp_zim_dir, mocker):
    # Create two files with identical YAML titles
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
    
    # Mock Pandoc
    def mock_run(cmd, **kwargs):
        input_md = Path(cmd[-1])
        output_txt = Path(cmd[-3])
        output_txt.write_text(input_md.read_text() + " (Zim formatted)")
    mock_pandoc.side_effect = mock_run
    
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
