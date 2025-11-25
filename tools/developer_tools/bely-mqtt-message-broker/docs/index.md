# BELY MQTT Framework Documentation

Welcome to the BELY MQTT Framework documentation. This framework helps you build event-driven integrations with BELY (Best Electronic Logbook Yet).

## Quick Links

- [Getting Started](getting-started.md) - Create your first handler in 5 minutes
- [API Reference](api-reference.md) - Complete API documentation
- [Examples](examples.md) - Real-world handler examples
- [Configuration](configuration.md) - Configure the framework
- [FAQ](faq.md) - Frequently asked questions
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## What is BELY MQTT Framework?

The BELY MQTT Framework is a pluggable Python framework for handling MQTT events from BELY. It provides:

- **Easy Handler Development** - Simple Python classes for event handling
- **Flexible Topic Matching** - Support for MQTT wildcards
- **Built-in Models** - Pydantic models for all BELY events
- **API Integration** - Optional BELY API client
- **Production Ready** - Logging, error handling, and systemd support

## Installation

```bash
pip install bely-mqtt-framework
```

## Basic Example

```python
from bely_mqtt import MQTTHandler, MQTTMessage

class LogHandler(MQTTHandler):
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Add"
    
    async def handle(self, message: MQTTMessage) -> None:
        self.logger.info(f"New entry: {message.payload['description']}")
```

## Architecture

The framework consists of:

1. **Core Framework** - MQTT client and plugin manager
2. **Handler System** - Pluggable handlers for different events
3. **Data Models** - Pydantic models for type safety
4. **CLI Interface** - Command-line tools for running the framework

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/bely-org/bely-mqtt-framework/issues)
- Documentation: [Full documentation](https://github.com/bely-org/bely-mqtt-framework/tree/main/docs)
- Examples: [Example handlers](https://github.com/bely-org/bely-mqtt-framework/tree/main/examples)