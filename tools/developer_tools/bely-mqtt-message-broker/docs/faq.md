# Frequently Asked Questions

## General Questions

### What is BELY MQTT Framework?

It's a Python framework that makes it easy to handle MQTT events from BELY (Best Electronic Logbook Yet). You write handlers that react to specific events like log entries being added or updated.

### What Python versions are supported?

Python 3.9, 3.10, 3.11, and 3.12 are supported.

### Do I need to know MQTT?

Basic understanding helps, but the framework handles most MQTT details for you. You just need to know about topics (like `bely/logEntry/Add`).

## Handler Development

### How do I handle multiple event types?

Use wildcards in your topic pattern and implement specific handler methods:

```python
from bely_mqtt import HybridEventHandler, LogEntryAddEvent, LogEntryUpdateEvent

class MultiHandler(HybridEventHandler):
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/+"  # Handles Add, Update, Delete
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        # Handle new entries
        pass
    
    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        # Handle updates
        pass
```

### Can I use the BELY API in handlers?

Yes! Configure the API when starting:

```bash
bely-mqtt start --api-url https://api.bely.dev --api-key YOUR_KEY
```

Then use `self.api_client` in your handler.

### How do I test my handlers?

```python
import pytest
from bely_mqtt import LogEntryAddEvent
from my_handler import MyHandler

@pytest.mark.asyncio
async def test_handler():
    handler = MyHandler()
    event = LogEntryAddEvent(
        description="Test entry",
        event_timestamp="2024-01-01T00:00:00Z",
        entity_name="Log",
        entity_id=1,
        event_triggered_by_username="testuser",
        parent_log_document_info={"name": "Test Doc", "id": 1},
        log_info={"id": 1},
        logbook_list=[],
        text_diff="+ Test entry"
    )
    await handler.handle_log_entry_add(event)
```

## Troubleshooting

### Handler not being called

1. Check the topic pattern matches the MQTT topic
2. Verify the handler file is in the handlers directory
3. Check logs for errors: `--log-level DEBUG`

### Connection refused

1. Check MQTT broker is running
2. Verify host and port are correct
3. Check username/password if required

### Import errors

Make sure the framework is installed:

```bash
pip install bely-mqtt-framework
```

## Performance

### How many handlers can I run?

The framework can handle hundreds of handlers. Each handler runs asynchronously, so they don't block each other.

### Can I run multiple instances?

By default, no. The framework uses a file lock (`/tmp/bely-mqtt.lock`) to enforce single-instance operation and prevent duplicate message processing. If you attempt to start a second instance, it will exit with an error.

If you need multiple instances (e.g., subscribing to different topics with separate handler sets), specify a different lock file for each:

```bash
# Instance 1
bely-mqtt start --lock-file /tmp/bely-mqtt-1.lock -t "bely/logEntry/#"

# Instance 2
bely-mqtt start --lock-file /tmp/bely-mqtt-2.lock -t "bely/logbook/#"
```

You can also set the lock file path via the `BELY_LOCK_FILE` environment variable.

### Is it production ready?

Yes! The framework includes:
- Error handling and recovery
- Logging
- Systemd service support
- Async processing