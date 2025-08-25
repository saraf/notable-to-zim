# Makefile for Notable-to-Zim project
# Supports running pytest tests, coverage, linting, virtual environment setup, and script execution
# Compatible with MSYS2 and Python 3.12.11

# Smart Python detection - tries multiple common paths
PYTHON := $(shell command -v python3 2>/dev/null || command -v /mingw64/bin/python3 2>/dev/null || command -v /usr/bin/python3 2>/dev/null || echo "python3-not-found")

# Use venv Python when available, fallback to system Python
VENV_PYTHON = $(shell [ -f venv/bin/python3 ] && echo "venv/bin/python3" || echo "$(PYTHON)")
PYTEST = pytest
PIP = pip3
NOTABLE_NOTES_DIR = /g/My Drive/MarkdownNotes/notes/
ZIM_NOTEBOOK_DIR = /d/aalhad/TestNotable
LOG_FILE = test.log

.PHONY: all test coverage clean zim-clean zim-run zim-run-dry lint setup venv check-pandoc check-python format format-check

all: test lint

# Check Python installation before doing anything
check-python:
	@if [ "$(PYTHON)" = "python3-not-found" ]; then \
		echo "[ERROR] Python 3 not found. Please install Python 3 or ensure it's in PATH."; \
		echo "For MSYS2, try: pacman -S mingw-w64-x86_64-python"; \
		echo "Common Python locations:"; \
		echo "  - /mingw64/bin/python3"; \
		echo "  - /usr/bin/python3"; \
		echo "  - python3 (if in PATH)"; \
		exit 1; \
	fi
	@echo "Using Python: $(PYTHON)"
	@$(PYTHON) --version

# Run all unit tests with verbose output
test:
	@$(VENV_PYTHON) -m $(PYTEST) tests/ --verbose

# Run tests with coverage report
coverage:
	@$(VENV_PYTHON) -m $(PYTEST) tests/ --verbose --cov=import_notable --cov-report=term-missing

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
	@$(VENV_PYTHON) import_notable.py --notable-dir "$(NOTABLE_NOTES_DIR)" --zim-dir "$(ZIM_NOTEBOOK_DIR)" --log-file $(LOG_FILE) --log-level DEBUG

# Run import_notable.py in dry-run mode
zim-run-dry:
	@$(VENV_PYTHON) import_notable.py --notable-dir "$(NOTABLE_NOTES_DIR)" --zim-dir "$(ZIM_NOTEBOOK_DIR)" --log-file $(LOG_FILE) --log-level DEBUG --dry-run

# Format code with Black
format:
	@$(VENV_PYTHON) -m black import_notable.py tests/
	@echo "Code formatted with Black"

# Check formatting without modifying files
format-check:
	@$(VENV_PYTHON) -m black --check import_notable.py tests/

# Enhanced linting target
lint: format-check
	@$(VENV_PYTHON) -m flake8 import_notable.py tests/

# Create virtual environment
venv: check-python
	@$(PYTHON) -m venv venv || { echo "[ERROR] Failed to create virtual environment. Ensure 'python3 -m venv' is available."; exit 1; }
	@echo "Virtual environment created at 'venv'. Activate it with:"
	@echo "  MSYS2/Linux: source venv/bin/activate"
	@echo "  Windows: source venv/Scripts/activate"

# Install dependencies in virtual environment
setup: venv
	@venv/bin/python3 -m pip --version >/dev/null 2>&1 || { echo "[ERROR] pip not found in virtual environment. Try re-running 'make venv'."; exit 1; }
	@if [ -f "requirements-dev.txt" ]; then \
		echo "Installing development dependencies from requirements-dev.txt"; \
		venv/bin/python3 -m pip install -r requirements-dev.txt; \
	elif [ -f "requirements.txt" ]; then \
		echo "Installing dependencies from requirements.txt"; \
		venv/bin/python3 -m pip install -r requirements.txt; \
		echo "Installing additional development tools"; \
		venv/bin/python3 -m pip install pytest pytest-cov flake8 black; \
	else \
		echo "[WARNING] No requirements.txt or requirements-dev.txt found"; \
		echo "Installing basic development tools"; \
		venv/bin/python3 -m pip install pytest pytest-cov flake8 black pyyaml python-dateutil; \
	fi
	@echo "Dependencies installed in virtual environment successfully"
	@echo "Activate the virtual environment with:"
	@echo "  MSYS2/Linux: source venv/bin/activate"

# Check if Pandoc is installed
check-pandoc:
	@command -v pandoc >/dev/null 2>&1 || { echo "[ERROR] Pandoc is not installed. Install it from https://pandoc.org/"; exit 1; }
	@echo "Pandoc is installed"