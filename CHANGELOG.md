# Changelog for Notable-to-Zim

All notable changes to the `import_notable.py` script will be documented in this file.

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
