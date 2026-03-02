# Getting Started

This guide will help you create your first MQTT handler for BELY events.

## Installation

```bash
pip install bely-mqtt-framework
```

## Your First Handler

Create a file `handlers/my_first_handler.py`:

```python
from bely_mqtt import MQTTHandler, LogEntryAddEvent

class MyFirstHandler(MQTTHandler):
    """Logs when new entries are added."""
    
    # By default, handlers subscribe to all BELY topics (bely/#)
    # The framework automatically routes events to the appropriate handler methods
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        self.logger.info(f"New log entry: {event.description}")
        self.logger.info(f"Added by: {event.event_triggered_by_username}")
```

### Subscribing to Specific Topics

If you want to limit your handler to specific topics only (for performance or clarity), override the `topic_pattern` property:

```python
class SpecificTopicHandler(MQTTHandler):
    """Only handles log entry events."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/#"  # Only log entry events
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        # Handle new entries
        pass
    
    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        # Handle updates
        pass
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

## Handler Methods

The framework automatically calls the appropriate method based on the event type:

- `handle_log_entry_add(event: LogEntryAddEvent)` - New log entries
- `handle_log_entry_update(event: LogEntryUpdateEvent)` - Updated entries
- `handle_log_entry_reply_add(event: LogEntryReplyAddEvent)` - New replies
- `handle_log_reaction_add(event: LogReactionAddEvent)` - New reactions

## What's Next?

- [API Reference](api-reference.md) - Complete API documentation
- [Examples](examples.md) - More handler examples
- [FAQ](faq.md) - Common questions and answers
- [Troubleshooting](troubleshooting.md) - Solve common issues

