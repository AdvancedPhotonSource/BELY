"""
Example handler that uses both specific and generic event handler methods with typed events.

This handler demonstrates how to implement both specific event handlers
(for specific event types) and a generic fallback handler for other events.
This is the most flexible approach.

The framework automatically parses MQTT messages into properly typed event objects
and passes them to the appropriate handler method.
"""

from bely_mqtt import (
    MQTTHandler,
    MQTTMessage,
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
    LogReactionAddEvent,
    LogReactionDeleteEvent,
    CoreEvent,
)


class HybridEventHandler(MQTTHandler):
    """
    Handler that implements both specific and generic event handler methods with typed events.
    
    This handler processes specific log entry events and replies, with a
    fallback generic handler for other event types. All handler methods receive
    properly typed event objects instead of raw MQTT messages.
    """

    @property
    def topic_pattern(self) -> str:
        """Subscribe to all BELY events."""
        return "bely/#"

    # Specific event handlers for log entries
    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        """
        Handle log entry add events.
        
        Args:
            event: The log entry add event (already parsed and typed).
        """
        try:
            self.logger.info(f"Log entry added: {event.log_info.id}")
            self.logger.debug(f"Document: {event.parent_log_document_info.name}")
            await self.process_log_entry_add(event)
        except Exception as e:
            self.logger.error(f"Error processing log entry add: {e}", exc_info=True)

    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        """
        Handle log entry update events.
        
        Args:
            event: The log entry update event (already parsed and typed).
        """
        try:
            self.logger.info(f"Log entry updated: {event.log_info.id}")
            self.logger.debug(f"Document: {event.parent_log_document_info.name}")
            await self.process_log_entry_update(event)
        except Exception as e:
            self.logger.error(f"Error processing log entry update: {e}", exc_info=True)

    # Specific event handlers for replies
    async def handle_log_entry_reply_add(self, event: LogEntryReplyAddEvent) -> None:
        """
        Handle log entry reply add events.
        
        Args:
            event: The log entry reply add event (already parsed and typed).
        """
        try:
            self.logger.info(f"Reply added to log entry: {event.parent_log_info.id}")
            await self.process_reply_add(event)
        except Exception as e:
            self.logger.error(f"Error processing reply add: {e}", exc_info=True)

    async def handle_log_entry_reply_update(self, event: LogEntryReplyUpdateEvent) -> None:
        """
        Handle log entry reply update events.
        
        Args:
            event: The log entry reply update event (already parsed and typed).
        """
        try:
            self.logger.info(f"Reply updated on log entry: {event.parent_log_info.id}")
            await self.process_reply_update(event)
        except Exception as e:
            self.logger.error(f"Error processing reply update: {e}", exc_info=True)

    # Specific event handlers for reactions
    async def handle_log_reaction_add(self, event: LogReactionAddEvent) -> None:
        """
        Handle log reaction add events.
        
        Args:
            event: The log reaction add event (already parsed and typed).
        """
        try:
            self.logger.info(
                f"Reaction added to log entry {event.parent_log_info.id}: "
                f"{event.log_reaction.reaction.emoji} by {event.log_reaction.username}"
            )
            await self.process_reaction_add(event)
        except Exception as e:
            self.logger.error(f"Error processing reaction add: {e}", exc_info=True)

    async def handle_log_reaction_delete(self, event: LogReactionDeleteEvent) -> None:
        """
        Handle log reaction delete events.
        
        Args:
            event: The log reaction delete event (already parsed and typed).
        """
        try:
            self.logger.info(
                f"Reaction deleted from log entry {event.parent_log_info.id}: "
                f"{event.log_reaction.reaction.emoji} by {event.log_reaction.username}"
            )
            await self.process_reaction_delete(event)
        except Exception as e:
            self.logger.error(f"Error processing reaction delete: {e}", exc_info=True)

    # Generic event handlers for other events
    async def handle_generic_add(self, event: CoreEvent) -> None:
        """
        Handle generic add events.
        
        Args:
            event: The generic add event (already parsed and typed).
        """
        try:
            self.logger.info(f"Generic add: {event.entity_name} (ID: {event.entity_id})")
            await self.process_generic_add(event)
        except Exception as e:
            self.logger.error(f"Error processing generic add: {e}", exc_info=True)

    async def handle_generic_update(self, event: CoreEvent) -> None:
        """
        Handle generic update events.
        
        Args:
            event: The generic update event (already parsed and typed).
        """
        try:
            self.logger.info(f"Generic update: {event.entity_name} (ID: {event.entity_id})")
            await self.process_generic_update(event)
        except Exception as e:
            self.logger.error(f"Error processing generic update: {e}", exc_info=True)

    async def handle_generic_delete(self, event: CoreEvent) -> None:
        """
        Handle generic delete events.
        
        Args:
            event: The generic delete event (already parsed and typed).
        """
        try:
            self.logger.info(f"Generic delete: {event.entity_name} (ID: {event.entity_id})")
            await self.process_generic_delete(event)
        except Exception as e:
            self.logger.error(f"Error processing generic delete: {e}", exc_info=True)

    # Fallback generic handler for unknown events
    async def handle_generic(self, message: MQTTMessage) -> None:
        """
        Fallback handler for events that don't match any specific handler.
        
        This is called if the message topic doesn't match any of the
        specific event types defined above.
        
        Args:
            message: The raw MQTT message.
        """
        self.logger.debug(f"Received unknown event on topic: {message.topic}")

    # Processing methods
    async def process_log_entry_add(self, event: LogEntryAddEvent) -> None:
        """Process a log entry add event."""
        self.logger.debug(f"Processing log entry add: {event.log_info.id}")

    async def process_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        """Process a log entry update event."""
        self.logger.debug(f"Processing log entry update: {event.log_info.id}")

    async def process_reply_add(self, event: LogEntryReplyAddEvent) -> None:
        """Process a reply add event."""
        self.logger.debug(f"Processing reply add to: {event.parent_log_info.id}")

    async def process_reply_update(self, event: LogEntryReplyUpdateEvent) -> None:
        """Process a reply update event."""
        self.logger.debug(f"Processing reply update to: {event.parent_log_info.id}")

    async def process_reaction_add(self, event: LogReactionAddEvent) -> None:
        """Process a reaction add event."""
        self.logger.debug(
            f"Processing reaction add: {event.log_reaction.reaction.emoji} "
            f"on log {event.parent_log_info.id}"
        )

    async def process_reaction_delete(self, event: LogReactionDeleteEvent) -> None:
        """Process a reaction delete event."""
        self.logger.debug(
            f"Processing reaction delete: {event.log_reaction.reaction.emoji} "
            f"on log {event.parent_log_info.id}"
        )

    async def process_generic_add(self, event: CoreEvent) -> None:
        """Process a generic add event."""
        self.logger.debug(f"Processing generic add: {event.entity_name}")

    async def process_generic_update(self, event: CoreEvent) -> None:
        """Process a generic update event."""
        self.logger.debug(f"Processing generic update: {event.entity_name}")

    async def process_generic_delete(self, event: CoreEvent) -> None:
        """Process a generic delete event."""
        self.logger.debug(f"Processing generic delete: {event.entity_name}")
