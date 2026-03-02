"""
Event type enumeration for BELY MQTT events.

This module defines all supported event types and provides utilities
for working with them.
"""

from enum import Enum
from typing import Optional


class EventType(Enum):
    """
    Enumeration of all supported BELY event types.

    Each event type corresponds to a specific MQTT topic pattern.

    Generic Events:
        GENERIC_ADD - Generic add event (bely/add)
        GENERIC_UPDATE - Generic update event (bely/update)
        GENERIC_DELETE - Generic delete event (bely/delete)

    Log Entry Events:
        LOG_ENTRY_ADD - Log entry added (bely/logEntry/Add)
        LOG_ENTRY_UPDATE - Log entry updated (bely/logEntry/Update)
        LOG_ENTRY_DELETE - Log entry deleted (bely/logEntry/Delete)

    Log Entry Reply Events:
        LOG_ENTRY_REPLY_ADD - Reply added (bely/logEntryReply/Add)
        LOG_ENTRY_REPLY_UPDATE - Reply updated (bely/logEntryReply/Update)
        LOG_ENTRY_REPLY_DELETE - Reply deleted (bely/logEntryReply/Delete)

    Log Reaction Events:
        LOG_REACTION_ADD - Reaction added (bely/logReaction/Add)
        LOG_REACTION_DELETE - Reaction deleted (bely/logReaction/Delete)

    Search Events:
        SEARCH - Search performed (bely/search)

    Notification Events:
        NOTIFICATION_TEST - Test notification (bely/notification/test)
    """

    # Generic events
    GENERIC_ADD = "bely/add"
    GENERIC_UPDATE = "bely/update"
    GENERIC_DELETE = "bely/delete"

    # Log entry events
    LOG_ENTRY_ADD = "bely/logEntry/Add"
    LOG_ENTRY_UPDATE = "bely/logEntry/Update"
    LOG_ENTRY_DELETE = "bely/logEntry/Delete"

    # Log entry reply events
    LOG_ENTRY_REPLY_ADD = "bely/logEntryReply/Add"
    LOG_ENTRY_REPLY_UPDATE = "bely/logEntryReply/Update"
    LOG_ENTRY_REPLY_DELETE = "bely/logEntryReply/Delete"

    # Log reaction events
    LOG_REACTION_ADD = "bely/logReaction/Add"
    LOG_REACTION_DELETE = "bely/logReaction/Delete"

    # Search events
    SEARCH = "bely/search"

    # Notification events
    NOTIFICATION_TEST = "bely/notification/test"

    def __str__(self) -> str:
        """Return the topic pattern for this event type."""
        return self.value

    @classmethod
    def from_topic(cls, topic: str) -> Optional["EventType"]:
        """
        Get EventType from MQTT topic.

        Args:
            topic: MQTT topic string (e.g., "bely/logEntry/Add")

        Returns:
            EventType if topic matches, None otherwise.

        Examples:
            >>> EventType.from_topic("bely/logEntry/Add")
            <EventType.LOG_ENTRY_ADD: 'bely/logEntry/Add'>

            >>> EventType.from_topic("bely/unknown")
            None
        """
        for event_type in cls:
            if event_type.value == topic:
                return event_type
        return None

    @property
    def handler_method_name(self) -> str:
        """
        Get the handler method name for this event type.

        Returns:
            Method name like "handle_log_entry_add"

        Examples:
            >>> EventType.LOG_ENTRY_ADD.handler_method_name
            'handle_log_entry_add'

            >>> EventType.GENERIC_UPDATE.handler_method_name
            'handle_generic_update'
        """
        # Convert enum name to snake_case method name
        # e.g., LOG_ENTRY_ADD -> handle_log_entry_add
        return f"handle_{self.name.lower()}"
