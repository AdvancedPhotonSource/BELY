"""
Example handler for log entry events.

This handler demonstrates how to parse specific event types
and extract relevant information.
"""

import logging

from bely_mqtt.models import LogEntryAddEvent, LogEntryUpdateEvent, MQTTMessage
from bely_mqtt.plugin import MQTTHandler

logger = logging.getLogger(__name__)


class LogEntryAddHandler(MQTTHandler):
    """
    Handler for log entry add events.
    
    This handler processes events when new log entries are added
    and can be extended to send notifications or trigger workflows.
    """

    @property
    def topic_pattern(self) -> str:
        """Subscribe to log entry add events."""
        return "bely/logEntry/Add"

    async def handle(self, message: MQTTMessage) -> None:
        """Handle log entry add event."""
        try:
            event = LogEntryAddEvent(**message.payload)
            self.logger.info(
                f"Log entry added: ID={event.log_info.id}, "
                f"Document={event.parent_log_document_info.name}, "
                f"By={event.event_triggered_by_username}"
            )
            self.logger.debug(f"Text: {event.text_diff}")

            # Example: Query BELY API for more information
            if self.api_client:
                try:
                    log_data = self.api_client.get_log_entry(event.log_info.id)
                    self.logger.debug(f"Retrieved log entry data: {log_data}")
                except NotImplementedError:
                    pass

        except Exception as e:
            self.logger.error(f"Failed to parse log entry add event: {e}")


class LogEntryUpdateHandler(MQTTHandler):
    """
    Handler for log entry update events.
    
    This handler processes events when log entries are modified.
    """

    @property
    def topic_pattern(self) -> str:
        """Subscribe to log entry update events."""
        return "bely/logEntry/Update"

    async def handle(self, message: MQTTMessage) -> None:
        """Handle log entry update event."""
        try:
            event = LogEntryUpdateEvent(**message.payload)
            self.logger.info(
                f"Log entry updated: ID={event.log_info.id}, "
                f"Document={event.parent_log_document_info.name}, "
                f"By={event.event_triggered_by_username}"
            )
            self.logger.debug(f"Changes:\n{event.text_diff}")

        except Exception as e:
            self.logger.error(f"Failed to parse log entry update event: {e}")
