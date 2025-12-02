# Apprise Smart Notification Handler

A modular BELY MQTT handler for sending smart notifications via Apprise.

## Structure

This handler is organized as a Python package with the following modules:

```
apprise_smart_notification/
├── __init__.py           # Package initialization and exports
├── handler.py            # Main handler class implementation
├── config_loader.py      # YAML configuration loading and processing
├── notification_processor.py  # Notification routing and sending logic
├── formatters.py         # Message formatting utilities
└── README.md            # This file
```

## Module Responsibilities

### handler.py
- Main `AppriseSmartNotificationHandler` class
- Event handling methods (handle_log_entry_add, etc.)
- High-level event routing logic
- Coordination between other modules

### config_loader.py
- `ConfigLoader` class for YAML file processing
- Global configuration management
- URL processing for mail server settings
- Configuration validation

### notification_processor.py
- `NotificationProcessor` class for notification management
- User notification settings management
- Apprise instance management
- Notification sending logic

### formatters.py
- `NotificationFormatter` class for message formatting
- HTML message generation
- Permalink generation
- Trigger description generation

## Usage

The handler can be used exactly the same way as before:

```python
from apprise_smart_notification import AppriseSmartNotificationHandler

handler = AppriseSmartNotificationHandler(
    config_path="/path/to/config.yaml",
    global_config=global_config
)
```

## Configuration

See the main docstring in `__init__.py` for detailed configuration documentation.

## Benefits of Modular Structure

1. **Maintainability**: Each module has a single, clear responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Reusability**: Components can be reused in other handlers
4. **Readability**: Smaller, focused files are easier to understand
5. **Extensibility**: New features can be added without modifying existing code

## Development

When adding new features:
- Event handling logic goes in `handler.py`
- Configuration features go in `config_loader.py`
- Notification logic goes in `notification_processor.py`
- Message formatting goes in `formatters.py`