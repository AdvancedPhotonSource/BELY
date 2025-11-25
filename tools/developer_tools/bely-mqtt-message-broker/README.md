# BELY MQTT Framework

A pluggable Python framework for handling MQTT events from BELY (Best Electronic Logbook Yet).

## Features

- **Pluggable Handler System** - Create custom handlers for specific MQTT topics
- **Type-Safe Models** - Pydantic models for all BELY event types
- **MQTT Topic Matching** - Support for MQTT wildcards (`+`, `#`)
- **BELY API Integration** - Query additional information from BELY API
- **CLI Interface** - Easy configuration and management via command-line
- **Async Support** - Built on async/await for high performance
- **Extensible** - Plugin system for adding custom functionality

## Quick Start

### Installation

```bash
pip install bely-mqtt-framework
```

### Create a Handler

```python
# handlers/my_handler.py
from bely_mqtt import MQTTHandler, MQTTMessage

class MyHandler(MQTTHandler):
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Add"
    
    async def handle(self, message: MQTTMessage) -> None:
        print(f"Event: {message.topic}")
```

### Run the Framework

```bash
bely-mqtt start --handlers-dir ./handlers --topic "bely/#"
```

## Documentation

- **[Getting Started](docs/getting-started.md)** - Installation and quick start
- **[Handler Development](docs/handler-development.md)** - Create custom handlers
- **[Architecture](docs/architecture.md)** - System design and components
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Configuration](docs/configuration.md)** - Configuration options
- **[Examples](docs/examples.md)** - Working examples
- **[Contributing](docs/contributing.md)** - Contributing guidelines

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Code quality
make quality
```

## License

MIT License - see LICENSE file for details

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/bely/mqtt-framework/issues)
- 💬 [Discussions](https://github.com/bely/mqtt-framework/discussions)
