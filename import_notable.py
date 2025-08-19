#!/usr/bin/env python3
"""
import_notable.py - VERSION v1.9.10

Import Notable Markdown notes into a Zim Desktop Wiki notebook,
creating raw AI notes with proper Zim metadata, and appending
links to the Journal pages in chronological order.

Part of the Notable-to-Zim project.

CHANGES IN v1.9.10:
- Enhanced needs_update with explicit conditional logging for YAML and filesystem timestamp comparisons.
- Removed redundant debug logs in get_file_date for cleaner output.
- Simplified journal link debug log in import_md_file.
- Ensured compatibility with test_import_notable.py, fixing 12 test failures.
- No new dependencies required.

CHANGES IN v1.9.9:
- Fixed needs_update to handle UTC timestamps in YAML by converting st_mtime to UTC for comparison.
- Added deduplication of journal links to prevent multiple identical links on the same day.
- Enhanced logging in needs_update to include UTC and local timestamps with microsecond precision.
- Kept Pandoc -f markdown-smart and journal link support for updated notes from v1.9.8.
- No new dependencies required.

See CHANGELOG.md for historical changes (v1.8–v1.9.8).
"""

# ------------------------ Imports ------------------------
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum
import yaml
import unicodedata
from dateutil import parser as dateutil_parser

# ------------------------ Constants ------------------------
class ImportStatus(Enum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4

# ------------------------ Global Variables ------------------------
_log_file = None
_log_level = LogLevel.INFO  # Default log level for console

# ------------------------ Logging Functions ------------------------
def set_log_file(log_file: Optional[Path]) -> None:
    """Set the global log file for error logging."""
    global _log_file
    _log_file = log_file

def set_log_level(level: str) -> None:
    """Set the global log level for console output."""
    global _log_level
    try:
        _log_level = LogLevel[level.upper()]
    except KeyError:
        raise ValueError(f"Invalid log level: {level}. Choose from DEBUG, INFO, WARNING, ERROR.")

def log_message(message: str, level: str = "INFO") -> None:
    """Log message to console (if level >= _log_level) and log file (if available)."""
    timestamp = datetime.now(timezone.utc).isoformat()
    formatted_message = f"[{level}] {timestamp} {message}"
    
    try:
        message_level = LogLevel[level.upper()]
        if message_level.value >= _log_level.value:
            print(formatted_message)
    except KeyError:
        print(formatted_message)
    
    if _log_file:
        log_entry = f"{timestamp} {formatted_message}\n"
        try:
            append_file(_log_file, log_entry)
        except Exception:
            pass

def log_error(message: str) -> None:
    """Log error message."""
    log_message(message, "ERROR")

def log_warning(message: str) -> None:
    """Log warning message."""
    log_message(message, "WARNING")

# ------------------------ Helper Functions ------------------------
def slugify(s: str, dest_dir: Path, used_slugs: set) -> str:
    """Convert string to a valid filename slug, handling duplicates."""
    base_slug = s.lower()
    base_slug = re.sub(r"[^\w\s-]", "", base_slug)
    base_slug = re.sub(r"\s+", "_", base_slug)
    base_slug = base_slug.strip("_-")
    base_slug = base_slug if base_slug else "untitled"
    
    if (dest_dir / f"{base_slug}.txt").exists() and base_slug not in used_slugs:
        return base_slug
    
    slug = base_slug
    counter = 1
    while (dest_dir / f"{slug}.txt").exists() or slug in used_slugs:
        slug = f"{base_slug}_{counter}"
        counter += 1
    used_slugs.add(slug)
    return slug

def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def parse_yaml_front_matter(content: str) -> Tuple[str, Dict[str, Any]]:
    """Parse YAML front matter and return stripped content and metadata."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                content = parts[2].lstrip("\n")
                return content, metadata
            except yaml.YAMLError as e:
                log_warning(f"Failed to parse YAML front matter: {e}")
                return content, {}
    return content, {}

def read_file(path: Path) -> str:
    """Read file content with error handling."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        log_warning(f"Unicode decode error for {path}, trying with latin-1")
        return path.read_text(encoding="latin-1")
    except Exception as e:
        log_error(f"Could not read file {path}: {e}")
        return ""

def write_file(path: Path, content: str) -> bool:
    """Write file content with error handling."""
    try:
        ensure_dir(path.parent)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        log_error(f"Could not write file {path}: {e}")
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
    output_txt_str = str(PureWindowsPath(output_txt).as_posix())
    cmd = ["pandoc", "-f", "markdown-smart", "-t", "zimwiki", "-o", output_txt_str, str(input_md)]
    log_message(f"Running pandoc command: {' '.join(cmd)}", "DEBUG")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log_message(f"Pandoc succeeded for {input_md}", "DEBUG")
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Pandoc failed for {input_md}: {e}")
        if e.stderr:
            log_error(f"Pandoc stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        log_error("Pandoc not found. Please install Pandoc and ensure it's in your PATH.")
        return False

def zim_header(title: str) -> str:
    """Generate Zim wiki page header."""
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    header = (
        "Content-Type: text/x-zim-wiki\n"
        "Wiki-Format: zim 0.6\n"
        f"Creation-Date: {ts}\n"
        f"====== {title} ======\n\n"
    )
    return header

def create_journal_page(page_path: Path) -> bool:
    """Create a new journal page if it doesn't exist."""
    if not page_path.exists():
        date_obj = datetime.strptime(page_path.stem, "%d")
        month_num = page_path.parent.name
        year_num = page_path.parent.parent.name
        full_date = datetime(int(year_num), int(month_num), int(page_path.stem))
        journal_title = full_date.strftime("%A %d %b %Y")
        header = zim_header(journal_title)
        if write_file(page_path, header):
            print(f"Created new journal page: {page_path}")
            return True
        return False
    return True

def append_journal_link(page_path: Path, link_text: str, link_target: str) -> bool:
    """Append a link to the journal page under AI Notes section, avoiding duplicates."""
    section_title = "===== AI Notes =====\n"
    if not create_journal_page(page_path):
        return False
    content = read_file(page_path)
    if not content:
        return False
    if "===== AI Notes =====" not in content:
        if not append_file(page_path, "\n" + section_title):
            return False
    link_line = f"* [[{link_target}|{link_text}]]\n"
    if link_line in content:
        log_message(f"Journal link already exists in {page_path}: {link_line.strip()}", "DEBUG")
        return True
    if append_file(page_path, link_line):
        print(f"Appended link to journal: {page_path.name}")
        return True
    return False

def create_zim_note(note_path: Path, title: str, content: str, tags: List[str]) -> bool:
    """Create a Zim note with proper header, content, and tags section."""
    log_message(f"Creating Zim note: {note_path}, tags={tags}", "DEBUG")
    header = zim_header(title)
    tags = tags or []
    tags_section = "\n\n**Tags:** " + " ".join(f"@{tag}" for tag in tags) + "\n" if tags else "\n\n"
    full_content = header + content + tags_section
    if write_file(note_path, full_content):
        print(f"Imported new AI note: {note_path.name}")
        return True
    return False

def remove_duplicate_heading(content: str, title: str, file_stem: str) -> str:
    """Remove duplicate level-1 heading from Pandoc-converted content if it matches title or file stem."""
    log_message(f"Checking for duplicate heading in content: title='{title}', file_stem='{file_stem}'", "DEBUG")
    normalized_content = unicodedata.normalize('NFKC', content).replace('’', "'")
    normalized_title = unicodedata.normalize('NFKC', title).replace('’', "'")
    normalized_file_stem = unicodedata.normalize('NFKC', file_stem).replace('’', "'")
    log_message(f"After normalization - title: {normalized_title}, file_stem: {normalized_file_stem}", "DEBUG")
    log_message(f"Content starts with: {normalized_content[:100]}", "DEBUG")
    heading_pattern = r'======\s*' + re.escape(normalized_title) + r'\s*======\s*\n*'
    alt_heading_pattern = r'======\s*' + re.escape(normalized_file_stem) + r'\s*======\s*\n*'
    log_message(f"Heading pattern: {heading_pattern}", "DEBUG")
    log_message(f"Alt heading pattern: {alt_heading_pattern}", "DEBUG")
    
    if re.search(heading_pattern, normalized_content, re.IGNORECASE):
        content = re.sub(heading_pattern, '', normalized_content, count=1, flags=re.IGNORECASE)
        log_message(f"Removed duplicate heading matching title: {title}", "DEBUG")
    elif re.search(alt_heading_pattern, normalized_content, re.IGNORECASE):
        content = re.sub(alt_heading_pattern, '', normalized_content, count=1, flags=re.IGNORECASE)
        log_message(f"Removed duplicate heading matching file stem: {file_stem}", "DEBUG")
    else:
        log_message("No duplicate heading found", "DEBUG")
    
    return content.strip()

def parse_timestamp(timestamp: Any) -> Optional[datetime]:
    """Parse ISO 8601 timestamp or datetime object from YAML, preserving UTC timezone."""
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)
    if isinstance(timestamp, str):
        try:
            parsed = dateutil_parser.isoparse(timestamp)
            if parsed.tzinfo is None:
                log_warning(f"Timestamp '{timestamp}' lacks timezone, assuming UTC")
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (ValueError, TypeError) as e:
            log_warning(f"Failed to parse timestamp string '{timestamp}': {e}")
            return None
    log_warning(f"Invalid timestamp type '{type(timestamp)}' for value: {timestamp}")
    return None

def get_file_date(md_path: Path, metadata: Dict[str, Any], key: str = 'created') -> datetime:
    """Get the specified date (created or modified) from YAML metadata in UTC, fall back to filesystem."""
    date_value = metadata.get(key)
    if date_value is not None:
        parsed = parse_timestamp(date_value)
        if parsed:
            return parsed
        log_warning(f"No valid '{key}' timestamp '{date_value}' in {md_path}, using filesystem {key} time")
    else:
        log_warning(f"No '{key}' field in {md_path}, using filesystem {key} time")
    try:
        if key == 'created' and hasattr(os.stat_result, 'st_birthtime'):
            file_time = datetime.fromtimestamp(md_path.stat().st_birthtime, tz=timezone.utc)
        elif key == 'created' and sys.platform == 'win32':
            file_time = datetime.fromtimestamp(md_path.stat().st_ctime, tz=timezone.utc)
        else:
            file_time = datetime.fromtimestamp(md_path.stat().st_mtime, tz=timezone.utc)
        return file_time
    except Exception:
        log_warning(f"Could not get filesystem {key} timestamp for {md_path}, using current UTC time")
        return datetime.now(timezone.utc)

def needs_update(source_path: Path, dest_path: Path, metadata: Dict[str, Any]) -> bool:
    """Check if source file's YAML modified timestamp (UTC) is newer than destination file's mtime (UTC)."""
    if not dest_path.exists():
        log_message(f"Destination file {dest_path} does not exist, needs update", "DEBUG")
        return True
    
    modified = metadata.get('modified')
    if modified is not None:
        parsed = parse_timestamp(modified)
        if parsed:
            try:
                dest_mtime = datetime.fromtimestamp(dest_path.stat().st_mtime, tz=timezone.utc)
                log_message(f"Comparing YAML modified timestamp {parsed.isoformat()} (UTC) with dest_mtime {dest_mtime.isoformat()} (UTC) for {source_path}", "DEBUG")
                if parsed > dest_mtime:
                    log_message(f"Modified timestamp is newer, needs update for {source_path}", "DEBUG")
                    return True
                log_message(f"Modified timestamp is not newer, no update needed for {source_path}", "DEBUG")
                return False
            except Exception as e:
                log_warning(f"Could not compare file times for {source_path}: {e}")
                return True
        log_warning(f"No valid 'modified' timestamp '{modified}' in {source_path}, using filesystem check")
    else:
        log_warning(f"No 'modified' field in {source_path}, using filesystem check")
    
    try:
        source_mtime = datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc)
        dest_mtime = datetime.fromtimestamp(dest_path.stat().st_mtime, tz=timezone.utc)
        log_message(f"Comparing filesystem source_mtime {source_mtime.isoformat()} (UTC) with dest_mtime {dest_mtime.isoformat()} (UTC) for {source_path}", "DEBUG")
        if source_mtime > dest_mtime:
            log_message(f"Filesystem mtime is newer, needs update for {source_path}", "DEBUG")
            return True
        log_message(f"Filesystem mtime is not newer, no update needed for {source_path}", "DEBUG")
        return False
    except Exception as e:
        log_warning(f"Could not compare filesystem times for {source_path}: {e}")
        return True

def import_md_file(md_path: Path, raw_store: Path, journal_root: Path, 
                   log_file: Optional[Path] = None, temp_dir: Optional[Path] = None, 
                   used_slugs: Optional[set] = None) -> ImportStatus:
    """Import a single markdown file into Zim wiki."""
    try:
        content = read_file(md_path)
        if not content.strip():
            log_warning(f"Empty content in: {md_path}")
            return ImportStatus.ERROR
        
        content, metadata = parse_yaml_front_matter(content)
        if not content.strip():
            log_warning(f"Empty content after YAML processing: {md_path}")
            return ImportStatus.ERROR
        
        title = metadata.get('title', md_path.stem)
        tags = metadata.get('tags') or []
        if not isinstance(tags, list):
            log_warning(f"Tags is not a list in {md_path}: {tags}, converting to empty list")
            tags = []
        log_message(f"Processed tags for {md_path}: {tags}", "DEBUG")
        
        slug = slugify(title, raw_store, used_slugs)
        note_file = raw_store / f"{slug}.txt"
        if title != md_path.stem:
            log_message(f"Using YAML title '{title}' for {md_path}", "INFO")
        else:
            log_message(f"Using filename '{md_path.stem}' as title for {md_path} due to missing YAML title or collision", "INFO")
        
        is_new_file = not note_file.exists()
        needs_reimport = needs_update(md_path, note_file, metadata)
        
        if not needs_reimport:
            print(f"Skipping up-to-date note: {note_file.name}")
            return ImportStatus.SKIPPED
        
        action_type = "Importing new" if is_new_file else "Updating existing"
        print(f"{action_type} note: {note_file.name}")
        
        temp_md = None
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix='.md', prefix='zim_import_', 
                                                 dir=temp_dir)
            temp_md = Path(temp_path)
            os.close(temp_fd)
            if not write_file(temp_md, content):
                return ImportStatus.ERROR

            if not run_pandoc(temp_md, note_file):
                return ImportStatus.ERROR

            content_plain = read_file(note_file)
            if not content_plain:
                return ImportStatus.ERROR

            content_plain = remove_duplicate_heading(content_plain, title, md_path.stem)

            if not create_zim_note(note_file, title, content_plain, tags):
                return ImportStatus.ERROR
            
        finally:
            if temp_md and temp_md.exists():
                try:
                    temp_md.unlink()
                except Exception as e:
                    log_warning(f"Could not delete temporary file {temp_md}: {e}")
        
        journal_date_key = 'created' if is_new_file else 'modified'
        journal_ts = get_file_date(md_path, metadata, journal_date_key)
        year = journal_ts.strftime("%Y")
        month = journal_ts.strftime("%m")
        day = journal_ts.strftime("%d")
        journal_page = journal_root / year / month / f"{day}.txt"
        
        if append_journal_link(journal_page, title, f"raw_ai_notes:{slug}"):
            log_message(f"Added journal link for {md_path} to {journal_page} (based on {journal_date_key} timestamp)", "DEBUG")
        else:
            log_warning(f"Failed to add journal link for {md_path} to {journal_page}")
        
        if log_file:
            status = "NEW" if is_new_file else "UPDATED"
            log_entry = f"{status}: Processed {md_path} -> {note_file} (Title: {title}, Tags: {tags}, Journal: {journal_page})\n"
            append_file(log_file, log_entry)
        
        return ImportStatus.SUCCESS
        
    except Exception as e:
        log_error(f"Failed to import {md_path}: {e}")
        return ImportStatus.ERROR
    
def validate_paths(notable_dir: Path, zim_dir: Path) -> bool:
    """Validate that the specified paths exist and are accessible."""
    if not notable_dir.exists():
        log_error(f"Notable directory does not exist: {notable_dir}")
        return False
    
    if not notable_dir.is_dir():
        log_error(f"Notable path is not a directory: {notable_dir}")
        return False
    
    if not zim_dir.exists():
        log_error(f"Zim directory does not exist: {zim_dir}")
        return False
    
    if not zim_dir.is_dir():
        log_error(f"Zim path is not a directory: {zim_dir}")
        return False
    
    return True

def main():
    try:
        parser = argparse.ArgumentParser(description="Import Notable Markdown notes into Zim Wiki")
        parser.add_argument("--notable-dir", required=True, 
                           help="Directory containing Notable .md notes")
        parser.add_argument("--zim-dir", required=True, 
                           help="Root directory of Zim notebook")
        parser.add_argument("--log-file", required=False, 
                           help="Optional log file for import details")
        parser.add_argument("--log-level", default="INFO",
                           choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                           help="Console log level (default: INFO)")
        parser.add_argument("--dry-run", action="store_true", 
                           help="Show what would be imported without making changes")
        args = parser.parse_args()

        temp_dir = None
        notable_dir = Path(args.notable_dir).expanduser().resolve()
        zim_dir = Path(args.notable_dir).expanduser().resolve()
        
        set_log_level(args.log_level)
        
        if not validate_paths(notable_dir, zim_dir):
            sys.exit(1)
        
        if not check_pandoc():
            print("[ERROR] Pandoc is required but not found in PATH.")
            print("Please install Pandoc from https://pandoc.org/")
            sys.exit(1)
        
        log_file = None
        if args.log_file:
            log_file = Path(args.log_file).expanduser().resolve()
            if not args.dry_run:
                ensure_dir(log_file.parent)
                append_file(log_file, f"\n=== Import session started at {datetime.now(timezone.utc).isoformat()} ===\n")
        
        set_log_file(log_file)
        
        journal_root = zim_dir / "Journal"
        raw_store = zim_dir / "raw_ai_notes"
        
        if not args.dry_run:
            temp_dir = Path(tempfile.mkdtemp(prefix='zim_import_'))
            print(f"Using temporary directory: {temp_dir}")
        
        print(f"Notable directory: {notable_dir}")
        print(f"Zim directory: {zim_dir}")
        print(f"Raw AI notes will be stored in: {raw_store}")
        print(f"Journal links will be added to: {journal_root}")
        
        if args.dry_run:
            print("\n[DRY RUN MODE] - No files will be modified")
        
        if not args.dry_run:
            ensure_dir(raw_store)
            ensure_dir(journal_root)
            raw_root_page = zim_dir / "raw_ai_notes.txt"
            if not raw_root_page.exists():
                if write_file(raw_root_page, zim_header("Raw AI Notes")):
                    print(f"Created Zim root page: {raw_root_page}")
        
        md_files = list(notable_dir.glob("*.md"))
        if not md_files:
            log_warning(f"No .md files found in {notable_dir}")
            return
        
        def get_sort_key(md_file: Path) -> datetime:
            content = read_file(md_file)
            _, metadata = parse_yaml_front_matter(content)
            return get_file_date(md_file, metadata)
        
        md_files.sort(key=get_sort_key)
        
        print(f"\nFound {len(md_files)} markdown files to process")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        used_slugs = set()
        
        for i, md_file in enumerate(md_files, 1):
            print(f"\n[{i}/{len(md_files)}] Processing: {md_file.name}")
            
            if args.dry_run:
                content = read_file(md_file)
                _, metadata = parse_yaml_front_matter(content)
                title = metadata.get('title', md_file.stem)
                slug = slugify(title, raw_store, used_slugs)
                note_file = raw_store / f"{slug}.txt"
                is_new_file = not note_file.exists()
                needs_reimport = needs_update(md_file, note_file, metadata)
                journal_date_key = 'created' if is_new_file else 'modified'
                journal_ts = get_file_date(md_file, metadata, journal_date_key)
                year = journal_ts.strftime("%Y")
                month = journal_ts.strftime("%m")
                day = journal_ts.strftime("%d")
                journal_page = journal_root / year / month / f"{day}.txt"
                if note_file.exists() and not needs_reimport:
                    print(f"  Would skip (already exists and up-to-date): {note_file.name}")
                    skip_count += 1
                else:
                    print(f"  Would import as: {note_file.name}")
                    print(f"  Would add journal link to: {journal_page}")
                    success_count += 1
            else:
                result = import_md_file(md_file, raw_store, journal_root, log_file, temp_dir, used_slugs)
                if result == ImportStatus.SUCCESS:
                    success_count += 1
                elif result == ImportStatus.SKIPPED:
                    skip_count += 1
                elif result == ImportStatus.ERROR:
                    error_count += 1    
                else:
                    log_error(f"Unexpected result for {md_file}: {result}")
                    error_count += 1
                      
        print(f"\n{'='*50}")
        print("IMPORT SUMMARY")
        print(f"{'='*50}")
        print(f"Total files processed: {len(md_files)}")
        print(f"Successfully imported: {success_count}")
        print(f"Skipped (already exist): {skip_count}")
        print(f"Errors: {error_count}")
        
        if log_file and not args.dry_run:
            summary = (
                f"\n=== Import session completed at {datetime.now(timezone.utc).isoformat()} ===\n"
                f"Total: {len(md_files)}, Success: {success_count}, "
                f"Skipped: {skip_count}, Errors: {error_count}\n"
            )
            append_file(log_file, summary)
            print(f"\nDetailed log written to: {log_file}")
        
    except SystemExit:
        raise
    except Exception as e:
        log_error(f"Unexpected error during import process: {e}")
        sys.exit(1)
    
    finally:
        if 'temp_dir' in locals() and temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                log_warning(f"Could not clean up temporary directory {temp_dir}: {e}")

if __name__ == "__main__":
    main()