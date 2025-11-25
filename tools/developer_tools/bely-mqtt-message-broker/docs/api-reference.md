# API Reference

## Core Classes

### MQTTHandler

Base class for all MQTT event handlers.

```python
from bely_mqtt import MQTTHandler, LogEntryAddEvent

class MyHandler(MQTTHandler):
    @property
    def topic_pattern(self) -> str:
        """MQTT topic pattern to match."""
        return "bely/logEntry/Add"
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        """Handle new log entry event."""
        pass
```

**Properties:**
- `logger` - Pre-configured logger instance
- `api_client` - Optional BELY API client (if configured)

**Event Handler Methods:**
- `handle_log_entry_add(event: LogEntryAddEvent)` - New log entries
- `handle_log_entry_update(event: LogEntryUpdateEvent)` - Updated entries
- `handle_log_entry_reply_add(event: LogEntryReplyAddEvent)` - New replies
- `handle_log_entry_reply_update(event: LogEntryReplyUpdateEvent)` - Updated replies
- `handle_log_reaction_add(event: LogReactionAddEvent)` - New reactions
- `handle_log_reaction_delete(event: LogReactionDeleteEvent)` - Deleted reactions

**Utility Methods:**
- `topic_matches(topic: str) -> bool` - Check if topic matches pattern

### HybridEventHandler

Handler that can process multiple event types with specific methods.

```python
from bely_mqtt import HybridEventHandler, LogEntryAddEvent, LogEntryUpdateEvent

class MultiHandler(HybridEventHandler):
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/+"  # Matches Add, Update, Delete
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        self.logger.info(f"New entry: {event.description}")
    
    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        self.logger.info(f"Updated entry: {event.log_info.id}")
```

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

# Event is automatically parsed from message payload
async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
    print(f"Entry ID: {event.log_info.id}")
    print(f"Document: {event.parent_log_document_info.name}")
    print(f"Added by: {event.event_triggered_by_username}")
    print(f"Description: {event.description}")
```

### LogEntryUpdateEvent

```python
from bely_mqtt import LogEntryUpdateEvent

async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
    print(f"Updated entry: {event.log_info.id}")
    print(f"Text diff: {event.text_diff}")
```

### LogEntryReplyAddEvent

```python
from bely_mqtt import LogEntryReplyAddEvent

async def handle_log_entry_reply_add(self, event: LogEntryReplyAddEvent) -> None:
    print(f"Reply to entry: {event.parent_log_info.id}")
    print(f"Reply ID: {event.log_info.id}")
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


