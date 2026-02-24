"""
BELY MQTT Framework - Pluggable Python framework for handling BELY MQTT events.

This framework provides:
- Pluggable handler system for MQTT topics
- Type-safe models for BELY events (CoreEvent, LogEntryAddEvent, etc.)
- Integration with BELY API for additional data
- CLI for easy configuration and management
- Specific event handlers for different event types
"""

from bely_mqtt.events import EventType
from bely_mqtt.models import (
    BaseEvent,
    CoreEvent,
    LogbookInfo,
    LogDocumentInfo,
    LogEntryEventBase,
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryDeleteEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
    LogEntryReplyDeleteEvent,
    LogInfo,
    LogReactionEventBase,
    LogReactionAddEvent,
    LogReactionDeleteEvent,
    LogReactionInfo,
    MQTTMessage,
    ReactionId,
    ReactionInfo,
    TestNotificationEvent,
)
from bely_mqtt.mqtt_client import BelyMQTTClient
from bely_mqtt.plugin import MQTTHandler, PluginManager

__version__ = "0.1.0"

__all__ = [
    "BelyMQTTClient",
    "MQTTHandler",
    "PluginManager",
    "EventType",
    "BaseEvent",
    "CoreEvent",
    "LogEntryEventBase",
    "LogEntryAddEvent",
    "LogEntryUpdateEvent",
    "LogEntryDeleteEvent",
    "LogEntryReplyAddEvent",
    "LogEntryReplyUpdateEvent",
    "LogEntryReplyDeleteEvent",
    "LogReactionEventBase",
    "LogReactionAddEvent",
    "LogReactionDeleteEvent",
    "LogDocumentInfo",
    "LogInfo",
    "LogbookInfo",
    "LogReactionInfo",
    "ReactionInfo",
    "ReactionId",
    "MQTTMessage",
    "TestNotificationEvent",
]
