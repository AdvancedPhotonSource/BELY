.PHONY: help install install-dev test lint format type-check clean docs

help:
	@echo "BELY MQTT Framework - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install the package"
	@echo "  make install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with black"
	@echo "  make type-check       Run type checking with mypy"
	@echo "  make quality          Run all quality checks"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Clean build artifacts"
	@echo "  make docs             Build documentation"
	@echo "  make run-example      Run example handler"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=src/bely_mqtt --cov-report=html --cov-report=term-missing

lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/bely_mqtt

quality: lint type-check test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf build/ dist/

docs:
	@echo "Documentation is in docs/ directory"
	@echo "Main files:"
	@echo "  - README.md: Overview and API reference"
	@echo "  - docs/QUICKSTART.md: Quick start guide"
	@echo "  - docs/HANDLER_DEVELOPMENT.md: Handler development guide"
	@echo "  - docs/ARCHITECTURE.md: Architecture documentation"

run-example:
	@echo "Starting BELY MQTT Framework with example handlers..."
	bely-mqtt start \
		--broker-host localhost \
		--broker-port 1883 \
		--handlers-dir ./examples/handlers \
		--topic "bely/#" \
		--log-level INFO

list-handlers:
	bely-mqtt list-handlers --handlers-dir ./examples/handlers
