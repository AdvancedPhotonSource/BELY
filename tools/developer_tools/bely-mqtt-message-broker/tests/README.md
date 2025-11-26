# BELY MQTT Message Broker - Testing Guide

## Overview

This directory contains the test suite for the BELY MQTT Message Broker, including unit tests and integration tests.

## Test Structure

```
tests/
├── test_models.py          # Unit tests for data models
├── test_plugin.py          # Unit tests for plugin system
├── integration/            # Integration tests
│   ├── __init__.py
│   └── test_mqtt_integration.py
├── mosquitto.conf          # MQTT broker configuration for testing
├── Dockerfile.test         # Docker image for test environment
└── README.md              # This file
```

## Running Tests

### Quick Start

```bash
# Run all unit tests
make test

# Run integration tests (requires MQTT broker)
make test-integration

# Run all tests with coverage
make test-cov

# Run tests in Docker environment
make docker-test
```

### Using the Test Script

```bash
# Run unit tests only
./scripts/run_tests.sh --unit

# Run integration tests only
./scripts/run_tests.sh --integration

# Run all tests with coverage
./scripts/run_tests.sh --all --coverage

# Run tests in Docker (no local dependencies needed)
./scripts/run_tests.sh --all --docker
```

### Manual Test Execution

```bash
# Unit tests only
pytest tests/ -k "not integration"

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/test_models.py

# With coverage
pytest --cov=src/bely_mqtt --cov-report=html
```

## GitHub Actions CI/CD

Tests are automatically run on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

The CI pipeline includes:
- Multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Unit tests
- Integration tests with real MQTT broker
- Code coverage reporting
- Code quality checks (linting, formatting, type checking)

### CI Workflow

```yaml
# Located at .github/workflows/test.yml
name: Test BELY MQTT Message Broker

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

## Local Development Testing

### Prerequisites

1. **Python 3.9+**
   ```bash
   python --version
   ```

2. **Development dependencies**
   ```bash
   make install-dev
   ```

3. **MQTT Broker** (for integration tests)
   
   Option A: Use Docker
   ```bash
   docker run -d -p 1883:1883 eclipse-mosquitto:2
   ```
   
   Option B: Install locally
   ```bash
   # macOS
   brew install mosquitto
   brew services start mosquitto
   
   # Ubuntu/Debian
   sudo apt-get install mosquitto
   sudo systemctl start mosquitto
   ```

### Docker-based Testing

For a completely isolated test environment:

```bash
# Using docker-compose
docker-compose -f docker-compose.test.yml up --build

# Using Make
make docker-test

# Manual Docker commands
docker build -f tests/Dockerfile.test -t bely-mqtt-test .
docker run --rm bely-mqtt-test
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation:

- **test_models.py**: Tests for event models and data parsing
  - CoreEvent parsing
  - LogEntryAddEvent parsing
  - Field aliasing and validation
  - Timestamp parsing

- **test_plugin.py**: Tests for plugin system
  - Handler registration
  - Topic pattern matching
  - Message routing
  - Wildcard support

### Integration Tests

Integration tests verify the system with a real MQTT broker:

- **test_mqtt_integration.py**: End-to-end MQTT functionality
  - Connection establishment
  - Publishing and subscribing
  - Message delivery guarantees (QoS)
  - Retained messages
  - Handler message processing
  - Error handling

## Writing New Tests

### Unit Test Template

```python
# tests/test_new_feature.py
import pytest
from bely_mqtt.new_feature import NewFeature

class TestNewFeature:
    def test_basic_functionality(self):
        feature = NewFeature()
        assert feature.do_something() == expected_result
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        feature = NewFeature()
        result = await feature.async_method()
        assert result == expected_result
```

### Integration Test Template

```python
# tests/integration/test_new_integration.py
import pytest
import pytest_asyncio
from aiomqtt import Client

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mqtt_feature(mqtt_client):
    """Test new MQTT feature."""
    # Your test code here
    await mqtt_client.publish("test/topic", payload=b"test")
    # Assertions
```

## Test Configuration

### pytest.ini

Configuration for pytest is in `pytest.ini`:
- Test discovery patterns
- Async test support
- Coverage settings
- Test markers

### Environment Variables

For integration tests:
- `MQTT_BROKER_HOST`: MQTT broker hostname (default: localhost)
- `MQTT_BROKER_PORT`: MQTT broker port (default: 1883)

## Troubleshooting

### Common Issues

1. **Integration tests failing: "MQTT broker not available"**
   - Ensure MQTT broker is running: `docker run -d -p 1883:1883 eclipse-mosquitto:2`
   - Check port 1883 is not in use: `lsof -i :1883`

2. **Import errors**
   - Install package in development mode: `make install-dev`
   - Verify Python path: `echo $PYTHONPATH`

3. **Async test warnings**
   - Ensure `pytest-asyncio` is installed
   - Check `asyncio_mode = auto` in pytest.ini

4. **Coverage not generated**
   - Install coverage tools: `pip install pytest-cov`
   - Run with coverage flag: `pytest --cov=src/bely_mqtt`

## Continuous Integration

### GitHub Actions Status

Tests run automatically on:
- Every push to protected branches
- All pull requests
- Manual workflow dispatch

Check test status:
- Go to Actions tab in GitHub repository
- View "Test BELY MQTT Message Broker" workflow
- Check test results and coverage reports

### Local CI Simulation

To simulate CI environment locally:

```bash
# Run exactly as CI does
act -j test

# Or use Docker
docker-compose -f docker-compose.test.yml up --build
```

## Coverage Reports

After running tests with coverage:

- **HTML Report**: `htmlcov/index.html`
- **Terminal Report**: Shown after test run
- **XML Report**: `coverage.xml` (for CI tools)

View HTML coverage report:
```bash
make test-cov
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Contributing

When adding new features:
1. Write unit tests for new components
2. Add integration tests for MQTT interactions
3. Ensure all tests pass locally
4. Check coverage doesn't decrease
5. Update this README if needed

## Support

For test-related issues:
1. Check this README
2. Review existing test examples
3. Check GitHub Actions logs
4. Open an issue with test output