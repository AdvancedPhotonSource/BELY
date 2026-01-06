"""
Notification formatters for Apprise Smart Notification Handler.
"""

import logging
from datetime import datetime, tzinfo
from typing import Optional, Union
from zoneinfo import ZoneInfo

from bely_mqtt import (
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryDeleteEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
    LogEntryReplyDeleteEvent,
    LogReactionAddEvent,
    LogReactionDeleteEvent,
    LogEntryEventBase,
    LogReactionEventBase,
)
from bely_mqtt.models import CoreEvent


class NotificationFormatter:
    """Handles formatting of notification messages."""

    def __init__(
        self, bely_url: Optional[str], logger: logging.Logger, timezone: Optional[str] = None
    ):
        """
        Initialize the formatter.

        Args:
            bely_url: Base URL for BELY instance
            logger: Logger instance for output
            timezone: Timezone string (e.g., 'America/New_York'). If None, uses system local timezone.
        """
        self.bely_url = bely_url
        self.logger = logger
        self.timezone: tzinfo  # Declare the type

        # Set timezone - use provided timezone, or detect local timezone
        if timezone:
            try:
                self.timezone = ZoneInfo(timezone)
            except Exception as e:
                self.logger.warning(f"Invalid timezone '{timezone}': {e}. Using UTC.")
                self.timezone = ZoneInfo("UTC")
        else:
            # Detect local timezone using datetime
            try:
                # Get the local timezone from the system
                local_tz = datetime.now().astimezone().tzinfo
                if local_tz is not None:
                    self.timezone = local_tz
                else:
                    self.timezone = ZoneInfo("UTC")
            except Exception as e:
                self.logger.debug(f"Could not detect local timezone: {e}. Using UTC.")
                self.timezone = ZoneInfo("UTC")

    def _format_timestamp(self, timestamp: datetime) -> str:
        """
        Format a timestamp for display in notifications.

        Args:
            timestamp: The datetime object to format

        Returns:
            Formatted timestamp string in local timezone
        """
        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            # Assume UTC if no timezone info
            timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to local timezone
        local_timestamp = timestamp.astimezone(self.timezone)

        # Format as readable string with timezone
        return local_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")

    def format_entry_added(self, event: LogEntryAddEvent) -> str:
        """Format notification body for new log entry."""
        body = (
            f"New entry added to {event.parent_log_document_info.name}<br/>"
            f"By: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Entry markdown: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event)

    def format_entry_updated(self, event: LogEntryUpdateEvent) -> str:
        """Format notification body for updated log entry (document owner notification)."""
        body = (
            f"Entry updated in {event.parent_log_document_info.name}<br/>"
            f"Updated by: {event.event_triggered_by_username}<br/>"
            f"Original author: {event.log_info.entered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Entry markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event)

    def format_own_entry_edited(self, event: LogEntryUpdateEvent) -> str:
        """Format notification body for when user's own entry is edited by someone else."""
        body = (
            f"Entry edited in {event.parent_log_document_info.name}<br/>"
            f"Original author: {event.log_info.entered_by_username}<br/>"
            f"Edited by: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Entry markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "own_entry_edit")

    def format_reply_added(self, event: LogEntryReplyAddEvent) -> str:
        """Format notification body for new reply."""
        body = (
            f"New reply to entry in {event.parent_log_document_info.name}<br/>"
            f"Entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Reply by: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"<br/>Reply markdown: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event)

    def format_reply_updated(self, event: LogEntryReplyUpdateEvent) -> str:
        """Format notification body for updated reply (document owner notification)."""
        body = (
            f"Reply updated in {event.parent_log_document_info.name}<br/>"
            f"Updated by: {event.event_triggered_by_username}<br/>"
            f"On entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"<br/>Reply markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event)

    def format_own_reply_updated(self, event: LogEntryReplyUpdateEvent) -> str:
        """Format notification body for when a reply on user's own entry is updated by someone else."""
        body = (
            f"Reply updated on entry in {event.parent_log_document_info.name}<br/>"
            f"Entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Updated by: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"<br/>Reply markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "own_reply_update")

    def format_document_reply(self, event: LogEntryReplyAddEvent) -> str:
        """Format notification body for document owner about new reply."""
        body = (
            f"New reply added in document {event.parent_log_document_info.name}<br/>"
            f"Reply by: {event.event_triggered_by_username}<br/>"
            f"To entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"<br/>Reply markdown: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "document_owner")

    def format_reaction_added(self, event: LogReactionAddEvent) -> str:
        """Format notification body for added reaction."""
        reaction_info = event.log_reaction.reaction
        body = (
            f"New reaction added to entry in {event.parent_log_document_info.name}<br/>"
            f"By: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Reaction: {reaction_info.emoji} {reaction_info.name}<br/>"
            f"Description: {event.description}"
        )
        return self._append_permalink_and_trigger(body, event)

    def format_reaction_deleted(self, event: LogReactionDeleteEvent) -> str:
        """Format notification body for deleted reaction."""
        reaction_info = event.log_reaction.reaction
        body = (
            f"Reaction removed from entry in {event.parent_log_document_info.name}<br/>"
            f"By: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Reaction: {reaction_info.emoji} {reaction_info.name}<br/>"
            f"Description: {event.description}"
        )
        return self._append_permalink_and_trigger(body, event)

    def format_entry_deleted(self, event: LogEntryDeleteEvent) -> str:
        """Format notification body for deleted log entry (document owner notification)."""
        body = (
            f"Entry deleted from {event.parent_log_document_info.name}<br/>"
            f"Deleted by: {event.event_triggered_by_username}<br/>"
            f"Original author: {event.log_info.entered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Deleted entry content: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "entry_delete")

    def format_own_entry_deleted(self, event: LogEntryDeleteEvent) -> str:
        """Format notification body for when user's own entry is deleted by someone else."""
        body = (
            f"Entry was deleted from {event.parent_log_document_info.name}<br/>"
            f"Deleted by: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Deleted entry content: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "own_entry_delete")

    def format_reply_deleted(self, event: LogEntryReplyDeleteEvent) -> str:
        """Format notification body for deleted reply (entry creator notification)."""
        body = (
            f"Reply deleted from entry in {event.parent_log_document_info.name}<br/>"
            f"Deleted by: {event.event_triggered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"<br/>Deleted reply content: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "reply_delete")

    def format_document_reply_deleted(self, event: LogEntryReplyDeleteEvent) -> str:
        """Format notification body for document owner about deleted reply."""
        body = (
            f"Reply deleted from document {event.parent_log_document_info.name}<br/>"
            f"Deleted by: {event.event_triggered_by_username}<br/>"
            f"On entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Time: {self._format_timestamp(event.event_timestamp)}<br/>"
            f"<br/>Deleted reply content: {self._format_text_diff_pre(event.text_diff)}"
        )
        return self._append_permalink_and_trigger(body, event, "document_owner")

    def _format_text_diff_pre(self, text_diff: str, max_height: str = "200px") -> str:
        """
        Format text diff in a styled pre box.

        Args:
            text_diff: The text difference to display
            max_height: Maximum height of the pre box (default: "200px")

        Returns:
            HTML formatted pre box with the text diff
        """
        return (
            f"<pre style='max-height: {max_height}; overflow-y: auto; "
            f"background-color: #f5f5f5; padding: 10px; border: 1px solid #ddd;'>"
            f"{text_diff}</pre>"
        )

    def _generate_log_entry_link(self, document_id: int, log_id: int) -> str:
        """
        Generate a direct link to a log entry in BELY.

        Args:
            document_id: The document ID
            log_id: The log entry ID

        Returns:
            URL string to the log entry
        """
        if not self.bely_url:
            return ""

        # Remove trailing slash if present
        base_url = self.bely_url.rstrip("/")

        return f"{base_url}/views/item/view?id={document_id}&logId={log_id}"

    def _append_permalink_and_trigger(
        self,
        body: str,
        event: Union[LogEntryEventBase, LogReactionEventBase],
        notification_context: Optional[str] = None,
    ) -> str:
        """
        Append permalink and trigger description to notification body.

        Args:
            body: The notification body
            event: The event that triggered the notification
            notification_context: Optional context about the notification type

        Returns:
            Body with permalink and trigger description appended
        """
        # Generate permalink if bely_url is available
        if self.bely_url:
            # Handle both LogEntryEventBase and LogReaction events
            if isinstance(event, LogEntryEventBase):
                log_id = event.log_info.id
                document_id = event.parent_log_document_info.id
            elif isinstance(event, LogReactionEventBase):
                log_id = event.parent_log_info.id
                document_id = event.parent_log_document_info.id
            else:
                log_id = None
                document_id = None

            if log_id and document_id:
                link = self._generate_log_entry_link(document_id, log_id)
                body += f'<br/><br/><a href="{link}">View entry</a>'

        # Add trigger description
        trigger_description = self._get_trigger_description(event, notification_context)
        body += f"<br/><br/><hr/><small><i>{trigger_description}</i></small>"

        return body

    def _get_trigger_description(
        self, event: CoreEvent, notification_context: Optional[str] = None
    ) -> str:
        """
        Get a description of why this notification was triggered.

        Args:
            event: The event that triggered the notification
            notification_context: Optional context about the notification type

        Returns:
            A human-readable description of the trigger
        """
        if isinstance(event, LogEntryAddEvent):
            return (
                f"This notification was sent because {event.event_triggered_by_username} "
                f"added a new log entry to the document '{event.parent_log_document_info.name}' "
                f"which you own. You have 'new_entries' notifications enabled."
            )
        elif isinstance(event, LogEntryUpdateEvent):
            # Check the notification context to determine the type
            if notification_context == "own_entry_edit":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"edited a log entry that you originally created in the document "
                    f"'{event.parent_log_document_info.name}'. You have 'own_entry_edits' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"updated a log entry in the document '{event.parent_log_document_info.name}' "
                    f"which you own. You have 'entry_updates' notifications enabled."
                )
        elif isinstance(event, LogEntryReplyAddEvent):
            # Check the notification context to determine the type
            if notification_context == "document_owner":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"added a reply to an entry in your document '{event.parent_log_document_info.name}'. "
                    f"You have 'document_replies' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"replied to your log entry in the document '{event.parent_log_document_info.name}'. "
                    f"You have 'entry_replies' notifications enabled."
                )
        elif isinstance(event, LogEntryReplyUpdateEvent):
            # Check the notification context to determine the type
            if notification_context == "own_reply_update":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"updated a reply on your log entry in the document "
                    f"'{event.parent_log_document_info.name}'. You have 'own_entry_edits' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"updated a reply in the document '{event.parent_log_document_info.name}' "
                    f"which you own. You have 'entry_replies' notifications enabled."
                )
        elif isinstance(event, LogReactionAddEvent):
            return (
                f"This notification was sent because {event.event_triggered_by_username} "
                f"added a reaction to your log entry in the document "
                f"'{event.parent_log_document_info.name}'. You have 'reactions' notifications enabled."
            )
        elif isinstance(event, LogReactionDeleteEvent):
            return (
                f"This notification was sent because {event.event_triggered_by_username} "
                f"removed a reaction from your log entry in the document "
                f"'{event.parent_log_document_info.name}'. You have 'reactions' notifications enabled."
            )
        elif isinstance(event, LogEntryDeleteEvent):
            # Check the notification context to determine the type
            if notification_context == "own_entry_delete":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"deleted a log entry that you originally created in the document "
                    f"'{event.parent_log_document_info.name}'. You have 'own_entry_edits' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"deleted a log entry in the document '{event.parent_log_document_info.name}' "
                    f"which you own. You have 'entry_updates' notifications enabled."
                )
        elif isinstance(event, LogEntryReplyDeleteEvent):
            # Check the notification context to determine the type
            if notification_context == "reply_delete":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"deleted a reply from your log entry in the document "
                    f"'{event.parent_log_document_info.name}'. You have 'entry_replies' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"deleted a reply in the document '{event.parent_log_document_info.name}' "
                    f"which you own. You have 'document_replies' notifications enabled."
                )
        else:
            return "This notification was sent due to activity on your BELY content."
