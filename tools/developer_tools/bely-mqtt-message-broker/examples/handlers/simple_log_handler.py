"""
Simple log entry handler example.

This handler demonstrates basic usage of the BELY MQTT Framework
by logging when new entries are added.
"""

from bely_mqtt import MQTTHandler, LogEntryAddEvent


class SimpleLogHandler(MQTTHandler):
    """Logs when new entries are added to BELY."""
    
    # Uses default topic_pattern "bely/#" - receives all BELY events
    # The framework will automatically route log entry add events to handle_log_entry_add
    
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        """Handle new log entry event using the specific handler method."""
        try:
            # Log the event details
            self.logger.info(
                f"New log entry added: "
                f"ID={event.log_info.id}, "
                f"Document={event.parent_log_document_info.name}, "
                f"By={event.event_triggered_by_username}"
            )
            
            # Log the entry description (first 100 chars)
            description = event.description[:100]
            if len(event.description) > 100:
                description += "..."
            self.logger.info(f"Description: {description}")
            
            # You can access all event fields with type safety
            self.logger.debug(f"Timestamp: {event.event_timestamp}")
            self.logger.debug(f"Logbooks: {[lb.name for lb in event.logbook_list]}")
            
        except Exception as e:
            self.logger.error(f"Failed to process log entry: {e}", exc_info=True)