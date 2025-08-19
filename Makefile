# Makefile for Notable-to-Zim project
# Supports running pytest tests, coverage, linting, virtual environment setup, and script execution
# Compatible with MSYS2 and Python 3.12.11

PYTHON = python3
PYTEST = pytest
PIP = pip3
NOTABLE_NOTES_DIR = /g/My Drive/MarkdownNotes/notes/
ZIM_NOTEBOOK_DIR = /d/aalhad/TestNotable
LOG_FILE = test.log

.PHONY: all test coverage clean zim-clean zim-run zim-run-dry lint setup venv check-pandoc

all: test lint

# Run all unit tests with verbose output
test:
	@$(PYTHON) -m $(PYTEST) tests/ --verbose

# Run tests with coverage report
coverage:
	@$(PYTHON) -m $(PYTEST) tests/ --verbose --cov=import_notable --cov-report=term-missing

# Clean up cache directories, virtual environment, and logs
clean:
	@rm -rf __pycache__ tests/__pycache__ .pytest_cache venv *.log
	@echo "Cleaned up cache directories, virtual environment, and logs"

# Clean up Zim notebook for testing
zim-clean:
	@rm -rf $(ZIM_NOTEBOOK_DIR)/Journal/*
	@rm -rf $(ZIM_NOTEBOOK_DIR)/raw_ai_notes
	@rm -f $(ZIM_NOTEBOOK_DIR)/raw_ai_notes.txt
	@echo "Cleaned up Zim notebook Journal and raw_ai_notes"

# Run import_notable.py with debug logging
zim-run:
	@$(PYTHON) import_notable.py --notable-dir "$(NOTABLE_NOTES_DIR)" --zim-dir "$(ZIM_NOTEBOOK_DIR)" --log-file $(LOG_FILE) --log-level DEBUG

# Run import_notable.py in dry-run mode
zim-run-dry:
	@$(PYTHON) import_notable.py --notable-dir "$(NOTABLE_NOTES_DIR)" --zim-dir "$(ZIM_NOTEBOOK_DIR)" --log-file $(LOG_FILE) --log-level DEBUG --dry-run

# Lint code with flake8
lint:
	@$(PIP) install flake8
	@flake8 import_notable.py tests/test_import_notable.py

# Create virtual environment
venv:
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "[ERROR] python3 is not installed. Please install Python 3."; exit 1; }
	@$(PYTHON) -m venv venv || { echo "[ERROR] Failed to create virtual environment. Ensure 'python3 -m venv' is available."; exit 1; }
	@echo "Virtual environment created at 'venv'. Activate it with:"
	@echo "  Linux/macOS: source venv/bin/activate"
	@echo "  Windows/MSYS2: source venv/Scripts/activate"

# Install dependencies in virtual environment
setup: venv
	@venv/bin/python3 -m pip --version >/dev/null 2>&1 || { echo "[ERROR] pip not found in virtual environment. Try re-running 'make venv'."; exit 1; }
	@venv/bin/python3 -m pip install -r requirements.txt
	@venv/bin/python3 -m pip install pytest pytest-cov flake8
	@echo "Dependencies installed in virtual environment successfully"
	@echo "Activate the virtual environment with:"
	@echo "  Linux/macOS: source venv/bin/activate"
	@echo "  Windows/MSYS2: source venv/Scripts/activate"

# Check if Pandoc is installed
check-pandoc:
	@command -v pandoc >/dev/null 2>&1 || { echo "[ERROR] Pandoc is not installed. Install it from https://pandoc.org/"; exit 1; }
	@echo "Pandoc is installed"