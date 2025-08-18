.PHONY: all test clean lint setup venv

all: test

test:
	@pytest tests/ --verbose

clean:
	@rm -rf __pycache__ tests/__pycache__ .pytest_cache venv
	@echo "Cleaned up cache directories and virtual environment"

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
