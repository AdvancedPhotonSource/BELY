# Migration Guide

## Migrating from Raw MQTT Client

If you're currently using a raw MQTT client (like `paho-mqtt`), here's how to migrate:

### Before (Raw MQTT)

```python
import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    if msg.topic == "bely/logEntry/Add":
        payload = json.loads(msg.payload)
        print(f"New entry: {payload['description']}")

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("bely/#")
client.loop_forever()
```

### After (BELY MQTT Framework)

```python
from bely_mqtt import MQTTHandler, LogEntryAddEvent

class LogHandler(MQTTHandler):
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Add"
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        print(f"New entry: {event.description}")
```

## Benefits of Migration

1. **Type Safety** - Pydantic models validate event data
2. **Better Organization** - Separate handlers for different events
3. **Error Handling** - Built-in error handling and logging
4. **Async Support** - Better performance with async/await
5. **API Integration** - Easy access to BELY API
6. **Testing** - Easier to unit test handlers

## Migration Steps

1. **Install the framework**
   ```bash
   pip install bely-mqtt-framework
   ```

2. **Convert callbacks to handlers**
   - Create one handler per event type
   - Move callback logic to specific handler methods (e.g., `handle_log_entry_add`)

3. **Use provided models**
   ```python
   from bely_mqtt import LogEntryAddEvent
   
   event = LogEntryAddEvent(**message.payload)
   # Now you have type-safe access to all fields
   ```

4. **Update configuration**
   - Replace connection code with CLI arguments
   - Use environment variables for secrets

5. **Test your handlers**
   ```python
   @pytest.mark.asyncio
   async def test_handler():
       handler = MyHandler()
       message = MQTTMessage(...)
       await handler.handle(message)
   ```

## Common Patterns

### Multiple Topics

**Before:**
```python
def on_message(client, userdata, msg):
    if msg.topic == "bely/logEntry/Add":
        handle_add(msg)
    elif msg.topic == "bely/logEntry/Update":
        handle_update(msg)
```

**After:**
```python
from bely_mqtt import HybridEventHandler, LogEntryAddEvent, LogEntryUpdateEvent

class MultiHandler(HybridEventHandler):
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/+"
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        # Handle add events
        pass
    
    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        # Handle update events
        pass
```

### Error Handling

**Before:**
```python
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        process_message(payload)
    except Exception as e:
        print(f"Error: {e}")
```

**After:**
```python
async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
    try:
        await self.process_event(event)
    except Exception as e:
        self.logger.error(f"Failed to process: {e}", exc_info=True)
```