"""
Plugin system for BELY MQTT handlers.

This module provides the base classes and interfaces for creating
pluggable handlers for MQTT topics.
"""

import importlib
import importlib.util
import inspect
import logging
from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from bely_mqtt.config import GlobalConfig
from bely_mqtt.events import EventType
from bely_mqtt.models import MQTTMessage

try:
    from BelyApiFactory import BelyApiFactory
except ImportError:
    BelyApiFactory = None  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


class MQTTHandler(ABC):
    """
    Base class for MQTT message handlers.

    Subclass this to create handlers for specific MQTT topics or event types.
    By default, handlers subscribe to all BELY topics (bely/#). Override the
    topic_pattern property to subscribe to specific topics only.

    Handlers can implement either:
    1. The generic `handle()` method for all messages
    2. Specific event handler methods like `handle_log_entry_add()`, `handle_generic_update()`, etc.
    3. Both (specific handlers are called first, then generic handle if not overridden)

    Supported specific event handlers:
        - handle_generic_add(event: CoreEvent) - Generic add events (bely/add)
        - handle_generic_update(event: CoreEvent) - Generic update events (bely/update)
        - handle_generic_delete(event: CoreEvent) - Generic delete events (bely/delete)
        - handle_log_entry_add(event: LogEntryAddEvent) - Log entry added (bely/logEntry/Add)
        - handle_log_entry_update(event: LogEntryUpdateEvent) - Log entry updated (bely/logEntry/Update)
        - handle_log_entry_delete(event: LogEntryDeleteEvent) - Log entry deleted (bely/logEntry/Delete)
        - handle_log_entry_reply_add(event: LogEntryReplyAddEvent) - Reply added (bely/logEntryReply/Add)
        - handle_log_entry_reply_update(event: LogEntryReplyUpdateEvent) - Reply updated (bely/logEntryReply/Update)
        - handle_log_entry_reply_delete(event: LogEntryReplyDeleteEvent) - Reply deleted (bely/logEntryReply/Delete)
        - handle_log_reaction_add(event: LogReactionAddEvent) - Reaction added (bely/logReaction/Add)
        - handle_log_reaction_delete(event: LogReactionDeleteEvent) - Reaction deleted (bely/logReaction/Delete)

    Example:
        class MyHandler(MQTTHandler):
            # Uses default topic_pattern "bely/#" - receives all BELY events

            async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
                # Only called for bely/logEntry/Add events
                # event is already parsed and typed
                self.logger.info(f"New entry: {event.log_info.id}")

            async def handle_generic_update(self, event: CoreEvent) -> None:
                # Only called for bely/update events
                self.logger.info(f"Updated: {event.entity_name}")

        class SpecificHandler(MQTTHandler):
            @property
            def topic_pattern(self) -> str:
                # Override to subscribe to specific topics only
                return "bely/logEntry/#"

            async def handle(self, message: MQTTMessage) -> None:
                # Handle only log entry related events
                pass
    """

    def __init__(
        self,
        api_factory=None,
        global_config: Optional[GlobalConfig] = None,
    ):
        """
        Initialize the handler.

        Args:
            api_factory: Optional BelyApiFactory instance for querying the BELY API.
            global_config: Optional global configuration shared across all handlers.
        """
        self.api_factory = api_factory
        self.global_config = global_config
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def topic_pattern(self) -> str:
        """
        Return the MQTT topic pattern this handler subscribes to.

        By default, handlers subscribe to all BELY topics (bely/#).
        Override this property to subscribe to specific topics only.

        Examples:
            - "bely/#" - matches all BELY topics (default)
            - "bely/add" - matches exact topic
            - "bely/logEntry/#" - matches all log entry subtopics
            - "bely/+/Add" - matches single level wildcard

        Returns:
            MQTT topic pattern string.
        """
        return "bely/#"

    async def handle(self, message: MQTTMessage) -> None:
        """
        Handle an MQTT message.

        This method is called for all messages matching the topic pattern.
        Override this method to handle all messages, or implement specific
        event handler methods (handle_log_entry_add, etc.) for specific events.

        Args:
            message: The MQTT message to handle.

        Raises:
            Exception: Any exception raised will be logged but not propagated.
        """
        # Try to route to specific event handler
        event_type = EventType.from_topic(message.topic)
        if event_type:
            handler_method_name = event_type.handler_method_name
            if hasattr(self, handler_method_name):
                handler_method = getattr(self, handler_method_name)
                if callable(handler_method):
                    # Parse the message payload into the appropriate event type
                    event = self._parse_event(event_type, message)
                    await handler_method(event)
                    return

        # If no specific handler found, call the generic handler
        await self.handle_generic(message)

    async def handle_generic(self, message: MQTTMessage) -> None:
        """
        Generic handler for messages that don't match specific event types.

        Override this method to handle messages that don't match any specific
        event type, or implement specific event handler methods.

        Args:
            message: The MQTT message to handle.
        """
        # Default implementation does nothing
        # Subclasses can override to provide custom behavior
        pass

    @staticmethod
    def _parse_event(event_type: EventType, message: MQTTMessage) -> Any:
        """
        Parse an MQTT message into the appropriate event type.

        Args:
            event_type: The EventType to parse into.
            message: The MQTT message to parse.

        Returns:
            Parsed event object of the appropriate type.

        Raises:
            ValueError: If the event type is not recognized.
        """
        # Import here to avoid circular imports
        from bely_mqtt.models import (
            CoreEvent,
            LogEntryAddEvent,
            LogEntryUpdateEvent,
            LogEntryDeleteEvent,
            LogEntryReplyAddEvent,
            LogEntryReplyUpdateEvent,
            LogEntryReplyDeleteEvent,
            LogReactionAddEvent,
            LogReactionDeleteEvent,
            TestNotificationEvent,
        )

        event_type_map = {
            EventType.GENERIC_ADD: CoreEvent,
            EventType.GENERIC_UPDATE: CoreEvent,
            EventType.GENERIC_DELETE: CoreEvent,
            EventType.LOG_ENTRY_ADD: LogEntryAddEvent,
            EventType.LOG_ENTRY_UPDATE: LogEntryUpdateEvent,
            EventType.LOG_ENTRY_DELETE: LogEntryDeleteEvent,
            EventType.LOG_ENTRY_REPLY_ADD: LogEntryReplyAddEvent,
            EventType.LOG_ENTRY_REPLY_UPDATE: LogEntryReplyUpdateEvent,
            EventType.LOG_ENTRY_REPLY_DELETE: LogEntryReplyDeleteEvent,
            EventType.LOG_REACTION_ADD: LogReactionAddEvent,
            EventType.LOG_REACTION_DELETE: LogReactionDeleteEvent,
            EventType.NOTIFICATION_TEST: TestNotificationEvent,
        }

        event_class = event_type_map.get(event_type)
        if not event_class:
            raise ValueError(f"Unknown event type: {event_type}")

        return event_class(**message.payload)

    def topic_matches(self, topic: str) -> bool:
        """
        Check if a topic matches this handler's pattern.

        Args:
            topic: The topic to check.

        Returns:
            True if the topic matches the pattern, False otherwise.
        """
        return self._match_mqtt_pattern(self.topic_pattern, topic)

    @staticmethod
    def _match_mqtt_pattern(pattern: str, topic: str) -> bool:
        """
        Match an MQTT topic against a pattern.

        Supports:
            - # (multi-level wildcard, must be at end)
            - + (single-level wildcard)
            - exact matches

        Args:
            pattern: The MQTT pattern.
            topic: The topic to match.

        Returns:
            True if the topic matches the pattern.
        """
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")

        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == "#":
                # Multi-level wildcard matches everything remaining
                return True
            elif pattern_part == "+":
                # Single-level wildcard matches one level
                if i >= len(topic_parts):
                    return False
            else:
                # Exact match required
                if i >= len(topic_parts) or topic_parts[i] != pattern_part:
                    return False

        # Check if we've consumed all topic parts
        return len(topic_parts) == len(pattern_parts)


class PluginManager:
    """
    Manages loading and executing MQTT handlers.

    Supports passing both global and handler-specific configuration to handlers
    during instantiation.
    """

    def __init__(
        self,
        api_factory=None,
        config_manager: Optional[Any] = None,
    ):
        """
        Initialize the plugin manager.

        Args:
            api_factory: Optional BelyApiFactory instance to pass to handlers.
            config_manager: Optional ConfigManager for handler configuration.
        """
        self.api_factory = api_factory
        self.config_manager = config_manager
        self.handlers: List[MQTTHandler] = []
        self.logger = logging.getLogger(__name__)

    def register_handler(self, handler: MQTTHandler) -> None:
        """
        Register a handler.

        Args:
            handler: The handler instance to register.
        """
        self.handlers.append(handler)
        self.logger.info(
            f"Registered handler {handler.__class__.__name__} "
            f"for topic pattern: {handler.topic_pattern}"
        )

    def register_handler_class(self, handler_class: Type[MQTTHandler]) -> None:
        """
        Register a handler by class.

        Attempts to pass both global configuration and handler-specific
        configuration to the handler if available.

        Args:
            handler_class: The handler class to instantiate and register.
        """
        handler_name = handler_class.__name__

        # Get global configuration if available
        global_config = None
        if self.config_manager:
            global_config = self.config_manager.get_global_config()

        # Try to get handler-specific configuration
        handler_config = None
        if self.config_manager:
            handler_config = self.config_manager.get_config(handler_name)

        # Prepare constructor arguments
        constructor_args = {
            "api_factory": self.api_factory,
        }

        # Add global_config if the handler accepts it
        if global_config:
            constructor_args["global_config"] = global_config

        # Add handler-specific configuration if available
        if handler_config and handler_config.config:
            constructor_args.update(handler_config.config)

        # Instantiate handler with configuration
        try:
            # First try with all arguments
            handler = handler_class(**constructor_args)  # type: ignore[arg-type]
            if global_config:
                self.logger.debug(f"Instantiated {handler_name} with global configuration")
            if handler_config:
                self.logger.debug(
                    f"Instantiated {handler_name} with handler configuration: {handler_config.config}"
                )
        except TypeError as e:
            # Handler might not accept all parameters, try with just what it accepts
            self.logger.debug(
                f"Handler {handler_name} does not accept all configuration parameters: {e}"
            )

            # Get the handler's __init__ signature
            import inspect

            sig = inspect.signature(handler_class.__init__)
            accepted_params = set(sig.parameters.keys()) - {"self"}

            # Filter constructor args to only what the handler accepts
            filtered_args = {k: v for k, v in constructor_args.items() if k in accepted_params}

            try:
                handler = handler_class(**filtered_args)  # type: ignore[arg-type]
                self.logger.debug(
                    f"Instantiated {handler_name} with filtered parameters: {filtered_args.keys()}"
                )
            except Exception as e2:
                # Fall back to minimal instantiation
                self.logger.warning(
                    f"Failed to instantiate {handler_name} with configuration, "
                    f"falling back to minimal instantiation: {e2}"
                )
                handler = handler_class()

        self.register_handler(handler)

    def load_handlers_from_directory(self, directory: Path) -> None:
        """
        Dynamically load handlers from a directory.

        Looks for Python files and packages in the directory and imports any classes
        that inherit from MQTTHandler.

        Supports:
        - Single Python files (*.py)
        - Python packages (directories with __init__.py)

        Args:
            directory: Path to the directory containing handler modules.
        """
        directory = Path(directory)
        if not directory.exists():
            self.logger.warning(f"Handler directory does not exist: {directory}")
            return

        # Load handlers from Python files
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find all MQTTHandler subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, MQTTHandler)
                        and obj is not MQTTHandler
                    ):
                        self.register_handler_class(obj)
                        self.logger.info(f"Loaded handler from {py_file}: {name}")

            except Exception as e:
                self.logger.error(f"Failed to load handlers from {py_file}: {e}")

        # Load handlers from Python packages (directories with __init__.py)
        for item in directory.iterdir():
            if not item.is_dir() or item.name.startswith("_") or item.name.startswith("."):
                continue

            init_file = item / "__init__.py"
            if not init_file.exists():
                continue

            module_name = item.name
            try:
                # Add parent directory to sys.path temporarily
                import sys

                old_path = sys.path.copy()
                sys.path.insert(0, str(directory))

                try:
                    # Import the package
                    module = importlib.import_module(module_name)

                    # Find all MQTTHandler subclasses in the package
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, MQTTHandler)
                            and obj is not MQTTHandler
                        ):
                            self.register_handler_class(obj)
                            self.logger.info(f"Loaded handler from package {item}: {name}")

                finally:
                    # Restore original sys.path
                    sys.path = old_path

            except Exception as e:
                self.logger.error(f"Failed to load handlers from package {item}: {e}")

    async def handle_message(self, message: MQTTMessage) -> None:
        """
        Route a message to all matching handlers.

        For each matching handler, attempts to route to a specific event handler
        method (e.g., handle_log_entry_add) if available, otherwise calls the
        generic handle() method.

        Specific event handlers receive parsed event objects (e.g., LogEntryAddEvent)
        instead of raw MQTT messages.

        Args:
            message: The MQTT message to handle.
        """
        matching_handlers = [h for h in self.handlers if h.topic_matches(message.topic)]

        if not matching_handlers:
            self.logger.debug(f"No handlers found for topic: {message.topic}")
            return

        # Get event type for this topic
        event_type = EventType.from_topic(message.topic)

        for handler in matching_handlers:
            try:
                # Try to route to specific event handler
                if event_type:
                    handler_method_name = event_type.handler_method_name
                    if hasattr(handler, handler_method_name):
                        handler_method = getattr(handler, handler_method_name)
                        if callable(handler_method):
                            self.logger.debug(
                                f"Routing {message.topic} to "
                                f"{handler.__class__.__name__}.{handler_method_name}"
                            )
                            # Parse message into typed event object
                            event = MQTTHandler._parse_event(event_type, message)
                            await handler_method(event)
                            continue

                # Fall back to generic handle method
                self.logger.debug(
                    f"Routing {message.topic} to " f"{handler.__class__.__name__}.handle"
                )
                await handler.handle(message)
            except Exception as e:
                self.logger.error(
                    f"Error in handler {handler.__class__.__name__}: {e}",
                    exc_info=True,
                )

    def get_handlers_for_topic(self, topic: str) -> List[MQTTHandler]:
        """
        Get all handlers that match a topic.

        Args:
            topic: The MQTT topic.

        Returns:
            List of matching handlers.
        """
        return [h for h in self.handlers if h.topic_matches(topic)]
