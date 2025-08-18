#!/usr/bin/env python3
"""
import_notable.py - BASELINE VERSION v1.0

Import Notable Markdown notes into a Zim Desktop Wiki notebook,
creating raw AI notes with proper Zim metadata, and appending
links to the Journal pages in chronological order.

BASELINE FEATURES (v1.0):
- Slugified filenames for raw AI notes.
- Idempotent import (skips already imported notes).
- Chronological journal links under "AI Notes" section.
- Pandoc conversion from Markdown to Zim-friendly plain text.
- Handles YAML front matter safely.
- Logging to console and optional log file.
- Better error handling and Windows compatibility.
- Progress reporting for large imports.
- Dry-run mode for previewing imports.
- Input validation and Pandoc availability check.

This is our agreed baseline version for future development.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ------------------------ Helper Functions ------------------------

def slugify(s: str) -> str:
    """Convert string to a valid filename slug."""
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("_-")
    # Ensure it's not empty
    return s if s else "untitled"

def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def strip_yaml_front_matter(content: str) -> str:
    """Remove YAML front matter from markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return content

def read_file(path: Path) -> str:
    """Read file content with error handling."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"[WARNING] Unicode decode error for {path}, trying with latin-1")
        return path.read_text(encoding="latin-1")
    except Exception as e:
        print(f"[ERROR] Could not read file {path}: {e}")
        return ""

def write_file(path: Path, content: str) -> bool:
    """Write file content with error handling."""
    try:
        ensure_dir(path.parent)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"[ERROR] Could not write file {path}: {e}")
        return False

def append_file(path: Path, content: str) -> bool:
    """Append content to file with error handling."""
    try:
        ensure_dir(path.parent)
        with path.open("a", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[ERROR] Could not append to file {path}: {e}")
        return False

def check_pandoc() -> bool:
    """Check if Pandoc is available in PATH."""
    try:
        subprocess.run(["pandoc", "--version"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_pandoc(input_md: Path, output_txt: Path) -> bool:
    """Convert markdown to Zim wiki format using Pandoc."""
    cmd = ["pandoc", "-f", "markdown", "-t", "zimwiki", "-o", str(output_txt), str(input_md)]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Pandoc failed for {input_md}: {e}")
        if e.stderr:
            print(f"[ERROR] Pandoc stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("[ERROR] Pandoc not found. Please install Pandoc and ensure it's in your PATH.")
        return False

def zim_header(title: str) -> str:
    """Generate Zim wiki page header."""
    # Use local timezone format that Zim expects
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    header = (
        "Content-Type: text/x-zim-wiki\n"
        "Wiki-Format: zim 0.6\n"
        f"Creation-Date: {ts}\n"
        f"====== {title} ======\n\n\n\n"
    )
    return header

def create_journal_page(page_path: Path) -> bool:
    """Create a new journal page if it doesn't exist."""
    if not page_path.exists():
        # Create journal page title in Zim Journal Plugin format
        date_obj = datetime.strptime(page_path.stem, "%d")
        # Get year and month from parent directories
        month_num = page_path.parent.name
        year_num = page_path.parent.parent.name
        
        # Reconstruct full date for proper formatting
        full_date = datetime(int(year_num), int(month_num), int(page_path.stem))
        journal_title = full_date.strftime("%A %d %b %Y")
        
        header = zim_header(journal_title)
        if write_file(page_path, header):
            print(f"Created new journal page: {page_path}")
            return True
        return False
    return True

def append_journal_link(page_path: Path, link_text: str, link_target: str) -> bool:
    """Append a link to the journal page under AI Notes section."""
    section_title = "===== AI Notes =====\n"
    
    # Create page if it doesn't exist
    if not create_journal_page(page_path):
        return False
    
    content = read_file(page_path)
    if not content:
        return False
    
    # Add AI Notes section if it doesn't exist
    if "===== AI Notes =====" not in content:
        if not append_file(page_path, "\n" + section_title):
            return False
    
    # Add the link
    link_line = f"* [[{link_target}|{link_text}]]\n"
    if append_file(page_path, link_line):
        print(f"Appended link to journal: {page_path.name}")
        return True
    return False

def create_zim_note(note_path: Path, title: str, content: str) -> bool:
    """Create a Zim note with proper header and content."""
    header = zim_header(title)
    full_content = header + content
    if write_file(note_path, full_content):
        print(f"Imported new AI note: {note_path.name}")
        return True
    return False

def get_file_date(md_path: Path) -> datetime:
    """Get the creation/modification date of a file."""
    try:
        # Try to get creation time first (Windows), fall back to modification time
        if hasattr(os.stat_result, 'st_birthtime'):
            # macOS
            return datetime.fromtimestamp(md_path.stat().st_birthtime)
        elif sys.platform == 'win32':
            # Windows - use creation time
            return datetime.fromtimestamp(md_path.stat().st_ctime)
        else:
            # Linux/Unix - use modification time
            return datetime.fromtimestamp(md_path.stat().st_mtime)
    except Exception:
        # Fallback to modification time
        return datetime.fromtimestamp(md_path.stat().st_mtime)

# ------------------------ Main Import Logic ------------------------

def import_md_file(md_path: Path, raw_store: Path, journal_root: Path, 
                   log_file: Optional[Path] = None) -> bool:
    """Import a single markdown file into Zim wiki."""
    try:
        # Read and strip YAML front matter
        content = strip_yaml_front_matter(read_file(md_path))
        if not content.strip():
            print(f"[WARNING] Empty content after processing: {md_path}")
            return False
        
        # Slugify filename
        slug = slugify(md_path.stem)
        note_file = raw_store / f"{slug}.txt"
        
        # Idempotent check
        if note_file.exists():
            print(f"Skipping already imported note: {note_file.name}")
            return True
        
        # Create temporary markdown file for pandoc
        temp_md = md_path.parent / f"temp_{md_path.name}"
        if not write_file(temp_md, content):
            return False
        
        try:
            # Convert Markdown to Zim format
            if not run_pandoc(temp_md, note_file):
                return False
            
            # Read the converted content
            content_plain = read_file(note_file)
            if not content_plain:
                return False
            
            # Create final Zim note with proper header
            if not create_zim_note(note_file, md_path.stem, content_plain):
                return False
            
        finally:
            # Clean up temp file
            if temp_md.exists():
                temp_md.unlink()
        
        # Determine journal page by file creation date
        created_ts = get_file_date(md_path)
        year = created_ts.strftime("%Y")
        month = created_ts.strftime("%m")
        day = created_ts.strftime("%d")
        journal_page = journal_root / year / month / f"{day}.txt"
        
        # Append link to journal
        if not append_journal_link(journal_page, md_path.stem, f"raw_ai_notes:{slug}"):
            print(f"[WARNING] Failed to add journal link for {md_path}")
        
        # Log if requested
        if log_file:
            log_entry = f"{datetime.now().isoformat()}: Imported {md_path} -> {note_file}\n"
            append_file(log_file, log_entry)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to import {md_path}: {e}")
        return False

def validate_paths(notable_dir: Path, zim_dir: Path) -> bool:
    """Validate that the specified paths exist and are accessible."""
    if not notable_dir.exists():
        print(f"[ERROR] Notable directory does not exist: {notable_dir}")
        return False
    
    if not notable_dir.is_dir():
        print(f"[ERROR] Notable path is not a directory: {notable_dir}")
        return False
    
    if not zim_dir.exists():
        print(f"[ERROR] Zim directory does not exist: {zim_dir}")
        return False
    
    if not zim_dir.is_dir():
        print(f"[ERROR] Zim path is not a directory: {zim_dir}")
        return False
    
    return True

# ------------------------ Main ------------------------

def main():
    parser = argparse.ArgumentParser(description="Import Notable Markdown notes into Zim Wiki")
    parser.add_argument("--notable-dir", required=True, 
                       help="Directory containing Notable .md notes")
    parser.add_argument("--zim-dir", required=True, 
                       help="Root directory of Zim notebook")
    parser.add_argument("--log-file", required=False, 
                       help="Optional log file for import details")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be imported without making changes")
    args = parser.parse_args()

    # Resolve and validate paths
    notable_dir = Path(args.notable_dir).expanduser().resolve()
    zim_dir = Path(args.zim_dir).expanduser().resolve()
    
    if not validate_paths(notable_dir, zim_dir):
        sys.exit(1)
    
    # Check for Pandoc
    if not check_pandoc():
        print("[ERROR] Pandoc is required but not found in PATH.")
        print("Please install Pandoc from https://pandoc.org/")
        sys.exit(1)
    
    journal_root = zim_dir / "Journal"
    raw_store = zim_dir / "raw_ai_notes"
    
    print(f"Notable directory: {notable_dir}")
    print(f"Zim directory: {zim_dir}")
    print(f"Raw AI notes will be stored in: {raw_store}")
    print(f"Journal links will be added to: {journal_root}")
    
    if args.dry_run:
        print("\n[DRY RUN MODE] - No files will be modified")
    
    # Create necessary directories
    if not args.dry_run:
        ensure_dir(raw_store)
        ensure_dir(journal_root)
        
        # Create raw_ai_notes root page for Zim index
        raw_root_page = zim_dir / "raw_ai_notes.txt"
        if not raw_root_page.exists():
            if write_file(raw_root_page, zim_header("Raw AI Notes")):
                print(f"Created Zim root page: {raw_root_page}")
    
    # Setup log file if requested
    log_file = None
    if args.log_file:
        log_file = Path(args.log_file).expanduser().resolve()
        if not args.dry_run:
            ensure_dir(log_file.parent)
            append_file(log_file, f"\n=== Import session started at {datetime.now().isoformat()} ===\n")
    
    # Collect and sort Notable MD files by creation time
    md_files = list(notable_dir.glob("*.md"))
    if not md_files:
        print(f"[WARNING] No .md files found in {notable_dir}")
        return
    
    md_files.sort(key=get_file_date)
    
    print(f"\nFound {len(md_files)} markdown files to process")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, md_file in enumerate(md_files, 1):
        print(f"\n[{i}/{len(md_files)}] Processing: {md_file.name}")
        
        if args.dry_run:
            slug = slugify(md_file.stem)
            note_file = raw_store / f"{slug}.txt"
            if note_file.exists():
                print(f"  Would skip (already exists): {note_file.name}")
                skip_count += 1
            else:
                print(f"  Would import as: {note_file.name}")
                success_count += 1
        else:
            result = import_md_file(md_file, raw_store, journal_root, log_file)
            if result:
                # Check if it was actually imported or skipped
                slug = slugify(md_file.stem)
                note_file = raw_store / f"{slug}.txt"
                if note_file.exists():
                    success_count += 1
                else:
                    skip_count += 1
            else:
                error_count += 1
    
    # Final summary
    print(f"\n{'='*50}")
    print("IMPORT SUMMARY")
    print(f"{'='*50}")
    print(f"Total files processed: {len(md_files)}")
    print(f"Successfully imported: {success_count}")
    print(f"Skipped (already exist): {skip_count}")
    print(f"Errors: {error_count}")
    
    if log_file and not args.dry_run:
        summary = (
            f"\n=== Import session completed at {datetime.now().isoformat()} ===\n"
            f"Total: {len(md_files)}, Success: {success_count}, "
            f"Skipped: {skip_count}, Errors: {error_count}\n"
        )
        append_file(log_file, summary)
        print(f"\nDetailed log written to: {log_file}")

if __name__ == "__main__":
    main()