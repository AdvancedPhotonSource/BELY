"""
Data models for BELY MQTT events.

These models are designed to be mappable to MQTT messages from BELY.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogbookInfo(BaseModel):
    """Information about a logbook."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    id: int
    display_name: Optional[str] = Field(None, alias="displayName")


class UserInfo(BaseModel):
    """Basic user information."""

    username: str


class LogDocumentInfo(BaseModel):
    """Information about a log document."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    id: int
    last_modified_on_date_time: Optional[datetime] = Field(None, alias="lastModifiedOnDateTime")
    created_by_username: Optional[str] = Field(None, alias="createdByUsername")
    last_modified_by_username: Optional[str] = Field(None, alias="lastModifiedByUsername")
    entered_on_date_time: Optional[datetime] = Field(None, alias="enteredOnDateTime")
    owner_username: Optional[str] = Field(None, alias="ownerUsername")
    owner_user_group_name: Optional[str] = Field(None, alias="ownerUserGroupName")


class LogInfo(BaseModel):
    """Information about a log entry."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    last_modified_on_date_time: Optional[datetime] = Field(None, alias="lastModifiedOnDateTime")
    last_modified_by_username: Optional[str] = Field(None, alias="lastModifiedByUsername")
    entered_by_username: Optional[str] = Field(None, alias="enteredByUsername")
    entered_on_date_time: Optional[datetime] = Field(None, alias="enteredOnDateTime")


class BaseEvent(BaseModel):
    """Base class for all BELY MQTT events.

    Note: entity_id can be either an integer (for most events) or a composite
    object like ReactionId (for log reaction events).
    """

    model_config = ConfigDict(populate_by_name=True)

    description: str
    event_timestamp: datetime = Field(alias="eventTimestamp")
    entity_name: str = Field(alias="entityName")
    entity_id: Any = Field(alias="entityId")  # Can be int or composite object
    event_triggered_by_username: str = Field(alias="eventTriggedByUsername")


class CoreEvent(BaseEvent):
    """Core event with minimal information (add/update/delete)."""

    pass


class LogEntryEventBase(BaseEvent):
    """Base class for log entry events with common fields."""

    parent_log_document_info: LogDocumentInfo = Field(alias="parentLogDocumentInfo")
    log_info: LogInfo = Field(alias="logInfo")
    logbook_list: List[LogbookInfo] = Field(alias="logbookList")
    text_diff: str = Field(alias="textDiff")


class LogEntryAddEvent(LogEntryEventBase):
    """Event triggered when a log entry is added."""

    pass


class LogEntryUpdateEvent(LogEntryEventBase):
    """Event triggered when a log entry is updated."""

    pass


class LogEntryDeleteEvent(LogEntryEventBase):
    """Event triggered when a log entry is deleted."""

    pass


class LogEntryReplyAddEvent(LogEntryEventBase):
    """Event triggered when a reply to a log entry is added."""

    parent_log_info: LogInfo = Field(alias="parentLogInfo")


class LogEntryReplyUpdateEvent(LogEntryEventBase):
    """Event triggered when a reply to a log entry is updated."""

    parent_log_info: LogInfo = Field(alias="parentLogInfo")


class LogEntryReplyDeleteEvent(LogEntryEventBase):
    """Event triggered when a reply to a log entry is deleted."""

    parent_log_info: LogInfo = Field(alias="parentLogInfo")


class ReactionInfo(BaseModel):
    """Information about a reaction."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    emoji_code: int = Field(alias="emojiCode")
    description: Optional[str] = None
    emoji: str


class ReactionId(BaseModel):
    """Composite ID for a reaction (log ID, reaction ID, user ID)."""

    model_config = ConfigDict(populate_by_name=True)

    log_id: int = Field(alias="logId")
    reaction_id: int = Field(alias="reactionId")
    user_id: int = Field(alias="userId")


class LogReactionInfo(BaseModel):
    """Information about a log reaction."""

    model_config = ConfigDict(populate_by_name=True)

    reaction: ReactionInfo
    id: ReactionId
    username: str


class LogReactionEventBase(BaseEvent):
    """Base class for log reaction events with common fields."""

    parent_log_info: LogInfo = Field(alias="parentLogInfo")
    parent_log_document_info: LogDocumentInfo = Field(alias="parentLogDocumentInfo")
    log_reaction: LogReactionInfo = Field(alias="logReaction")


class LogReactionAddEvent(LogReactionEventBase):
    """Event triggered when a reaction is added to a log entry."""

    pass


class LogReactionDeleteEvent(LogReactionEventBase):
    """Event triggered when a reaction is deleted from a log entry."""

    pass


class MQTTMessage(BaseModel):
    """Wrapper for an MQTT message with topic and payload."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    topic: str
    payload: Dict[str, Any]
    raw_payload: str = ""
