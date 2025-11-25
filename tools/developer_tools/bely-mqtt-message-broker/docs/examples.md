# Examples

## Basic Examples

### Simple Log Entry Handler

```python
from bely_mqtt import MQTTHandler, LogEntryAddEvent

class SimpleHandler(MQTTHandler):
    """Log new entries to console."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Add"
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        self.logger.info(f"New entry: {event.description}")
```

### Multi-Event Handler

```python
from bely_mqtt import HybridEventHandler, LogEntryAddEvent, LogEntryUpdateEvent

class LogMonitor(HybridEventHandler):
    """Monitor all log entry changes."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/+"  # Matches Add, Update, Delete
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        self.logger.info(f"NEW: {event.description[:50]}...")
    
    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        self.logger.info(f"UPDATED: Entry {event.log_info.id}")
```

## Advanced Examples

### API Integration

```python
from bely_mqtt import MQTTHandler, LogEntryUpdateEvent

class EnrichedHandler(MQTTHandler):
    """Enrich events with API data."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Update"
    
    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        if self.api_client:
            # Get full entry details
            entry = await self.api_client.get_log_entry(event.log_info.id)
            self.logger.info(f"Full entry data: {entry}")
```

### Notification Handler

```python
from bely_mqtt import MQTTHandler, LogEntryReplyAddEvent
import aiohttp

class NotificationHandler(MQTTHandler):
    """Send notifications for replies."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntryReply/Add"
    
    async def handle_log_entry_reply_add(self, event: LogEntryReplyAddEvent) -> None:
        # Don't notify about self-replies
        if event.event_triggered_by_username == event.parent_log_info.entered_by_username:
            return
        
        message = f"New reply from {event.event_triggered_by_username}"
        await self.send_slack_notification(message)
    
    async def send_slack_notification(self, message: str) -> None:
        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK"
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"text": message})
```

### Reaction Tracker

```python
from bely_mqtt import MQTTHandler, LogReactionAddEvent, LogReactionDeleteEvent
from collections import defaultdict

class ReactionTracker(MQTTHandler):
    """Track reactions on log entries."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reaction_counts = defaultdict(lambda: defaultdict(int))
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logReaction/+"
    
    async def handle_log_reaction_add(self, event: LogReactionAddEvent) -> None:
        log_id = event.parent_log_info.id
        emoji = event.log_reaction.reaction.emoji
        self.reaction_counts[log_id][emoji] += 1
        
        self.logger.info(f"Reaction {emoji} added to entry {log_id}")
    
    async def handle_log_reaction_delete(self, event: LogReactionDeleteEvent) -> None:
        log_id = event.parent_log_info.id
        emoji = event.log_reaction.reaction.emoji
        if self.reaction_counts[log_id][emoji] > 0:
            self.reaction_counts[log_id][emoji] -= 1
```

### Error Handling Example

```python
from bely_mqtt import MQTTHandler, LogEntryAddEvent
import asyncio

class RobustHandler(MQTTHandler):
    """Handler with comprehensive error handling."""
    
    @property
    def topic_pattern(self) -> str:
        return "bely/logEntry/Add"
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        try:
            # Process with timeout
            await asyncio.wait_for(
                self.process_entry(event),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout processing entry {event.log_info.id}")
        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
    
    async def process_entry(self, event: LogEntryAddEvent) -> None:
        # Your processing logic here
        await asyncio.sleep(1)
        self.logger.info(f"Processed entry {event.log_info.id}")
```

## Running the Examples

1. Create a `handlers` directory
2. Copy example code to Python files in the directory
3. Run the framework:

```bash
# Basic
bely-mqtt start --handlers-dir ./handlers

# With API integration
bely-mqtt start \
    --handlers-dir ./handlers \
    --api-url https://api.bely.dev \
    --api-key your-api-key

# With debug logging
bely-mqtt start \
    --handlers-dir ./handlers \
    --log-level DEBUG
```

## Testing Examples

```python
import pytest
from bely_mqtt import LogEntryAddEvent
from handlers.simple_handler import SimpleHandler

@pytest.mark.asyncio
async def test_simple_handler(caplog):
    handler = SimpleHandler()
    
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
    
    assert "New entry: Test entry" in caplog.text
```