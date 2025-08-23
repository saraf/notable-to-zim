# Changelog for Notable-to-Zim

All notable changes to the `import_notable.py` script will be documented in this file.

## [2.0.0] - 2025-08-23
### Added
- Added `utc_to_local` function to convert UTC timestamps to local timezone, ensuring journal pages align with user’s local calendar dates (e.g., a note created at 11 PM local time appears in that day’s journal, not the next day’s if UTC crosses midnight).
- Implemented `format_journal_link` and `create_journal_links_section` for journal backlinks in AI notes, linking notes to their creation/modification journal pages.
- Added `create_tag_string_for_zim` to normalize and format tags for Zim compatibility, handling hyphens, spaces, slashes, and special characters.
- Introduced comprehensive test suite across multiple files (`test_import_md_file.py`, `test_create_journal_links_section.py`, `test_zim_tag_creation.py`, `test_timezone_handling.py`, `test_backlinks.py`, `test_import_notable.py`) with pytest fixtures and mocking.
- Added `README.md` with project overview, installation, usage, and contribution guidelines.

### Changed
- Bumped version to 2.0.0 to reflect major enhancements in functionality, testing, and timezone handling.
- Updated `import_notable.py` to v2.0.0, fixing duplicate titles, tags placement, and journal link deduplication.
- Enhanced `needs_update` to handle UTC timestamps with local timezone conversion and improved logging for YAML vs. filesystem comparisons.
- Fixed Pandoc command to use `-f markdown-smart+lists_without_preceding_blankline+yaml_metadata_block` for robust list parsing and YAML handling.
- Applied Black autoformatting and configured flake8 with `max-line-length=88` for consistent code style (commits `7dfc0b3`, `11bb9c6`).
- Updated `Makefile` with `coverage`, `zim-run-dry`, and `check-pandoc` targets for better automation.
- Kept all fixes from v1.9.15 (last known good state) and v1.9.25, including `--log-level` support and MSYS2 path compatibility (`/g/My Drive/MarkdownNotes/notes/`, `/d/aalhad/TestNotable`).

### Fixed
- Fixed five test failures from v1.9.23 (`test_parse_yaml_front_matter`, `test_parse_timestamp`, `test_get_file_date`, `test_needs_update`, `test_import_md_file`) by improving datetime mocking, file operation mocks, and YAML parsing.
- Resolved `FileNotFoundError` in `test_import_md_file` with safer unlink operations and proper file mocks (commit `dccbd60`).
- Fixed `isinstance` issue in `test_get_file_date` by using a `MockDatetimeClass` that preserves datetime type checks (commit `6f03fd8`).
- Corrected Pandoc YAML parsing conflicts with horizontal rule syntax by adding `-yaml_metadata_block` extension (commit `a3eaefb`).
- Fixed list formatting issues in Pandoc with `+lists_without_preceding_blankline` (commit `21f4360`).

### Removed
- Removed outdated `test_import_notable_old.py` (commit `d497030`).
- Removed redundant debug logs in `get_file_date` for cleaner output (commit `d497030`).

### Dependencies
- Added `pytest-cov>=4.0.0` for coverage reports (commit `d497030`).
- No new runtime dependencies beyond existing `python-dateutil`, `pyyaml==6.0.1`, and `pandoc`.

## [1.9.15] - 2025-08-19
- Fixed tags placement in `create_zim_note` to append tags at the end of the content.
- Fixed duplicate titles in Zim notes by improving `remove_duplicate_heading` regex to handle quotes and special characters in Pandoc zimwiki output.
- Updated `test_create_zim_note` to verify tags at the end of the note.
- Updated `test_remove_duplicate_heading` to test titles with quotes and Pandoc-style headings.
- Kept `note_path` fix, journal title format 'Tuesday DD Mon YYYY', `section_title='AI Notes'`, and `[Errno 2]` fix from v1.9.14 and earlier.

## [1.9.14] - 2025-08-19
- Fixed `NameError` in `import_md_file` by replacing incorrect `note_path` with `note_file` in `create_zim_note` call.
- Updated `test_import_md_file` to include a real `create_zim_note` call to catch variable errors.

## [1.9.13] - 2025-08-19
- Fixed journal page titles to use format 'Tuesday DD Mon YYYY' (e.g., 'Tuesday 18 Aug 2025') instead of 'Journal DD'.
- Added `format_journal_title` helper to parse date from `page_path` or `journal_date`.
- Updated `create_journal_page` and `append_journal_link` to use formatted titles.
- Updated `import_md_file` to pass `journal_ts` to `append_journal_link` for title formatting.
- Updated tests to verify correct journal page titles.

## [1.9.10] - 2025-08-19
- Enhanced `needs_update` with explicit conditional logging for YAML and filesystem timestamp comparisons.
- Removed redundant debug logs in `get_file_date` for cleaner output.
- Simplified journal link debug log in `import_md_file`.
- Updated `test_import_notable.py` to fix 12 test failures (subprocess imports, assertions for `slugify`, `read_file`, `append_file`, etc.).
- Removed outdated `test_import_notable_old.py`, which tested pre-v1.9.9 behavior.
- Ensured compatibility with MSYS2 paths (`/g/My Drive/MarkdownNotes/notes/`, `/d/aalhad/TestNotable`).
- Moved historical changelog entries (v1.8–v1.9.8) to this `CHANGELOG.md` file.
- No new dependencies required.

## [1.9.9] - 2025-07-15
- Fixed `needs_update` to handle UTC timestamps in YAML by converting `st_mtime` to UTC for comparison.
- Added deduplication of journal links to prevent multiple identical links on the same day.
- Enhanced logging in `needs_update` to include UTC and local timestamps with microsecond precision.
- Kept Pandoc `-f markdown-smart` and journal link support for updated notes from v1.9.8.
- No new dependencies required.

## [1.9.8] - 2025-06-20
- Fixed Pandoc command by replacing invalid `--no-smart` with `-f markdown-smart` to disable smart punctuation.
- Added debug logging for Pandoc command to aid troubleshooting.
- Kept journal link support for updated notes from v1.9.7.

## [1.9.7] - 2025-05-10
- Added journal link for updated notes based on YAML modified timestamp.
- Enhanced logging to track journal link additions for updated notes.
- Kept `slugify` base_slug check and duplicate heading fix from v1.9.6.

## [1.9.6] - 2025-04-05
- Fixed persistent duplicate heading by explicitly handling curly apostrophes in `remove_duplicate_heading`.
- Added path normalization for MSYS2 filenames with spaces/apostrophes in Pandoc call.
- Restored `slugify` base_slug check to prevent unnecessary suffixes (regression in earlier v1.9.6 draft).
- Enhanced debug logging for Pandoc input/output and heading removal.

## [1.9.5] - 2025-03-01
- Fixed persistent duplicate heading issue by improving Unicode normalization and regex in `remove_duplicate_heading`.
- Added debug logging for regex patterns.

## [1.9.4] - 2025-02-10
- Fixed multiple file copies by improving `needs_update` timestamp comparison and `slugify` logic.
- Improved `remove_duplicate_heading` to use `re.search` and log normalization details.

## [1.9.3] - 2025-01-15
- Fixed duplicate heading issue in Zim notes by normalizing Unicode characters in `remove_duplicate_heading`.
- Added `unicodedata` dependency for Unicode normalization.

## [1.9.2] - 2024-12-20
- Strengthened `temp_dir` check in `main()` to avoid `UnboundLocalError` by checking if `temp_dir` is defined.
- No new dependencies required.

## [1.9.1] - 2024-11-30
- Fixed `UnboundLocalError` for `temp_dir` when `--help` triggers early exit.
- Updated project name to Notable-to-Zim in docstring.
- No new dependencies required.

## [1.9] - 2024-11-01
- Added `--log-level` command-line argument to control console log verbosity (DEBUG, INFO, WARNING, ERROR).
- Modified `log_message` to filter console output based on log level, while writing all messages to log file.
- No new dependencies required.

## [1.8] - 2024-10-15
- Removed duplicate level-1 heading in `raw_ai_notes` output after Pandoc conversion if it matches the YAML title or file stem.
- Added debug logging for heading removal process.
- No new dependencies required.