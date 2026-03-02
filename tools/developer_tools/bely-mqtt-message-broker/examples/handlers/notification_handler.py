"""
Example notification handler using Apprise.

This handler demonstrates how to send notifications for specific events.
It requires the 'apprise' extra to be installed:
    pip install bely-mqtt-framework[apprise]
"""

import logging
from typing import Optional

from bely_mqtt.models import (
    LogEntryAddEvent,
    LogEntryReplyAddEvent,
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


class NotificationHandler(MQTTHandler):
    """
    Handler that sends notifications for BELY events using Apprise.
    
    This is an example handler showing how to integrate with external
    notification services. Configure notification endpoints via environment
    variables or configuration files.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the notification handler."""
        super().__init__(*args, **kwargs)
        self.apprise_instance: Optional[apprise.Apprise] = None
        if APPRISE_AVAILABLE:
            self.apprise_instance = apprise.Apprise()

    @property
    def topic_pattern(self) -> str:
        """Subscribe to log entry events."""
        return "bely/logEntry/#"

    async def handle(self, message: MQTTMessage) -> None:
        """Handle log entry events and send notifications."""
        if not APPRISE_AVAILABLE:
            self.logger.warning("Apprise not available, skipping notification")
            return

        try:
            if "Add" in message.topic:
                await self._handle_add_event(message)
            elif "Update" in message.topic:
                await self._handle_update_event(message)
        except Exception as e:
            self.logger.error(f"Failed to handle notification event: {e}")

    async def _handle_add_event(self, message: MQTTMessage) -> None:
        """Handle log entry add event."""
        event = LogEntryAddEvent(**message.payload)
        title = f"New Log Entry in {event.parent_log_document_info.name}"
        body = (
            f"User {event.event_triggered_by_username} added a new log entry.\n"
            f"Logbooks: {', '.join(lb.display_name or lb.name for lb in event.logbook_list)}"
        )
        await self._send_notification(title, body)

    async def _handle_update_event(self, message: MQTTMessage) -> None:
        """Handle log entry update event."""
        event = LogEntryUpdateEvent(**message.payload)
        title = f"Log Entry Updated in {event.parent_log_document_info.name}"
        body = (
            f"User {event.event_triggered_by_username} updated a log entry.\n"
            f"Changes:\n{event.text_diff[:200]}..."
        )
        await self._send_notification(title, body)

    async def _send_notification(self, title: str, body: str) -> None:
        """Send a notification via Apprise."""
        if not self.apprise_instance:
            self.logger.warning("Apprise instance not initialized")
            return

        # Example: Add notification endpoints
        # self.apprise_instance.add('mailto://user:password@gmail.com')
        # self.apprise_instance.add('discord://webhook_id/webhook_token')

        # For now, just log the notification
        self.logger.info(f"Notification: {title}")
        self.logger.info(f"  {body}")

        # Uncomment to actually send notifications:
        # self.apprise_instance.notify(
        #     body=body,
        #     title=title,
        # )
