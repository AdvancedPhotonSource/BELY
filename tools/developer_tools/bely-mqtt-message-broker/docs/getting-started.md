# Getting Started

This guide will help you create your first MQTT handler for BELY events.

## Installation

```bash
pip install bely-mqtt-framework
```

## Your First Handler

Create a file `handlers/my_first_handler.py`:

```python
from bely_mqtt import MQTTHandler, MQTTMessage

class MyFirstHandler(MQTTHandler):
    """Logs when new entries are added."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Add"
    
    async def handle(self, message: MQTTMessage) -> None:
        self.logger.info(f"New log entry: {message.payload['description']}")
```

## Running the Framework

```bash
# Start with your handler
bely-mqtt start --handlers-dir ./handlers

# With custom MQTT broker
bely-mqtt start \
    --handlers-dir ./handlers \
    --mqtt-host broker.example.com \
    --mqtt-port 1883
```

## What's Next?

- [Handler Development](handler-development.md) - Learn about advanced handler features
- [Configuration](configuration.md) - Configure MQTT, logging, and more
- [Examples](examples.md) - See more handler examples