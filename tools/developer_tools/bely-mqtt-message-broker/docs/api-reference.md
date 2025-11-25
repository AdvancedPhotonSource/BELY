# API Reference

## Core Classes

### MQTTHandler

Base class for all MQTT event handlers.

```python
from bely_mqtt import MQTTHandler

class MyHandler(MQTTHandler):
    @property
    def topic_pattern(self) -> str:
        """MQTT topic pattern to match."""
        return "bely/logEntry/+"
    
    async def handle(self, message: MQTTMessage) -> None:
        """Handle incoming MQTT message."""
        pass
```

**Properties:**
- `logger` - Pre-configured logger instance
- `api_client` - Optional BELY API client (if configured)

**Methods:**
- `topic_matches(topic: str) -> bool` - Check if topic matches pattern
- `handle(message: MQTTMessage)` - Process incoming message (override this)

### MQTTMessage

Represents an MQTT message.

```python
from bely_mqtt import MQTTMessage

message = MQTTMessage(
    topic="bely/logEntry/Add",
    payload={"description": "Entry added"},
    raw_payload='{"description": "Entry added"}'
)
```

**Attributes:**
- `topic: str` - MQTT topic
- `payload: Dict[str, Any]` - Parsed JSON payload
- `raw_payload: str` - Original payload string

## Event Models

### LogEntryAddEvent

```python
from bely_mqtt import LogEntryAddEvent

event = LogEntryAddEvent(**message.payload)
print(f"Entry ID: {event.log_info.id}")
print(f"Added by: {event.event_triggered_by_username}")
```

### LogEntryUpdateEvent

```python
from bely_mqtt import LogEntryUpdateEvent

event = LogEntryUpdateEvent(**message.payload)
print(f"Updated entry: {event.log_info.id}")
print(f"Text diff: {event.text_diff}")
```

### LogEntryReplyAddEvent

```python
from bely_mqtt import LogEntryReplyAddEvent

event = LogEntryReplyAddEvent(**message.payload)
print(f"Reply to entry: {event.parent_log_info.id}")
```

## Topic Patterns

MQTT topic patterns support wildcards:

- `+` - Single level wildcard
- `#` - Multi-level wildcard

Examples:
- `bely/logEntry/Add` - Exact match
- `bely/logEntry/+` - Matches Add, Update, Delete
- `bely/+/Add` - Matches any entity Add events
- `bely/#` - Matches all BELY events

## CLI Commands

### start

Start the MQTT framework:

```bash
bely-mqtt start [OPTIONS]
```

**Options:**
- `--handlers-dir PATH` - Directory containing handlers
- `--mqtt-host TEXT` - MQTT broker host
- `--mqtt-port INTEGER` - MQTT broker port
- `--mqtt-username TEXT` - MQTT username
- `--mqtt-password TEXT` - MQTT password
- `--log-level TEXT` - Logging level
- `--api-url TEXT` - BELY API URL
- `--api-key TEXT` - BELY API key

### version

Show version:

```bash
bely-mqtt version
```