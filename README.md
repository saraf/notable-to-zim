# Notable-to-Zim

**Notable-to-Zim** is a Python tool to import Markdown notes from [Notable](https://notable.app/) into a [Zim Desktop Wiki](https://zim-wiki.org/) notebook. It converts Notable's Markdown files, including YAML front matter, into Zim-compatible wiki pages, stores them in a `raw_ai_notes` folder, and appends links to chronological Journal pages in the Zim notebook.

## Features
- Converts Notable Markdown files to Zim wiki format using Pandoc.
- Extracts YAML metadata (title, tags, created/modified dates) for proper Zim integration.
- Handles duplicate titles by generating unique slugs.
- Creates or updates Journal pages with links to imported notes.
- Supports configurable console log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- Removes duplicate headings in output to ensure clean Zim pages.
- Logs import details to a file for debugging and tracking.

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Pandoc**: Required for Markdown to Zim wiki conversion. Install from [pandoc.org](https://pandoc.org/).
- **Zim Desktop Wiki**: Version 0.6 or compatible, for the target notebook.
- **Notable**: Source Markdown notes exported from Notable.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/saraf/notable-to-zim.git
   cd notable-to-zim
   ```

2. **Set Up a Virtual Environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Pandoc**:
   - On Ubuntu/Debian:
     ```bash
     sudo apt-get install pandoc
     ```
   - On macOS:
     ```bash
     brew install pandoc
     ```
   - On Windows (MSYS2):
     ```bash
     pacman -S mingw-w64-x86_64-pandoc
     ```
   - Or download from [pandoc.org/installing](https://pandoc.org/installing.html).

5. **Verify Setup**:
   Ensure Pandoc is in your PATH:
   ```bash
   pandoc --version
   ```

## Usage
Run the `import_notable.py` script to import Notable Markdown notes into a Zim notebook:

```bash
python3 import_notable.py --notable-dir <path-to-notable-notes> --zim-dir <path-to-zim-notebook>
```

### Options
- `--notable-dir`: Directory containing Notable `.md` files (required).
- `--zim-dir`: Root directory of the Zim notebook (required).
- `--log-file`: Path to a log file for detailed import records (optional).
- `--log-level`: Console log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`; default: `INFO`).
- `--dry-run`: Simulate the import process without modifying files.

### Example
Import notes from `~/notable` to `~/zim_notebook` with a log file and minimal console output:

```bash
python3 import_notable.py --notable-dir ~/notable --zim-dir ~/zim_notebook --log-file ~/import.log --log-level WARNING
```

This will:
- Convert each `.md` file to Zim wiki format.
- Store converted notes in `~/zim_notebook/raw_ai_notes`.
- Add links to `~/zim_notebook/Journal/YYYY/MM/DD.txt` based on the note's creation date.
- Log details to `~/import.log` and show only warnings/errors on the console.

### Example Input (Notable Markdown)
```markdown
---
title: Cognitively Rich Anki Card Checklist - Examples
tags: [anki, checklist]
created: 2025-07-24T12:55:26.779Z
modified: 2025-07-24T13:00:44.505Z
---
# Cognitively Rich Anki Card Checklist - Examples
Content here.
```

### Example Output (Zim Note)
`raw_ai_notes/cognitively_rich_anki_card_checklist_examples.txt`:
```
Content-Type: text/x-zim-wiki
Wiki-Format: zim 0.6
Creation-Date: 2025-08-18T...

====== Cognitively Rich Anki Card Checklist - Examples ======

Content here.

**Tags:** @anki @checklist
```

## Project Structure
```
notable-to-zim/
├── import_notable.py      # Main script for importing notes
├── requirements.txt       # Python dependencies
├── Makefile              # Build and test automation
├── tests/                # Unit tests
│   ├── __init__.py
│   └── test_import_notable.py
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
└── README.md             # This file
```

## Development
To run tests or lint the code:

1. **Install Development Dependencies**:
   ```bash
   make setup
   ```

2. **Run Tests**:
   ```bash
   make test
   ```

3. **Run Linter**:
   ```bash
   make lint
   ```

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please ensure code passes tests and linting before submitting.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Issues
Report bugs or suggest features via [GitHub Issues](https://github.com/saraf/notable-to-zim/issues).

## Acknowledgments
- Built with [Python](https://python.org/), [Pandoc](https://pandoc.org/), and [PyYAML](https://pyyaml.org/).
- Inspired by the need to integrate Notable's Markdown notes with Zim's wiki system.