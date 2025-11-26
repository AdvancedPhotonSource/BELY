.PHONY: help install install-dev test test-integration test-all lint format type-check clean docs

help:
	@echo "BELY MQTT Framework - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install the package"
	@echo "  make install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run unit tests"
	@echo "  make test-integration Run integration tests (requires MQTT broker)"
	@echo "  make test-all         Run all tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with black"
	@echo "  make type-check       Run type checking with mypy"
	@echo "  make quality          Run all quality checks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-test      Run tests in Docker with MQTT broker"
	@echo "  make docker-up        Start MQTT broker for local testing"
	@echo "  make docker-down      Stop MQTT broker"
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
	pytest tests/ -k "not integration"

test-integration:
	@echo "Running integration tests (requires MQTT broker on localhost:1883)"
	pytest tests/integration/ -v
test-all:
	pytest tests/ -v

test-cov:
	pytest --cov=src/bely_mqtt --cov-report=html --cov-report=term-missing --cov-report=xml

# Docker commands for testing
docker-up:
	@echo "Starting MQTT broker for testing..."
	docker run -d --name mqtt-test-broker -p 1883:1883 eclipse-mosquitto:2

docker-down:
	@echo "Stopping MQTT broker..."
	docker stop mqtt-test-broker || true
	docker rm mqtt-test-broker || true

docker-test: docker-down docker-up
	@echo "Waiting for MQTT broker to start..."
	@sleep 3
	@make test-integration
	@make docker-down

lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/bely_mqtt

quality: lint type-check test

# CI/CD specific commands
ci-test:
	@echo "Running CI tests..."
	pytest tests/ -v --tb=short --junitxml=test-results.xml

ci-integration:
	@echo "Running CI integration tests..."
	MQTT_BROKER_HOST=localhost MQTT_BROKER_PORT=1883 pytest tests/integration/ -v --tb=short

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

