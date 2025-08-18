.PHONY: all test clean lint setup venv

ZIM_NOTEBOOK_DIR := /d/aalhad/TestNotable
NOTABLE_NOTES_DIR := /g/My Drive/MarkdownNotes/notes/

all: test

test:
	@pytest tests/ --verbose

clean:
	@rm -rf __pycache__ tests/__pycache__ .pytest_cache venv
	@echo "Cleaned up cache directories and virtual environment"

zim-clean:
	@rm -rf $(ZIM_NOTEBOOK_DIR)/Journal/*
	@rm -rf $(ZIM_NOTEBOOK_DIR)/raw_ai_notes
	@rm -f $(ZIM_NOTEBOOK_DIR)/raw_ai_notes.txt
	@rm -f *.log
	@echo "Cleaned up the Zim raw ai notes area - and the Journal" 

zim-run:
	./import_notable.py --notable-dir "$(NOTABLE_NOTES_DIR)" --zim-dir "$(ZIM_NOTEBOOK_DIR)" --log-file test.log
# ./import_notable.py --notable-dir "/g/My Drive/MarkdownNotes/notes/" --zim-dir $(ZIM_NOTEBOOK_DIR) --log-file test.log

lint:
	@pylint import_notable.py

venv:
	@command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 is not installed. Please install Python 3."; exit 1; }
	@python3 -m venv venv || { echo "[ERROR] Failed to create virtual environment. Ensure 'python3 -m venv' is available."; exit 1; }
	@echo "Virtual environment created at 'venv'. Activate it with:"
	@echo "  Linux/macOS: source venv/bin/activate"
	@echo "  Windows: venv\\Scripts\\activate"

setup: venv
	@venv/bin/python3 -m pip --version >/dev/null 2>&1 || { echo "[ERROR] pip not found in virtual environment. Try re-running 'make venv'."; exit 1; }
	@venv/bin/python3 -m pip install -r requirements.txt
	@echo "Dependencies installed in virtual environment successfully"
	@echo "Activate the virtual environment with:"
	@echo "  Linux/macOS: source venv/bin/activate"
	@echo "  Windows: venv\\Scripts\\activate"



# Add if using temp dirs in tests: clean-test-data or similar
