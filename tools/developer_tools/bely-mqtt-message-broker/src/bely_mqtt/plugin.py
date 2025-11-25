"""
Plugin system for BELY MQTT handlers.

This module provides the base classes and interfaces for creating
pluggable handlers for MQTT topics.
"""

import importlib
import inspect
import logging
from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from bely_mqtt.events import EventType
from bely_mqtt.models import MQTTMessage

logger = logging.getLogger(__name__)


class BelyAPIClient:
    """
    Interface for BELY API client.
    
    This is a placeholder interface. The actual implementation should be
    provided by the bely-api library.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize the BELY API client."""
        self.base_url = base_url
        self.api_key = api_key

    def get_log_entry(self, log_id: int) -> Dict[str, Any]:
        """Get a log entry by ID."""
        raise NotImplementedError("Implement in actual BELY API library")

    def get_log_document(self, doc_id: int) -> Dict[str, Any]:
        """Get a log document by ID."""
        raise NotImplementedError("Implement in actual BELY API library")

    def get_user(self, username: str) -> Dict[str, Any]:
        """Get user information."""
        raise NotImplementedError("Implement in actual BELY API library")


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
        - handle_log_entry_reply_add(event: LogEntryReplyAddEvent) - Reply added (bely/logEntryReply/Add)
        - handle_log_entry_reply_update(event: LogEntryReplyUpdateEvent) - Reply updated (bely/logEntryReply/Update)
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

    def __init__(self, api_client: Optional[BelyAPIClient] = None):
        """
        Initialize the handler.
        
        Args:
            api_client: Optional BELY API client for querying additional information.
        """
        self.api_client = api_client
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
            LogEntryReplyAddEvent,
            LogEntryReplyUpdateEvent,
            LogReactionAddEvent,
            LogReactionDeleteEvent,
        )
        
        event_type_map = {
            EventType.GENERIC_ADD: CoreEvent,
            EventType.GENERIC_UPDATE: CoreEvent,
            EventType.GENERIC_DELETE: CoreEvent,
            EventType.LOG_ENTRY_ADD: LogEntryAddEvent,
            EventType.LOG_ENTRY_UPDATE: LogEntryUpdateEvent,
            EventType.LOG_ENTRY_REPLY_ADD: LogEntryReplyAddEvent,
            EventType.LOG_ENTRY_REPLY_UPDATE: LogEntryReplyUpdateEvent,
            EventType.LOG_REACTION_ADD: LogReactionAddEvent,
            EventType.LOG_REACTION_DELETE: LogReactionDeleteEvent,
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
    
    Supports passing configuration to handlers during instantiation.
    """

    def __init__(
        self,
        api_client: Optional[BelyAPIClient] = None,
        config_manager: Optional[Any] = None,
    ):
        """
        Initialize the plugin manager.
        
        Args:
            api_client: Optional BELY API client to pass to handlers.
            config_manager: Optional ConfigManager for handler configuration.
        """
        self.api_client = api_client
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
        
        Attempts to pass configuration to the handler if available.
        
        Args:
            handler_class: The handler class to instantiate and register.
        """
        handler_name = handler_class.__name__
        
        # Try to get configuration for this handler
        config = None
        if self.config_manager:
            config = self.config_manager.get_config(handler_name)
        
        # Instantiate handler with configuration if available
        try:
            if config and config.config:
                # Pass configuration to handler
                handler = handler_class(api_client=self.api_client, **config.config)
                self.logger.debug(
                    f"Instantiated {handler_name} with configuration: {config.config}"
                )
            else:
                # Instantiate without configuration
                handler = handler_class(api_client=self.api_client)
        except TypeError as e:
            # Handler doesn't accept configuration parameters
            self.logger.debug(
                f"Handler {handler_name} does not accept configuration parameters: {e}"
            )
            handler = handler_class(api_client=self.api_client)
        
        self.register_handler(handler)

    def load_handlers_from_directory(self, directory: Path) -> None:
        """
        Dynamically load handlers from a directory.
        
        Looks for Python files in the directory and imports any classes
        that inherit from MQTTHandler.
        
        Args:
            directory: Path to the directory containing handler modules.
        """
        directory = Path(directory)
        if not directory.exists():
            self.logger.warning(f"Handler directory does not exist: {directory}")
            return

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
                    f"Routing {message.topic} to "
                    f"{handler.__class__.__name__}.handle"
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
