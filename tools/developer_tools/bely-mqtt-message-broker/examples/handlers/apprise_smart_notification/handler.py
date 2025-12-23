"""
Main handler implementation for Apprise Smart Notifications.
"""

from typing import Any, Optional, Union

from bely_mqtt import (
    MQTTHandler,
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryDeleteEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
    LogEntryReplyDeleteEvent,
    LogReactionAddEvent,
    LogReactionDeleteEvent,
)
from bely_mqtt.config import GlobalConfig

try:
    # Try relative imports first (when used as a package)
    from .config_loader import ConfigLoader
    from .notification_processor import NotificationProcessor
    from .formatters import NotificationFormatter
    from .email_threading import NotificationEventType
except ImportError:
    # Fall back to absolute imports (when imported directly from tests)
    from config_loader import ConfigLoader  # type: ignore[no-redef]
    from notification_processor import NotificationProcessor  # type: ignore[no-redef]
    from formatters import NotificationFormatter  # type: ignore[no-redef]
    from email_threading import NotificationEventType  # type: ignore[no-redef]


class AppriseSmartNotificationHandler(MQTTHandler):
    """
    Smart notification handler using Apprise with YAML configuration.

    Sends notifications for:
    - Log entry updates by other users
    - Log entry replies by other users
    - New log entries in documents by other users
    - Reactions to log entries by other users
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        api_client: Optional[Any] = None,
        global_config: Optional[GlobalConfig] = None,
    ):
        """
        Initialize the handler.

        Args:
            config_path: Path to YAML configuration file
            api_client: Optional BELY API client
            global_config: Optional global configuration containing bely_url and other settings

        Raises:
            ImportError: If apprise or yaml not installed
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        super().__init__(api_client=api_client)

        self.bely_url = global_config.bely_url if global_config else None

        # Initialize components
        self.config_loader = ConfigLoader(self.logger)

        # Initialize formatter with timezone from config if available
        self.timezone = None
        self.formatter = NotificationFormatter(
            self.bely_url, self.logger
        )  # Will be updated after config load
        self.processor = NotificationProcessor(self.logger)

        # Load configuration
        if config_path:
            config = self.config_loader.load_config(config_path)
            self.processor.initialize_from_config(config, self.config_loader)
        else:
            self.logger.warning("No config path provided. Handler will not send notifications.")

    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        """
        Handle new log entry events.

        Notify document owner/creators if entry is created by someone else.

        Args:
            event: The log entry add event
        """
        try:
            await self._handle_add_event(event, is_reply=False)
        except Exception as e:
            self.logger.error(f"Error processing log entry add: {e}", exc_info=True)

    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        """
        Handle log entry update events.

        Notify:
        1. The original creator if their entry is updated by someone else (own_entry_edits)
        2. Document owners about any updates

        Args:
            event: The log entry update event
        """
        try:
            await self._handle_update_event(event, is_reply=False)
        except Exception as e:
            self.logger.error(f"Error processing log entry update: {e}", exc_info=True)

    async def handle_log_entry_reply_add(self, event: LogEntryReplyAddEvent) -> None:
        """
        Handle log entry reply events.

        Notify:
        1. The original entry creator if someone else replies
        2. The document owner if someone replies to any entry in their document

        Args:
            event: The log entry reply add event
        """
        try:
            await self._handle_add_event(event, is_reply=True)
        except Exception as e:
            self.logger.error(f"Error processing log entry reply add: {e}", exc_info=True)

    async def handle_log_entry_reply_update(self, event: LogEntryReplyUpdateEvent) -> None:
        """
        Handle log entry reply update events.

        Notify:
        1. The original entry creator if someone else updates a reply on their entry (own_entry_edits)
        2. Document owners about any reply updates

        Args:
            event: The log entry reply update event
        """
        try:
            await self._handle_update_event(event, is_reply=True)
        except Exception as e:
            self.logger.error(f"Error processing log entry reply update: {e}", exc_info=True)

    async def handle_log_reaction_add(self, event: LogReactionAddEvent) -> None:
        """
        Handle log reaction add events.

        Notify the original entry creator if someone else reacts to their entry.

        Args:
            event: The log reaction add event
        """
        try:
            await self._handle_reaction_event(event, is_add=True)
        except Exception as e:
            self.logger.error(f"Error processing log reaction add: {e}", exc_info=True)

    async def handle_log_reaction_delete(self, event: LogReactionDeleteEvent) -> None:
        """
        Handle log reaction delete events.

        Notify the original entry creator if someone removes a reaction from their entry.

        Args:
            event: The log reaction delete event
        """
        try:
            await self._handle_reaction_event(event, is_add=False)
        except Exception as e:
            self.logger.error(f"Error processing log reaction delete: {e}", exc_info=True)

    async def handle_log_entry_delete(self, event: LogEntryDeleteEvent) -> None:
        """
        Handle log entry delete events.

        Notify:
        1. The original creator if their entry is deleted by someone else
        2. Document owners about any deletions

        Args:
            event: The log entry delete event
        """
        try:
            await self._handle_delete_event(event, is_reply=False)
        except Exception as e:
            self.logger.error(f"Error processing log entry delete: {e}", exc_info=True)

    async def handle_log_entry_reply_delete(self, event: LogEntryReplyDeleteEvent) -> None:
        """
        Handle log entry reply delete events.

        Notify:
        1. The original entry creator if someone deletes a reply on their entry
        2. Document owners about any reply deletions

        Args:
            event: The log entry reply delete event
        """
        try:
            await self._handle_delete_event(event, is_reply=True)
        except Exception as e:
            self.logger.error(f"Error processing log entry reply delete: {e}", exc_info=True)

    async def _handle_add_event(
        self, event: Union[LogEntryAddEvent, LogEntryReplyAddEvent], is_reply: bool = False
    ) -> None:
        """
        Unified handler for add events (entry or reply adds).

        Args:
            event: The add event
            is_reply: Whether this is a reply add
        """
        notification_configs = []

        # Determine event type for threading
        event_type = (
            NotificationEventType.ENTRY_REPLY if is_reply else NotificationEventType.ENTRY_ADD
        )

        # Extract IDs for threading
        entry_id = event.log_info.id if hasattr(event, "log_info") else None
        parent_entry_id = (
            event.parent_log_info.id if is_reply and hasattr(event, "parent_log_info") else None
        )

        if is_reply:
            # Notify the original entry creator
            creator_username = event.parent_log_info.entered_by_username
            notification_configs.append(
                {
                    "username": creator_username,
                    "notification_type": "entry_replies",
                    "title": f"Reply to Your Log Entry in {event.parent_log_document_info.name}",
                    "body": self.formatter.format_reply_added(event),
                    "context": None,
                    "event_type": event_type,
                    "entry_id": entry_id,
                    "parent_entry_id": parent_entry_id,
                }
            )

            # Notify the document owner
            owner_username = event.parent_log_document_info.owner_username
            notification_configs.append(
                {
                    "username": owner_username,
                    "notification_type": "document_replies",
                    "title": f"New Reply in Your Document: {event.parent_log_document_info.name}",
                    "body": self.formatter.format_document_reply(event),
                    "context": "document_owner",
                    "event_type": event_type,
                    "entry_id": entry_id,
                    "parent_entry_id": parent_entry_id,
                }
            )
        else:
            # Don't notify if the creator is also the document creator
            if (
                event.event_triggered_by_username
                == event.parent_log_document_info.created_by_username
            ):
                return

            # Notify document owner about new entry
            owner_username = event.parent_log_document_info.owner_username
            notification_configs.append(
                {
                    "username": owner_username,
                    "notification_type": "new_entries",
                    "title": f"New Log Entry in {event.parent_log_document_info.name}",
                    "body": self.formatter.format_entry_added(event),
                    "context": None,
                    "event_type": event_type,
                    "entry_id": entry_id,
                }
            )

        await self.processor.process_notifications(event, notification_configs)

    async def _handle_update_event(
        self, event: Union[LogEntryUpdateEvent, LogEntryReplyUpdateEvent], is_reply: bool = False
    ) -> None:
        """
        Unified handler for update events (entry or reply updates).

        Args:
            event: The update event
            is_reply: Whether this is a reply update
        """
        notification_configs = []

        # Determine event type for threading
        event_type = (
            NotificationEventType.REPLY_UPDATE if is_reply else NotificationEventType.ENTRY_UPDATE
        )

        # Extract IDs for threading
        entry_id = event.log_info.id if hasattr(event, "log_info") else None
        parent_entry_id = (
            event.parent_log_info.id if is_reply and hasattr(event, "parent_log_info") else None
        )

        if is_reply:
            creator_username = event.parent_log_info.entered_by_username
            own_edit_title = (
                f"Reply Updated on Your Log Entry in {event.parent_log_document_info.name}"
            )
            own_edit_body = self.formatter.format_own_reply_updated(event)
            owner_title = f"Reply Updated in {event.parent_log_document_info.name}"
            owner_body = self.formatter.format_reply_updated(event)
            owner_notification_type = "entry_replies"
            own_context = "own_reply_update"
        else:
            creator_username = event.log_info.entered_by_username
            own_edit_title = f"Your Log Entry Was Edited: {event.parent_log_document_info.name}"
            own_edit_body = self.formatter.format_own_entry_edited(event)
            owner_title = f"Log Entry Updated: {event.parent_log_document_info.name}"
            owner_body = self.formatter.format_entry_updated(event)
            owner_notification_type = "entry_updates"
            own_context = "own_entry_edit"

        # Config for notifying the original creator
        notification_configs.append(
            {
                "username": creator_username,
                "notification_type": "own_entry_edits",
                "title": own_edit_title,
                "body": own_edit_body,
                "context": own_context,
                "event_type": event_type,
                "entry_id": entry_id,
                "parent_entry_id": parent_entry_id,
            }
        )

        # Config for notifying the document owner
        owner_username = event.parent_log_document_info.owner_username
        notification_configs.append(
            {
                "username": owner_username,
                "notification_type": owner_notification_type,
                "title": owner_title,
                "body": owner_body,
                "context": None,
                "event_type": event_type,
                "entry_id": entry_id,
                "parent_entry_id": parent_entry_id,
            }
        )

        await self.processor.process_notifications(event, notification_configs)

    async def _handle_reaction_event(
        self, event: Union[LogReactionAddEvent, LogReactionDeleteEvent], is_add: bool = True
    ) -> None:
        """
        Handle log reaction events (both add and delete).

        Notify the original entry creator if someone else reacts to or removes a reaction from their entry.

        Args:
            event: The log reaction event
            is_add: Whether this is an add event (True) or delete event (False)
        """
        # Don't notify the reactor (person who added/removed the reaction)
        if event.event_triggered_by_username == event.parent_log_info.entered_by_username:
            return

        # Check if we should notify about reactions
        creator_username = event.parent_log_info.entered_by_username
        if not self.processor.should_notify(creator_username, "reactions"):
            return

        # Determine event type for threading
        event_type = (
            NotificationEventType.REACTION_ADD if is_add else NotificationEventType.REACTION_DELETE
        )

        # Extract entry ID for threading
        entry_id = event.parent_log_info.id if hasattr(event, "parent_log_info") else None

        # Build notification
        if is_add:
            title = f"Reaction to Your Log Entry in {event.parent_log_document_info.name}"
            body = self.formatter.format_reaction_added(event)
        else:
            title = f"Reaction Removed from Your Log Entry in {event.parent_log_document_info.name}"
            body = self.formatter.format_reaction_deleted(event)

        # Send notification with threading support
        await self.processor.send_notification_with_threading(
            username=creator_username,
            title=title,
            body=body,
            event_type=event_type,
            document_id=event.parent_log_document_info.id,
            document_name=event.parent_log_document_info.name,
            entry_id=entry_id,
            action_by=event.event_triggered_by_username,
        )

    async def _handle_delete_event(
        self, event: Union[LogEntryDeleteEvent, LogEntryReplyDeleteEvent], is_reply: bool = False
    ) -> None:
        """
        Unified handler for delete events (entry or reply deletes).

        Args:
            event: The delete event
            is_reply: Whether this is a reply delete
        """
        notification_configs = []

        # Determine event type for threading
        event_type = (
            NotificationEventType.REPLY_DELETE if is_reply else NotificationEventType.ENTRY_DELETE
        )

        # Extract IDs for threading
        entry_id = event.log_info.id if hasattr(event, "log_info") else None
        parent_entry_id = (
            event.parent_log_info.id if is_reply and hasattr(event, "parent_log_info") else None
        )

        if is_reply:
            # Notify the original entry creator about reply deletion
            creator_username = event.parent_log_info.entered_by_username
            notification_configs.append(
                {
                    "username": creator_username,
                    "notification_type": "entry_replies",
                    "title": f"Reply Deleted from Your Log Entry in {event.parent_log_document_info.name}",
                    "body": self.formatter.format_reply_deleted(event),
                    "context": "reply_delete",
                    "event_type": event_type,
                    "entry_id": entry_id,
                    "parent_entry_id": parent_entry_id,
                }
            )

            # Notify the document owner about reply deletion
            owner_username = event.parent_log_document_info.owner_username
            notification_configs.append(
                {
                    "username": owner_username,
                    "notification_type": "document_replies",
                    "title": f"Reply Deleted in Your Document: {event.parent_log_document_info.name}",
                    "body": self.formatter.format_document_reply_deleted(event),
                    "context": "document_owner",
                    "event_type": event_type,
                    "entry_id": entry_id,
                    "parent_entry_id": parent_entry_id,
                }
            )
        else:
            # Notify the original entry creator about their entry being deleted
            creator_username = event.log_info.entered_by_username
            notification_configs.append(
                {
                    "username": creator_username,
                    "notification_type": "own_entry_edits",
                    "title": f"Your Log Entry Was Deleted: {event.parent_log_document_info.name}",
                    "body": self.formatter.format_own_entry_deleted(event),
                    "context": "own_entry_delete",
                    "event_type": event_type,
                    "entry_id": entry_id,
                }
            )

            # Notify the document owner about entry deletion
            owner_username = event.parent_log_document_info.owner_username
            notification_configs.append(
                {
                    "username": owner_username,
                    "notification_type": "entry_updates",
                    "title": f"Log Entry Deleted: {event.parent_log_document_info.name}",
                    "body": self.formatter.format_entry_deleted(event),
                    "context": "entry_delete",
                    "event_type": event_type,
                    "entry_id": entry_id,
                }
            )

        await self.processor.process_notifications(event, notification_configs)
