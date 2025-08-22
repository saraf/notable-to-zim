#!/usr/bin/env python3
"""
import_notable.py - VERSION v1.9.15

Import Notable Markdown notes into a Zim Desktop Wiki notebook,
creating raw AI notes with proper Zim metadata, and appending
links to the Journal pages in chronological order under a specified section.

Part of the Notable-to-Zim project.

CHANGES IN v1.9.15:
- Fixed tags placement in create_zim_note to append tags at the end of the content.
- Fixed duplicate titles in Zim notes by improving remove_duplicate_heading regex
  to handle quotes and special characters in Pandoc zimwiki output.
- Updated test_create_zim_note to verify tags at the end of the note.
- Updated test_remove_duplicate_heading to test titles with quotes and
  Pandoc-style headings.
- Kept note_path fix, journal title format 'Tuesday DD Mon YYYY',
  section_title='AI Notes', and [Errno 2] fix from v1.9.14 and earlier.

CHANGES IN v1.9.14:
- Fixed NameError in import_md_file by replacing incorrect 'note_path' with
  'note_file' in create_zim_note call.
- Updated test_import_md_file to include a real create_zim_note call to catch variable
  errors.

CHANGES IN v1.9.13:
- Fixed journal page titles to use format 'Tuesday DD Mon YYYY'
  (e.g., 'Tuesday 18 Aug 2025')
  instead of 'Journal DD'.
- Added format_journal_title helper to parse date from page_path or journal_date.
- Updated create_journal_page and append_journal_link to use formatted titles.
- Updated import_md_file to pass journal_ts to append_journal_link for title formatting.
- Updated tests to verify correct journal page titles.

See CHANGELOG.md for historical changes (v1.8–v1.9.9).
Dependencies: python-dateutil, pyyaml==6.0.1, pandoc
"""

# ------------------------ Imports ------------------------
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
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
        raise ValueError(
            f"Invalid log level: {level}. Choose from DEBUG, INFO, WARNING, ERROR."
        )


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


def log_debug(message: str) -> None:
    """Log debug message."""
    log_message(message, "DEBUG")


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
    """Read file content, handling errors."""
    try:
        with path.open(encoding="utf-8") as f:
            return f.read()
    except (IOError, OSError) as e:
        log_error(f"Could not read file {path}: {e}")
        return ""


def write_file(path: Path, content: str) -> bool:
    """Write content to file, creating parent directories if needed."""
    try:
        ensure_dir(path.parent)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        return True
    except (IOError, OSError) as e:
        log_error(f"Could not write file {path}: {e}")
        return False


def append_file(path: Path, content: str) -> bool:
    """Append content to file, creating parent directories if needed."""
    try:
        ensure_dir(path.parent)
        with path.open("a", encoding="utf-8") as f:
            f.write(content)
        return True
    except (IOError, OSError) as e:
        log_error(f"Could not append to file {path}: {e}")
        return False


def check_pandoc() -> bool:
    """Check if pandoc is installed and available."""
    try:
        subprocess.run(
            ["pandoc", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_pandoc(input_path: Path, output_path: Path) -> bool:
    """Convert Markdown to Zim Wiki format using Pandoc."""
    try:
        subprocess.run(
            [
                "pandoc",
                "-f",
                "markdown-smart-yaml_metadata_block+lists_without_preceding_blankline",
                "-t",
                "zimwiki",
                str(input_path),
                "-o",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Pandoc conversion failed: {e.stderr}")
        return False
    except FileNotFoundError:
        log_error("Pandoc not found in system PATH")
        return False


def zim_header(title: str) -> str:
    """Generate Zim Wiki page header."""
    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"Content-Type: text/x-zim-wiki\n"
        f"Wiki-Format: zim 0.6\n"
        f"Creation-Date: {created}\n"
        f"\n"
        f"====== {title} ======\n"
    )


def format_journal_title(page_path: Path = None, journal_date: datetime = None) -> str:
    """Format journal title as 'Tuesday DD Mon YYYY' from page_path or journal_date."""
    if journal_date:
        return journal_date.strftime("%A %d %b %Y")
    try:
        # Extract date from page_path like Journal/YYYY/MM/DD.txt
        parts = page_path.parts
        year, month, day = parts[-3], parts[-2], parts[-1].replace(".txt", "")
        date = datetime(int(year), int(month), int(day))
        return date.strftime("%A %d %b %Y")
    except (IndexError, ValueError):
        log_error(f"Could not parse date from {page_path}, using fallback title")
        return f"Journal {page_path.stem}"


def create_journal_page(page_path: Path) -> bool:
    """Create a new journal page with a formatted title."""
    title = format_journal_title(page_path=page_path)
    return write_file(page_path, zim_header(title))


# TODO: rename this function to better reflect its purpose
# We are appending a link to a raw AI note to a journal page
# hence, its should be append_note_link_to_journal_page
def append_journal_link(
    page_path: Path,
    title: str,
    link: str,
    journal_date: datetime = None,
    section_title: str = "AI Notes",
) -> bool:
    """Append a note link to a journal page under a specified section,
    avoiding duplicates."""
    section_header = f"===== {section_title} ====="
    link_line = f"* [[{link}|{title}]]\n"
    title = format_journal_title(page_path=page_path, journal_date=journal_date)
    if not page_path.exists():
        content = zim_header(title) + f"\n{section_header}\n{link_line}"
        return write_file(page_path, content)
    content = read_file(page_path)
    if not content:
        content = zim_header(title) + f"\n{section_header}\n{link_line}"
        return write_file(page_path, content)
    if link_line.strip() in content.splitlines():
        return True
    # Check if section exists, append link under it
    section_pattern = re.compile(rf"^{re.escape(section_header)}\s*\n", re.MULTILINE)
    if section_pattern.search(content):
        # Insert link at the end of the section
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                # Find the end of the section (next header or end of file)
                j = i + 1
                while j < len(lines) and not lines[j].startswith("====="):
                    j += 1
                lines.insert(j, link_line.strip())
                content = "\n".join(lines)
                return write_file(page_path, content.rstrip("\n") + "\n")
    else:
        # Append section and link
        content = content.rstrip("\n") + f"\n\n{section_header}\n{link_line}"
        return write_file(page_path, content)
    return False


def create_tag_string_for_zim(tags: List[str]) -> str:
    """
    Build Zim tag string: underscores replace invalid chars;
    slashes keep only last part;
    empty tags ignored.
    Returns '@tag1 @tag2 ...' or ''.
    """
    if not tags:
        return ""
    cleaned_tags = []
    for tag in tags:
        if not tag:
            continue
        # If slash is present, use only last part
        if "/" in tag:
            tag = tag.split("/")[-1]
        # Replace special characters and formatting
        tag = re.sub(r"[\'\"]", "", tag)  # Remove quotes and apostrophes
        tag = unicodedata.normalize("NFKD", tag)  # Normalize unicode characters
        tag = tag.strip()  # Remove leading/trailing whitespace

        tag = re.sub(
            r"[\'\"\.\,\:\;\?\!\+\&\$\%\#\\\*]", "_", tag
        )  # Replace listed special chars with underscore
        tag = tag.replace("-", "_").replace(" ", "_").replace("'", "_")
        tag = re.sub(
            r"[^A-Za-z0-9_]", "", tag
        )  # Remove any remaining non-alphanumeric/underscore chars

        # Only add the tag if it contains at least one alphanumeric character
        if tag and re.search(r"[A-Za-z0-9]", tag):
            cleaned_tags.append(f"@{tag}")
    if not cleaned_tags:
        return ""
    else:
        return " ".join(cleaned_tags)


def create_zim_note(
    note_path: Path,
    title: str,
    content: str,
    tags: List[str],
    created_date: Optional[datetime] = None,
    modified_date: Optional[datetime] = None,
) -> bool:
    """
    Create a Zim note with proper formatting, tags at the end, and optional journal links.

    Args:
        note_path: Path where the note will be created
        title: Title of the note
        content: Main content of the note
        tags: List of tags for the note
        created_date: Creation date for journal link (optional)
        modified_date: Modification date for journal link (optional)

    Returns:
        True if successful, False otherwise
    """
    # Remove duplicate heading
    content = remove_duplicate_heading(content, title, note_path.stem)

    # Create journal links section if we have valid dates
    journal_links = create_journal_links_section(created_date, modified_date)

    # Create tags string
    tags_str = create_tag_string_for_zim(tags)

    # Assemble the full content
    header = zim_header(title)
    full_content = f"{header}\n{content}{journal_links}"

    # Add tags at the end
    if tags_str:
        full_content += f"\n{tags_str}\n"
    else:
        full_content += "\n"

    return write_file(note_path, full_content)


def remove_duplicate_heading(content: str, title: str, slug: str) -> str:
    """Remove duplicate heading if it matches title or slug,
    handling special characters."""

    # Normalize title and slug, preserving quotes and apostrophes
    title_clean = title.strip()
    slug_clean = slug.replace("_", " ").strip()
    # Escape special regex characters, but keep quotes and apostrophes
    title_escaped = re.escape(title_clean).replace(r"\'", "'")
    slug_escaped = re.escape(slug_clean).replace(r"\'", "'")
    # Match Zim Wiki level 1 heading (======) with flexible whitespace and case
    heading_pattern = re.compile(
        r"^======\s*({}|{})\s*======\s*\n".format(title_escaped, slug_escaped),
        re.MULTILINE | re.IGNORECASE,
    )
    return heading_pattern.sub("", content).strip()


def parse_timestamp(timestamp: Any) -> Optional[datetime]:
    """Parse ISO 8601 timestamp or datetime object from YAML,
    preserving UTC timezone."""
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp
    if isinstance(timestamp, str):
        try:
            parsed = dateutil_parser.parse(timestamp, ignoretz=False)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (ValueError, TypeError):
            log_error(f"Invalid timestamp format: {timestamp}")
            return None
    log_error(f"Invalid timestamp type: {type(timestamp)}")
    return None


def get_file_date(
    md_file: Path, metadata: Dict[str, Any], date_type: str = "created"
) -> datetime:
    """Extract timestamp from metadata or file system."""
    timestamp = metadata.get(date_type)
    ts = parse_timestamp(timestamp)
    if ts:
        return ts
    try:
        stat = md_file.stat()
        return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    except Exception as e:
        log_error(f"Cannot access timestamp for {md_file}: {e}")
        return datetime.now(timezone.utc)


def needs_update(md_file: Path, note_file: Path, metadata: Dict[str, Any]) -> bool:
    """Check if note needs to be re-imported based on timestamps."""
    if not note_file.exists():
        return True
    md_ts = get_file_date(md_file, metadata, "modified")
    try:
        note_stat = note_file.stat()
        note_ts = datetime.fromtimestamp(note_stat.st_mtime, tz=timezone.utc)
        return md_ts > note_ts
    except Exception as e:
        log_error(f"Cannot access timestamp for {note_file}: {e}")
        return True


def format_journal_link(date: datetime, link_type: str = "Created") -> str:
    """
    Format a journal link for insertion into Zim notes.

    Args:
        date: The datetime object for the journal date
        link_type: Type of link ("Created" or "Modified")

    Returns:
        Formatted journal link string
    """
    if not date:
        return ""

    if not isinstance(date, datetime):
        log_error(f"Invalid date type: {type(date)}. Expected datetime.")
        return ""
    if date.tzinfo is None:
        log_error("Date must have timezone info. Assuming UTC.")
        date = date.replace(tzinfo=timezone.utc)
    if link_type is None:
        link_type = "Created"
    elif not link_type.strip():
        link_type = ""

    try:
        formatted_date = date.strftime("%Y:%m:%d")
        journal_path = f"Journal:{formatted_date}"
        display_text = f"{link_type} on {date.strftime('%B %d %Y')}"
        return f"[[{journal_path}|{display_text}]]"
    except (ValueError, TypeError) as e:
        log_error(f"Error formatting journal link: {e}")
        return ""


def create_journal_links_section(
    created_date: Optional[datetime], modified_date: Optional[datetime]
) -> str:
    """
    Create a journal links section for Zim notes.

    Args:
        created_date: Creation date of the note
        modified_date: Modification date of the note

    Returns:
        Formatted journal links section or empty string if no valid dates
    """
    links = []

    # Add created link if we have a valid created date
    created_link = format_journal_link(created_date, "Created")
    if created_link:
        links.append(created_link)

    # Add modified link only if:
    # 1. We have a valid modified date
    # 2. It's different from the created date (to avoid duplicates)
    if modified_date and modified_date != created_date:
        modified_link = format_journal_link(modified_date, "Modified")
        if modified_link:
            links.append(modified_link)

    # Return empty string if no valid links
    if not links:
        return ""

    # Create the formatted section
    section_content = "\n".join(f"* {link}" for link in links)
    return f"\n**Journal Links:**\n{section_content}\n"


# ------------------------ End Helper Functions ------------------------


def import_md_file(
    md_file: Path,
    raw_dir: Path,
    journal_dir: Path,
    log_file: Optional[Path],
    temp_dir: Path,
    used_slugs: set,
) -> ImportStatus:
    """Import a single Markdown file into the Zim notebook."""
    content = read_file(md_file)
    if not content:
        return ImportStatus.ERROR

    body, metadata = parse_yaml_front_matter(content)
    title = metadata.get("title", md_file.stem)
    tags = metadata.get("tags", [])

    # Extract dates for journal links
    created_date = None
    modified_date = None

    # Try to get dates from metadata first
    if metadata.get("created"):
        created_date = parse_timestamp(metadata["created"])
    if metadata.get("modified"):
        modified_date = parse_timestamp(metadata["modified"])

    # Fallback to file dates if not in metadata
    if not created_date:
        created_date = get_file_date(md_file, metadata, "created")
    if not modified_date:
        modified_date = get_file_date(md_file, metadata, "modified")

    slug = slugify(title, raw_dir, used_slugs)
    note_file = raw_dir / f"{slug}.txt"

    if not needs_update(md_file, note_file, metadata):
        log_message(f"Skipping {md_file.name}: already up-to-date", "INFO")
        return ImportStatus.SKIPPED

    log_message(f"Importing {md_file.name} as {note_file.name}", "INFO")

    temp_input = temp_dir / f"{slug}.md"
    temp_output = temp_dir / f"{slug}.txt"
    write_file(temp_input, body)

    if not run_pandoc(temp_input, temp_output):
        log_error(f"Failed to convert {md_file.name} with Pandoc")
        temp_input.unlink()
        return ImportStatus.ERROR

    zim_content = read_file(temp_output)
    temp_input.unlink()
    temp_output.unlink()

    if not zim_content:
        log_error(f"No content generated for {md_file.name}")
        return ImportStatus.ERROR

    # Create Zim note with journal links
    if not create_zim_note(
        note_file, title, zim_content, tags, created_date, modified_date
    ):
        log_error(f"Failed to create Zim note {note_file}")
        return ImportStatus.ERROR

    # Existing journal link logic remains unchanged
    journal_date_key = "created" if not note_file.exists() else "modified"
    journal_ts = get_file_date(md_file, metadata, journal_date_key)
    year = journal_ts.strftime("%Y")
    month = journal_ts.strftime("%m")
    day = journal_ts.strftime("%d")
    journal_page = journal_dir / year / month / f"{day}.txt"

    if not append_journal_link(
        journal_page,
        title,
        f"raw_ai_notes:{slug}",
        journal_date=journal_ts,
        section_title="AI Notes",
    ):
        log_error(f"Failed to append journal link for {note_file.name}")
        return ImportStatus.ERROR

    return ImportStatus.SUCCESS


# def import_md_file(
#     md_file: Path,
#     raw_dir: Path,
#     journal_dir: Path,
#     log_file: Optional[Path],
#     temp_dir: Path,
#     used_slugs: set,
# ) -> ImportStatus:
#     """Import a single Markdown file into the Zim notebook."""
#     content = read_file(md_file)
#     if not content:
#         return ImportStatus.ERROR

#     body, metadata = parse_yaml_front_matter(content)
#     title = metadata.get("title", md_file.stem)
#     tags = metadata.get("tags", [])
#     log_debug(
#         f"Processing {md_file.name} with title '{title}'" f" and zzzztags: {tags}"
#     )

#     slug = slugify(title, raw_dir, used_slugs)
#     note_file = raw_dir / f"{slug}.txt"

#     if not needs_update(md_file, note_file, metadata):
#         log_message(f"Skipping {md_file.name}: already up-to-date", "INFO")
#         return ImportStatus.SKIPPED

#     log_message(f"Importing {md_file.name} as {note_file.name}", "INFO")

#     temp_input = temp_dir / f"{slug}.md"
#     temp_output = temp_dir / f"{slug}.txt"
#     write_file(temp_input, body)
#     # log_message(f"DEBUG: Writing to temp file for Pandoc:\n{body[:500]}...", "DEBUG")

#     if not run_pandoc(temp_input, temp_output):
#         log_error(f"Failed to convert {md_file.name} with Pandoc")
#         temp_input.unlink()
#         return ImportStatus.ERROR

#     zim_content = read_file(temp_output)
#     temp_input.unlink()
#     temp_output.unlink()

#     if not zim_content:
#         log_error(f"No content generated for {md_file.name}")
#         return ImportStatus.ERROR

#     if not create_zim_note(note_file, title, zim_content, tags):
#         log_error(f"Failed to create Zim note {note_file}")
#         return ImportStatus.ERROR

#     journal_date_key = "created" if not note_file.exists() else "modified"
#     journal_ts = get_file_date(md_file, metadata, journal_date_key)
#     year = journal_ts.strftime("%Y")
#     month = journal_ts.strftime("%m")
#     day = journal_ts.strftime("%d")
#     journal_page = journal_dir / year / month / f"{day}.txt"

#     if not append_journal_link(
#         journal_page,
#         title,
#         f"raw_ai_notes:{slug}",
#         journal_date=journal_ts,
#         section_title="AI Notes",
#     ):
#         log_error(f"Failed to append journal link for {note_file.name}")
#         return ImportStatus.ERROR

#     return ImportStatus.SUCCESS


def main():
    """Parse command-line arguments and run the import process."""
    parser = argparse.ArgumentParser(
        description="Import Notable notes to Zim Desktop Wiki"
    )
    parser.add_argument(
        "--notable-dir",
        type=Path,
        required=True,
        help="Path to Notable notes directory",
    )
    parser.add_argument(
        "--zim-dir", type=Path, required=True, help="Path to Zim notebook directory"
    )
    parser.add_argument("--log-file", type=Path, help="Path to log file")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run without writing files"
    )
    args = parser.parse_args()

    set_log_level(args.log_level)

    try:
        notable_dir = args.notable_dir
        zim_dir = args.zim_dir
        log_file = args.log_file

        if not notable_dir.exists():
            log_error(f"Notable directory does not exist: {notable_dir}")
            sys.exit(1)
        if not zim_dir.exists():
            log_error(f"Zim directory does not exist: {zim_dir}")
            sys.exit(1)

        if not check_pandoc():
            log_error("Pandoc is not installed or not found in PATH")
            sys.exit(1)

        if log_file:
            append_file(
                log_file,
                (
                    f"\n=== Import session started at "
                    f"{datetime.now(timezone.utc).isoformat()} ===\n"
                ),
            )

        set_log_file(log_file)

        journal_root = zim_dir / "Journal"
        raw_store = zim_dir / "raw_ai_notes"

        if not args.dry_run:
            temp_dir = Path(tempfile.mkdtemp(prefix="zim_import_"))
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
                title = metadata.get("title", md_file.stem)
                slug = slugify(title, raw_store, used_slugs)
                note_file = raw_store / f"{slug}.txt"
                is_new_file = not note_file.exists()
                needs_reimport = needs_update(md_file, note_file, metadata)
                journal_date_key = "created" if is_new_file else "modified"
                journal_ts = get_file_date(md_file, metadata, journal_date_key)
                year = journal_ts.strftime("%Y")
                month = journal_ts.strftime("%m")
                day = journal_ts.strftime("%d")
                journal_page = journal_root / year / month / f"{day}.txt"
                if note_file.exists() and not needs_reimport:
                    print(
                        f"  Would skip (already exists and up-to-date): "
                        f"{note_file.name}"
                    )
                    skip_count += 1
                else:
                    print(f"  Would import as: {note_file.name}")
                    print(f"  Would add journal link to: {journal_page}")
                    success_count += 1
            else:
                result = import_md_file(
                    md_file, raw_store, journal_root, log_file, temp_dir, used_slugs
                )
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
                f"\n=== Import session completed at "
                f"{datetime.now(timezone.utc).isoformat()} ===\n"
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
        if "temp_dir" in locals() and temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                log_warning(f"Could not clean up temporary directory {temp_dir}: {e}")


if __name__ == "__main__":
    main()
