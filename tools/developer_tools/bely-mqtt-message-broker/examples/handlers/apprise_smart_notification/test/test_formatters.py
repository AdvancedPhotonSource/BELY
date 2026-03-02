"""
Tests for notification formatters.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

# Add parent directory to path for imports
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))

from formatters import NotificationFormatter  # noqa: E402
from bely_mqtt import (  # noqa: E402
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryDeleteEvent,
    LogEntryReplyAddEvent,
    LogReactionAddEvent,
)
from bely_mqtt.models import (  # noqa: E402
    LogDocumentInfo,
    LogInfo,
    LogbookInfo,
    ReactionInfo,
    ReactionId,
    LogReactionInfo,
)


@pytest.fixture
def logger():
    """Create a mock logger."""
    return MagicMock(spec=logging.Logger)


@pytest.fixture
def formatter_utc(logger):
    """Create a formatter with UTC timezone."""
    return NotificationFormatter(bely_url="https://bely.example.com", logger=logger, timezone="UTC")


@pytest.fixture
def formatter_eastern(logger):
    """Create a formatter with Eastern timezone."""
    return NotificationFormatter(
        bely_url="https://bely.example.com", logger=logger, timezone="America/New_York"
    )


@pytest.fixture
def formatter_pacific(logger):
    """Create a formatter with Pacific timezone."""
    return NotificationFormatter(
        bely_url="https://bely.example.com", logger=logger, timezone="America/Los_Angeles"
    )


@pytest.fixture
def sample_log_document_info():
    """Create sample log document info."""
    return LogDocumentInfo(
        name="Test Document", id=123, ownerUsername="doc_owner", createdByUsername="doc_creator"
    )


@pytest.fixture
def sample_log_info():
    """Create sample log info."""
    return LogInfo(id=456, enteredByUsername="entry_author", lastModifiedByUsername="modifier")


@pytest.fixture
def sample_parent_log_info():
    """Create sample parent log info for replies."""
    return LogInfo(
        id=789, enteredByUsername="parent_author", lastModifiedByUsername="parent_modifier"
    )


@pytest.fixture
def sample_logbook_list():
    """Create sample logbook list."""
    return [
        LogbookInfo(name="Logbook1", id=1, displayName="Display 1"),
        LogbookInfo(name="Logbook2", id=2, displayName="Display 2"),
    ]


@pytest.fixture
def sample_reaction_info():
    """Create sample reaction info."""
    return ReactionInfo(
        id=1, name="thumbs_up", emojiCode=128077, emoji="👍", description="Thumbs up"
    )


@pytest.fixture
def sample_log_reaction_info(sample_reaction_info):
    """Create sample log reaction info."""
    return LogReactionInfo(
        reaction=sample_reaction_info,
        id=ReactionId(logId=456, reactionId=1, userId=999),
        username="reactor_user",
    )


class TestTimezoneFormatting:
    """Test timezone formatting functionality."""

    def test_utc_timestamp_formatting(self, formatter_utc):
        """Test that UTC timestamps are formatted correctly."""
        # Create a UTC timestamp
        utc_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

        formatted = formatter_utc._format_timestamp(utc_time)

        # Should show UTC time
        assert "2024-01-15 14:30:45" in formatted
        assert "UTC" in formatted

    def test_eastern_timezone_formatting(self, formatter_eastern):
        """Test that timestamps are converted to Eastern timezone."""
        # Create a UTC timestamp (2:30 PM UTC)
        utc_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

        formatted = formatter_eastern._format_timestamp(utc_time)

        # Should show Eastern time (9:30 AM EST, UTC-5)
        assert "2024-01-15 09:30:45" in formatted
        assert "EST" in formatted or "EDT" in formatted

    def test_pacific_timezone_formatting(self, formatter_pacific):
        """Test that timestamps are converted to Pacific timezone."""
        # Create a UTC timestamp (2:30 PM UTC)
        utc_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

        formatted = formatter_pacific._format_timestamp(utc_time)

        # Should show Pacific time (6:30 AM PST, UTC-8)
        assert "2024-01-15 06:30:45" in formatted
        assert "PST" in formatted or "PDT" in formatted

    def test_naive_timestamp_assumes_utc(self, formatter_eastern):
        """Test that naive timestamps are assumed to be UTC."""
        # Create a naive timestamp (no timezone info)
        naive_time = datetime(2024, 1, 15, 14, 30, 45)

        formatted = formatter_eastern._format_timestamp(naive_time)

        # Should treat as UTC and convert to Eastern (9:30 AM EST)
        assert "2024-01-15 09:30:45" in formatted

    def test_daylight_saving_time(self, formatter_eastern):
        """Test that daylight saving time is handled correctly."""
        # Summer date (EDT - Eastern Daylight Time, UTC-4)
        summer_time = datetime(2024, 7, 15, 14, 30, 45, tzinfo=timezone.utc)
        formatted_summer = formatter_eastern._format_timestamp(summer_time)
        assert "2024-07-15 10:30:45" in formatted_summer  # UTC-4

        # Winter date (EST - Eastern Standard Time, UTC-5)
        winter_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)
        formatted_winter = formatter_eastern._format_timestamp(winter_time)
        assert "2024-01-15 09:30:45" in formatted_winter  # UTC-5

    def test_invalid_timezone_falls_back_to_utc(self, logger):
        """Test that invalid timezone falls back to UTC."""
        formatter = NotificationFormatter(
            bely_url="https://bely.example.com", logger=logger, timezone="Invalid/Timezone"
        )

        # Should have logged a warning
        logger.warning.assert_called()

        # Should use UTC
        utc_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)
        formatted = formatter._format_timestamp(utc_time)
        assert "2024-01-15 14:30:45 UTC" in formatted

    def test_no_timezone_specified(self, logger):
        """Test formatter with no timezone specified (uses local or UTC)."""
        formatter = NotificationFormatter(bely_url="https://bely.example.com", logger=logger)

        # Should have a timezone set (either local or UTC)
        assert formatter.timezone is not None

        # Should be able to format timestamps
        utc_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)
        formatted = formatter._format_timestamp(utc_time)
        assert "2024-01-15" in formatted
        assert ":" in formatted  # Has time component


class TestEventFormatting:
    """Test event formatting with timezone support."""

    def test_entry_added_with_timezone(
        self, formatter_eastern, sample_log_document_info, sample_log_info, sample_logbook_list
    ):
        """Test that LogEntryAddEvent uses timezone formatting."""
        event = LogEntryAddEvent(
            description="Test entry added",
            eventTimestamp=datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc),
            entityName="Log",
            entityId=123,
            eventTriggedByUsername="test_user",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            logbookList=sample_logbook_list,
            textDiff="This is the entry content",
        )

        result = formatter_eastern.format_entry_added(event)

        # Check that Eastern time is shown (9:30 AM EST)
        assert "2024-01-15 09:30:45" in result
        assert "test_user" in result
        assert "Test Document" in result

    def test_entry_updated_with_timezone(
        self, formatter_pacific, sample_log_document_info, sample_log_info, sample_logbook_list
    ):
        """Test that LogEntryUpdateEvent uses timezone formatting."""
        event = LogEntryUpdateEvent(
            description="Test entry updated",
            eventTimestamp=datetime(2024, 7, 15, 18, 45, 30, tzinfo=timezone.utc),
            entityName="Log",
            entityId=123,
            eventTriggedByUsername="updater",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            logbookList=sample_logbook_list,
            textDiff="Updated content",
        )

        result = formatter_pacific.format_entry_updated(event)

        # Check that Pacific time is shown (11:45 AM PDT, UTC-7 in summer)
        assert "2024-07-15 11:45:30" in result
        assert "updater" in result

    def test_reply_added_with_timezone(
        self,
        formatter_eastern,
        sample_log_document_info,
        sample_log_info,
        sample_parent_log_info,
        sample_logbook_list,
    ):
        """Test that LogEntryReplyAddEvent uses timezone formatting."""
        event = LogEntryReplyAddEvent(
            description="Reply added",
            eventTimestamp=datetime(2024, 3, 10, 22, 15, 0, tzinfo=timezone.utc),
            entityName="LogReply",
            entityId=999,
            eventTriggedByUsername="replier",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            parentLogInfo=sample_parent_log_info,
            logbookList=sample_logbook_list,
            textDiff="Reply content",
        )

        result = formatter_eastern.format_reply_added(event)

        # Check that Eastern time is shown (6:15 PM EDT, UTC-4 in March after DST)
        assert "2024-03-10 18:15:00" in result
        assert "replier" in result

    def test_reaction_added_with_timezone(
        self,
        formatter_utc,
        sample_log_document_info,
        sample_parent_log_info,
        sample_log_reaction_info,
    ):
        """Test that LogReactionAddEvent uses timezone formatting."""
        event = LogReactionAddEvent(
            description="Reaction added",
            eventTimestamp=datetime(2024, 12, 25, 10, 0, 0, tzinfo=timezone.utc),
            entityName="LogReaction",
            entityId={"logId": 456, "reactionId": 1, "userId": 999},
            eventTriggedByUsername="reactor",
            parentLogInfo=sample_parent_log_info,
            parentLogDocumentInfo=sample_log_document_info,
            logReaction=sample_log_reaction_info,
        )

        result = formatter_utc.format_reaction_added(event)

        # Check that UTC time is shown
        assert "2024-12-25 10:00:00 UTC" in result
        assert "reactor" in result
        assert "👍" in result

    def test_entry_deleted_with_timezone(
        self, formatter_eastern, sample_log_document_info, sample_log_info, sample_logbook_list
    ):
        """Test that LogEntryDeleteEvent uses timezone formatting."""
        event = LogEntryDeleteEvent(
            description="Entry deleted",
            eventTimestamp=datetime(2024, 6, 1, 3, 30, 15, tzinfo=timezone.utc),
            entityName="Log",
            entityId=123,
            eventTriggedByUsername="deleter",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            logbookList=sample_logbook_list,
            textDiff="Deleted content",
        )

        result = formatter_eastern.format_entry_deleted(event)

        # Check that Eastern time is shown (11:30 PM EDT previous day, UTC-4 in June)
        assert "2024-05-31 23:30:15" in result
        assert "deleter" in result

    def test_multiple_events_same_formatter(
        self, formatter_eastern, sample_log_document_info, sample_log_info, sample_logbook_list
    ):
        """Test that the same formatter consistently formats times in the same timezone."""
        # Create multiple events with different UTC times
        event1 = LogEntryAddEvent(
            description="Morning entry",
            eventTimestamp=datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc),
            entityName="Log",
            entityId=1,
            eventTriggedByUsername="user1",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            logbookList=sample_logbook_list,
            textDiff="Morning content",
        )

        event2 = LogEntryAddEvent(
            description="Afternoon entry",
            eventTimestamp=datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc),
            entityName="Log",
            entityId=2,
            eventTriggedByUsername="user2",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            logbookList=sample_logbook_list,
            textDiff="Afternoon content",
        )

        event3 = LogEntryAddEvent(
            description="Evening entry",
            eventTimestamp=datetime(2024, 1, 15, 23, 0, 0, tzinfo=timezone.utc),
            entityName="Log",
            entityId=3,
            eventTriggedByUsername="user3",
            parentLogDocumentInfo=sample_log_document_info,
            logInfo=sample_log_info,
            logbookList=sample_logbook_list,
            textDiff="Evening content",
        )

        result1 = formatter_eastern.format_entry_added(event1)
        result2 = formatter_eastern.format_entry_added(event2)
        result3 = formatter_eastern.format_entry_added(event3)

        # All should be in Eastern time
        assert "03:00:00" in result1  # 8 AM UTC = 3 AM EST
        assert "10:00:00" in result2  # 3 PM UTC = 10 AM EST
        assert "18:00:00" in result3  # 11 PM UTC = 6 PM EST

        # All should show EST
        assert "EST" in result1 or "EDT" in result1
        assert "EST" in result2 or "EDT" in result2
        assert "EST" in result3 or "EDT" in result3


class TestFormatterInitialization:
    """Test formatter initialization with different timezone configurations."""

    def test_formatter_with_valid_timezone(self, logger):
        """Test creating formatter with valid timezone."""
        formatter = NotificationFormatter(
            bely_url="https://bely.example.com", logger=logger, timezone="Europe/London"
        )

        assert formatter.timezone == ZoneInfo("Europe/London")

        # Test formatting
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        formatted = formatter._format_timestamp(utc_time)
        assert "12:00:00" in formatted  # Same as UTC in January (no DST)

    def test_formatter_with_asia_timezone(self, logger):
        """Test creating formatter with Asian timezone."""
        formatter = NotificationFormatter(
            bely_url="https://bely.example.com", logger=logger, timezone="Asia/Tokyo"
        )

        assert formatter.timezone == ZoneInfo("Asia/Tokyo")

        # Test formatting
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        formatted = formatter._format_timestamp(utc_time)
        assert "21:00:00" in formatted  # UTC+9 for Tokyo

    def test_formatter_with_australia_timezone(self, logger):
        """Test creating formatter with Australian timezone."""
        formatter = NotificationFormatter(
            bely_url="https://bely.example.com", logger=logger, timezone="Australia/Sydney"
        )

        assert formatter.timezone == ZoneInfo("Australia/Sydney")

        # Test formatting
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        formatted = formatter._format_timestamp(utc_time)
        assert "23:00:00" in formatted  # UTC+11 for Sydney in January (summer)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
