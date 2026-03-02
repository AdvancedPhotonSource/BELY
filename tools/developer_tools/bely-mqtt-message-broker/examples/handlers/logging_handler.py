"""
Example handler that logs all BELY events.

This is a simple example handler that demonstrates how to create
a basic handler that processes MQTT messages.
"""

import json
import logging

from bely_mqtt.models import MQTTMessage
from bely_mqtt.plugin import MQTTHandler

logger = logging.getLogger(__name__)


class LoggingHandler(MQTTHandler):
    """
    Simple handler that logs all BELY events.
    
    This handler subscribes to all BELY topics and logs the events
    to the standard logging system.
    """

    @property
    def topic_pattern(self) -> str:
        """Subscribe to all BELY topics."""
        return "bely/#"

    async def handle(self, message: MQTTMessage) -> None:
        """Log the incoming message."""
        self.logger.info(f"Event received on topic: {message.topic}")
        self.logger.debug(f"Payload: {json.dumps(message.payload, indent=2)}")
