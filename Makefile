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

#test-data:
#	@rm -rf tests/temp_data
#	@echo "Removed temporary test data"
#.PHONY: setup test-data
#setup: clean test-data
#	@echo "Setup complete, ready to run tests"		
#	@python import_notable.py  # Run the main script if needed
#	@echo "Main script executed"
#	@echo "All tasks completed successfully"
#
# Additional targets can be added as needed
# For example, to run the main script directly:
# run:
# 	@python import_notable.py
# 	@echo "Main script executed"
# To run specific tests, you can add:
# test-specific:
# 	@pytest tests/test_specific.py --verbose
# To run all tests with coverage, you can add:
# coverage:
# 	@coverage run -m pytest tests/ --verbose
# 	@coverage report -m
# 	@coverage html  # Generates an HTML report
# 	@echo "Coverage report generated"
# To run the main script with specific arguments, you can add:
# run-args:
# 	@python import_notable.py --arg1 value1 --arg2 value2
# 	@echo "Main script executed with arguments"
# To run the main script with a specific configuration, you can add:
# run-config:
# 	@python import_notable.py --config config_file.json
# 	@echo "Main script executed with configuration"
# To run the main script with a specific environment, you can add:
# run-env:
# 	@python import_notable.py --env production
# 	@echo "Main script executed in production environment"
# To run the main script with a specific logging level, you can add:
# run-logging:
# 	@python import_notable.py --log-level DEBUG
# 	@echo "Main script executed with DEBUG logging level"
# To run the main script with a specific output format, you can add:
# run-output:
# 	@python import_notable.py --output-format json