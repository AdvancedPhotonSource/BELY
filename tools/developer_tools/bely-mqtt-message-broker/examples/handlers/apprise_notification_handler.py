"""
Advanced notification handler using Apprise.

This handler demonstrates how to send notifications for BELY events
using the Apprise library, which supports multiple notification services.

Installation:
    pip install bely-mqtt-framework[apprise]

Configuration:
    Set APPRISE_URLS environment variable with notification endpoints:
    
    APPRISE_URLS="mailto://user:password@gmail.com discord://webhook_id/webhook_token"
    
    Or configure in handler initialization.
"""

import logging
import os
from typing import List, Optional

from bely_mqtt.models import (
    LogEntryAddEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
    LogEntryUpdateEvent,
    MQTTMessage,
)
from bely_mqtt.plugin import MQTTHandler

logger = logging.getLogger(__name__)

try:
    import apprise

    APPRISE_AVAILABLE = True
except ImportError:
    APPRISE_AVAILABLE = False
    logger.warning(
        "Apprise not installed. Install with: pip install bely-mqtt-framework[apprise]"
    )


class ApprisNotificationHandler(MQTTHandler):
    """
    Send notifications for BELY events using Apprise.
    
    Supports multiple notification services:
    - Email (SMTP)
    - Discord
    - Slack
    - Telegram
    - Pushbullet
    - And many more...
    
    Configure notification URLs via:
    1. APPRISE_URLS environment variable
    2. Handler initialization
    3. Configuration file
    """

    def __init__(self, *args, notification_urls: Optional[List[str]] = None, **kwargs):
        """
        Initialize the notification handler.
        
        Args:
            notification_urls: List of Apprise notification URLs.
                              If not provided, will read from APPRISE_URLS env var.
        """
        super().__init__(*args, **kwargs)
        self.apprise_instance: Optional[apprise.Apprise] = None
        self.notification_urls: List[str] = []

        if not APPRISE_AVAILABLE:
            self.logger.warning(
                "Apprise not available. Install with: pip install bely-mqtt-framework[apprise]"
            )
            return

        # Get notification URLs from parameter or environment
        if notification_urls:
            self.notification_urls = notification_urls
        else:
            env_urls = os.getenv("APPRISE_URLS", "")
            if env_urls:
                self.notification_urls = env_urls.split()

        if self.notification_urls:
            self.apprise_instance = apprise.Apprise()
            for url in self.notification_urls:
                if self.apprise_instance.add(url):
                    self.logger.info(f"Added notification endpoint: {url}")
                else:
                    self.logger.warning(f"Failed to add notification endpoint: {url}")
        else:
            self.logger.warning(
                "No notification URLs configured. Set APPRISE_URLS environment variable."
            )

    @property
    def topic_pattern(self) -> str:
        """Subscribe to all log entry events."""
        return "bely/logEntry/#"

    async def handle(self, message: MQTTMessage) -> None:
        """Handle log entry events and send notifications."""
        if not APPRISE_AVAILABLE or not self.apprise_instance:
            self.logger.debug("Apprise not available, skipping notification")
            return

        try:
            if "Reply" in message.topic:
                if "Add" in message.topic:
                    await self._handle_reply_added(message)
                elif "Update" in message.topic:
                    await self._handle_reply_updated(message)
            elif "Add" in message.topic:
                await self._handle_entry_added(message)
            elif "Update" in message.topic:
                await self._handle_entry_updated(message)
        except Exception as e:
            self.logger.error(f"Failed to handle notification event: {e}", exc_info=True)

    async def _handle_entry_added(self, message: MQTTMessage) -> None:
        """Handle log entry add event."""
        event = LogEntryAddEvent(**message.payload)

        title = f"📝 New Log Entry in {event.parent_log_document_info.name}"
        body = self._format_entry_added_body(event)

        await self._send_notification(title, body)

    async def _handle_entry_updated(self, message: MQTTMessage) -> None:
        """Handle log entry update event."""
        event = LogEntryUpdateEvent(**message.payload)

        title = f"✏️ Log Entry Updated in {event.parent_log_document_info.name}"
        body = self._format_entry_updated_body(event)

        await self._send_notification(title, body)

    async def _handle_reply_added(self, message: MQTTMessage) -> None:
        """Handle reply add event."""
        event = LogEntryReplyAddEvent(**message.payload)

        title = f"💬 Reply Added to Entry in {event.parent_log_document_info.name}"
        body = self._format_reply_added_body(event)

        await self._send_notification(title, body)

    async def _handle_reply_updated(self, message: MQTTMessage) -> None:
        """Handle reply update event."""
        event = LogEntryReplyUpdateEvent(**message.payload)

        title = f"✏️ Reply Updated in {event.parent_log_document_info.name}"
        body = self._format_reply_updated_body(event)

        await self._send_notification(title, body)

    def _format_entry_added_body(self, event: LogEntryAddEvent) -> str:
        """Format notification body for entry added event."""
        logbooks = ", ".join(lb.display_name or lb.name for lb in event.logbook_list)
        return (
            f"User: {event.event_triggered_by_username}\n"
            f"Logbooks: {logbooks}\n"
            f"Entry ID: {event.log_info.id}\n"
            f"Time: {event.event_timestamp.isoformat()}\n\n"
            f"Content:\n{event.text_diff[:200]}"
        )

    def _format_entry_updated_body(self, event: LogEntryUpdateEvent) -> str:
        """Format notification body for entry updated event."""
        logbooks = ", ".join(lb.display_name or lb.name for lb in event.logbook_list)
        return (
            f"User: {event.event_triggered_by_username}\n"
            f"Logbooks: {logbooks}\n"
            f"Entry ID: {event.log_info.id}\n"
            f"Time: {event.event_timestamp.isoformat()}\n\n"
            f"Changes:\n{event.text_diff[:200]}"
        )

    def _format_reply_added_body(self, event: LogEntryReplyAddEvent) -> str:
        """Format notification body for reply added event."""
        logbooks = ", ".join(lb.display_name or lb.name for lb in event.logbook_list)
        return (
            f"User: {event.event_triggered_by_username}\n"
            f"Logbooks: {logbooks}\n"
            f"Reply to Entry: {event.parent_log_info.id}\n"
            f"Reply ID: {event.log_info.id}\n"
            f"Time: {event.event_timestamp.isoformat()}\n\n"
            f"Content:\n{event.text_diff[:200]}"
        )

    def _format_reply_updated_body(self, event: LogEntryReplyUpdateEvent) -> str:
        """Format notification body for reply updated event."""
        logbooks = ", ".join(lb.display_name or lb.name for lb in event.logbook_list)
        return (
            f"User: {event.event_triggered_by_username}\n"
            f"Logbooks: {logbooks}\n"
            f"Reply to Entry: {event.parent_log_info.id}\n"
            f"Reply ID: {event.log_info.id}\n"
            f"Time: {event.event_timestamp.isoformat()}\n\n"
            f"Changes:\n{event.text_diff[:200]}"
        )

    async def _send_notification(self, title: str, body: str) -> None:
        """Send a notification via Apprise."""
        if not self.apprise_instance:
            self.logger.warning("Apprise instance not initialized")
            return

        self.logger.info(f"Sending notification: {title}")

        # Send notification
        self.apprise_instance.notify(
            body=body,
            title=title,
        )


class SelectiveNotificationHandler(MQTTHandler):
    """
    Send notifications only for specific conditions.
    
    This handler demonstrates how to filter events and only send
    notifications for specific logbooks or users.
    """

    def __init__(
        self,
        *args,
        notification_urls: Optional[List[str]] = None,
        target_logbooks: Optional[List[str]] = None,
        exclude_users: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Initialize the selective notification handler.
        
        Args:
            notification_urls: List of Apprise notification URLs.
            target_logbooks: Only notify for these logbooks (None = all).
            exclude_users: Don't notify for these users.
        """
        super().__init__(*args, **kwargs)
        self.target_logbooks = target_logbooks
        self.exclude_users = exclude_users or []
        self.apprise_instance: Optional[apprise.Apprise] = None

        if not APPRISE_AVAILABLE:
            return

        if notification_urls:
            self.apprise_instance = apprise.Apprise()
            for url in notification_urls:
                self.apprise_instance.add(url)

    @property
    def topic_pattern(self) -> str:
        """Subscribe to log entry add events."""
        return "bely/logEntry/Add"

    async def handle(self, message: MQTTMessage) -> None:
        """Handle log entry add event with filtering."""
        if not APPRISE_AVAILABLE or not self.apprise_instance:
            return

        try:
            event = LogEntryAddEvent(**message.payload)

            # Filter by user
            if event.event_triggered_by_username in self.exclude_users:
                self.logger.debug(
                    f"Skipping notification for excluded user: "
                    f"{event.event_triggered_by_username}"
                )
                return

            # Filter by logbook
            if self.target_logbooks:
                logbook_names = [lb.name for lb in event.logbook_list]
                if not any(lb in self.target_logbooks for lb in logbook_names):
                    self.logger.debug(
                        f"Skipping notification for non-target logbooks: {logbook_names}"
                    )
                    return

            # Send notification
            title = f"📝 New Entry in {event.parent_log_document_info.name}"
            body = (
                f"User: {event.event_triggered_by_username}\n"
                f"Entry ID: {event.log_info.id}\n\n"
                f"{event.text_diff[:200]}"
            )

            self.apprise_instance.notify(title=title, body=body)
            self.logger.info(f"Notification sent for entry {event.log_info.id}")

        except Exception as e:
            self.logger.error(f"Failed to handle notification: {e}", exc_info=True)
