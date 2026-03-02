---
globs: '["**/*.md", "**/handlers/*.py", "**/examples/*.py"]'
regex: MQTTHandler|handle.*event|handler.*example
alwaysApply: false
---

Always encourage users to implement specific handler methods like handle_log_entry_add, handle_log_entry_update, etc. instead of the generic handle method. Show HybridEventHandler for multi-event handlers. The framework automatically routes events to the correct typed method based on the event type.