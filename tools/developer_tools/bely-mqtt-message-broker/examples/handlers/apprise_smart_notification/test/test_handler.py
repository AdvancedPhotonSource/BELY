"""
Comprehensive test suite for Apprise Smart Notification Handler.

Tests all event types and notification scenarios with mock data.
"""

import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import yaml
import sys

# Add src directory to path to import bely_mqtt
src_path = Path(__file__).parent.parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Mock apprise before importing handler
mock_apprise = MagicMock()
sys.modules["apprise"] = mock_apprise

from bely_mqtt import (  # noqa: E402
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryDeleteEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
    LogEntryReplyDeleteEvent,
    LogReactionAddEvent,
    LogReactionDeleteEvent,
)
from bely_mqtt.models import (  # noqa: E402
    LogInfo,
    LogDocumentInfo,
    LogReactionInfo,
    ReactionInfo,
)
from bely_mqtt.config import GlobalConfig  # noqa: E402

# Add parent directory to path to import handler module
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))

from handler import AppriseSmartNotificationHandler  # noqa: E402


class MockEventFactory:
    """Factory for creating mock events with realistic data."""

    def __init__(self):
        self.timestamp = datetime.now().isoformat()

        # Define three test users for proper notification testing
        self.alice = "alice"  # Document owner
        self.bob = "bob"  # Entry creator (different from document owner)
        self.charlie = "charlie"  # Third party who updates/replies

        # Create mock document owned by Alice
        self.document = self._create_document()

        # Create mock log entries
        self.alice_entry = self._create_log_entry(self.alice, 1)
        self.bob_entry = self._create_log_entry(self.bob, 2)  # Bob's entry in Alice's document
        self.charlie_entry = self._create_log_entry(self.charlie, 3)

    def _create_document(self) -> LogDocumentInfo:
        """Create a mock document owned by Alice."""
        return LogDocumentInfo(
            id=100,
            name="Project Alpha Documentation",
            ownerUsername=self.alice,
            createdByUsername=self.alice,
            lastModifiedByUsername=self.alice,
            enteredOnDateTime=self.timestamp,
            lastModifiedOnDateTime=self.timestamp,
        )

    def _create_log_entry(self, username: str, entry_id: int) -> LogInfo:
        """Create a mock log entry."""
        return LogInfo(
            id=entry_id,
            enteredByUsername=username,
            lastModifiedByUsername=username,
            enteredOnDateTime=self.timestamp,
            lastModifiedOnDateTime=self.timestamp,
        )

    def _create_reaction(self, emoji: str = "👍", name: str = "thumbsup") -> LogReactionInfo:
        """Create a mock reaction."""
        from bely_mqtt.models import ReactionId

        return LogReactionInfo(
            id=ReactionId(logId=1, reactionId=1, userId=2),
            reaction=ReactionInfo(
                id=1,
                emoji=emoji,
                name=name,
                emojiCode=128077,  # Unicode code point for thumbs up
                description=f"Reaction {name}",
            ),
            username=self.bob,
        )

    def create_entry_add_by_bob(self) -> LogEntryAddEvent:
        """Bob adds a new entry to Alice's document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryAddEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.bob,
            entityName="LogEntry",
            entityId=2,
            parentLogDocumentInfo=self.document,
            logInfo=self.bob_entry,
            description="New findings from testing",
            textDiff="+ Added new test results\n+ Performance improved by 20%",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
        )

    def create_entry_update_by_bob_on_alice(self) -> LogEntryUpdateEvent:
        """Bob updates Alice's entry."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryUpdateEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.bob,
            entityName="LogEntry",
            entityId=1,
            parentLogDocumentInfo=self.document,
            logInfo=self.alice_entry,
            description="Corrected typo and added details",
            textDiff="- Old text with typo\n+ New text with correction",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
        )

    def create_entry_update_by_charlie_on_bob(self) -> LogEntryUpdateEvent:
        """Charlie updates Bob's entry in Alice's document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryUpdateEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.charlie,  # Charlie is the third party
            entityName="LogEntry",
            entityId=2,
            parentLogDocumentInfo=self.document,
            logInfo=self.bob_entry,
            description="Added clarification",
            textDiff="+ Added clarification note",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
        )

    def create_reply_add_by_charlie_to_bob(self) -> LogEntryReplyAddEvent:
        """Charlie replies to Bob's entry in Alice's document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryReplyAddEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.charlie,  # Charlie is the third party
            entityName="LogEntryReply",
            entityId=3,
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.bob_entry,  # Replying to Bob's entry
            logInfo=LogInfo(
                id=3,
                enteredByUsername=self.charlie,
                lastModifiedByUsername=self.charlie,
                enteredOnDateTime=self.timestamp,
                lastModifiedOnDateTime=self.timestamp,
            ),
            textDiff="Great point! I agree with this approach.",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
            description="Reply to Bob's entry",
        )

    def create_reply_add_by_alice_to_bob(self) -> LogEntryReplyAddEvent:
        """Alice replies to Bob's entry in her document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryReplyAddEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.alice,
            entityName="LogEntryReply",
            entityId=4,
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.bob_entry,
            logInfo=LogInfo(
                id=4,
                enteredByUsername=self.alice,
                lastModifiedByUsername=self.alice,
                enteredOnDateTime=self.timestamp,
                lastModifiedOnDateTime=self.timestamp,
            ),
            textDiff="Thanks for the update. Please also check the API docs.",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
            description="Reply to Bob's entry",
        )

    def create_reply_update_by_charlie_on_bob_entry(self) -> LogEntryReplyUpdateEvent:
        """Charlie updates a reply on Bob's entry in Alice's document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryReplyUpdateEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.charlie,  # Charlie is updating
            entityName="LogEntryReply",
            entityId=3,
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.bob_entry,  # Bob's entry
            logInfo=LogInfo(
                id=3,
                enteredByUsername=self.charlie,  # Charlie originally created this reply
                lastModifiedByUsername=self.charlie,
                enteredOnDateTime=self.timestamp,
                lastModifiedOnDateTime=self.timestamp,
            ),
            textDiff="- Old reply text\n+ Updated reply with more details",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
            description="Updated reply",
        )

    def create_reaction_add_by_bob_to_alice(self) -> LogReactionAddEvent:
        """Bob adds a reaction to Alice's entry."""
        from bely_mqtt.models import ReactionId

        return LogReactionAddEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.bob,
            entityName="LogReaction",
            entityId=ReactionId(logId=1, reactionId=1, userId=2),
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.alice_entry,
            logReaction=self._create_reaction("🎉", "tada"),
            description="Celebrating the achievement",
        )

    def create_reaction_delete_by_bob_from_alice(self) -> LogReactionDeleteEvent:
        """Bob removes a reaction from Alice's entry."""
        from bely_mqtt.models import ReactionId

        return LogReactionDeleteEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.bob,
            entityName="LogReaction",
            entityId=ReactionId(logId=1, reactionId=1, userId=2),
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.alice_entry,
            logReaction=self._create_reaction("👍", "thumbsup"),
            description="Removing thumbsup",
        )

    def create_self_reaction_by_alice(self) -> LogReactionAddEvent:
        """Alice adds a reaction to her own entry (should not notify)."""
        from bely_mqtt.models import ReactionId

        return LogReactionAddEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.alice,
            entityName="LogReaction",
            entityId=ReactionId(logId=1, reactionId=2, userId=1),
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.alice_entry,
            logReaction=self._create_reaction("✅", "check"),
            description="Marking as complete",
        )

    def create_entry_delete_by_bob_on_alice(self) -> LogEntryDeleteEvent:
        """Bob deletes Alice's entry."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryDeleteEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.bob,
            entityName="LogEntry",
            entityId=1,
            parentLogDocumentInfo=self.document,
            logInfo=self.alice_entry,
            description="Deleted outdated entry",
            textDiff="- Deleted content: This was the original entry text",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
        )

    def create_entry_delete_by_charlie_on_bob(self) -> LogEntryDeleteEvent:
        """Charlie deletes Bob's entry in Alice's document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryDeleteEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.charlie,
            entityName="LogEntry",
            entityId=2,
            parentLogDocumentInfo=self.document,
            logInfo=self.bob_entry,
            description="Removed duplicate entry",
            textDiff="- Deleted content: Bob's test results",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
        )

    def create_reply_delete_by_charlie_on_bob_entry(self) -> LogEntryReplyDeleteEvent:
        """Charlie deletes a reply on Bob's entry in Alice's document."""
        from bely_mqtt.models import LogbookInfo

        return LogEntryReplyDeleteEvent(
            eventTimestamp=self.timestamp,
            eventTriggedByUsername=self.charlie,
            entityName="LogEntryReply",
            entityId=3,
            parentLogDocumentInfo=self.document,
            parentLogInfo=self.bob_entry,
            logInfo=LogInfo(
                id=3,
                enteredByUsername=self.charlie,
                lastModifiedByUsername=self.charlie,
                enteredOnDateTime=self.timestamp,
                lastModifiedOnDateTime=self.timestamp,
            ),
            textDiff="- Deleted reply: This comment is no longer relevant",
            logbookList=[LogbookInfo(id=1, name="Project Alpha", displayName="Project Alpha")],
            description="Deleted outdated reply",
        )


class TestAppriseSmartNotificationHandler:
    """Test suite for AppriseSmartNotificationHandler."""

    @pytest.fixture
    def mock_factory(self):
        """Provide a mock event factory."""
        return MockEventFactory()

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file for testing."""
        config = {
            "global": {
                "mail_server": {
                    "host": "smtp.example.com",
                    "port": 587,
                    "username": "notifications@example.com",
                    "password": "secret123",
                    "use_tls": True,
                }
            },
            "users": {
                "alice": {
                    "apprise_urls": [
                        "mailto://alice@example.com",
                        "discord://webhook_id/webhook_token",
                    ],
                    "notifications": {
                        "entry_updates": True,
                        "own_entry_edits": True,
                        "entry_replies": True,
                        "new_entries": True,
                        "reactions": True,
                        "document_replies": True,
                    },
                },
                "bob": {
                    "apprise_urls": [
                        "mailto://bob@example.com",
                        "slack://TokenA/TokenB/TokenC/",
                    ],
                    "notifications": {
                        "entry_updates": True,
                        "own_entry_edits": True,
                        "entry_replies": True,
                        "new_entries": False,  # Bob doesn't want new entry notifications
                        "reactions": False,  # Bob doesn't want reaction notifications
                        "document_replies": True,
                    },
                },
                "charlie": {
                    "apprise_urls": [
                        "mailto://charlie@example.com",
                        "teams://webhook_url",
                    ],
                    "notifications": {
                        "entry_updates": True,
                        "own_entry_edits": True,
                        "entry_replies": True,
                        "new_entries": True,
                        "reactions": True,
                        "document_replies": True,
                    },
                },
            },
        }

        config_path = tmp_path / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    @pytest.fixture
    def handler(self, config_file):
        """Create a handler instance with mocked Apprise."""
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        # Mock AppriseWithEmailHeaders class
        mock_apprise_wrapper = MagicMock()
        mock_apprise_wrapper.return_value.notify = MagicMock(return_value=True)
        mock_apprise_wrapper.return_value.add = MagicMock(return_value=True)
        mock_apprise_wrapper.return_value.__bool__ = MagicMock(return_value=True)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_wrapper):
            handler = AppriseSmartNotificationHandler(
                config_path=str(config_file), global_config=global_config
            )

            # Mock the notify method for all user instances
            for username, apobj in handler.processor.user_apprise_instances.items():
                apobj.notify = MagicMock(return_value=True)

            return handler

    @pytest.mark.asyncio
    async def test_entry_add_by_collaborator(self, handler, mock_factory):
        """Test: Bob adds entry to Alice's document -> Alice gets notified."""
        event = mock_factory.create_entry_add_by_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_add(event)

            # Alice should be notified about new entry in her document
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "alice"
            # Alice has email configured, so should get email-style subject
            assert "Re: Log: Project Alpha Documentation" in call_args[0][1]
            assert "bob" in call_args[0][1] or "bob" in call_args[0][2]
            assert "Performance improved by 20%" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_entry_update_by_collaborator(self, handler, mock_factory):
        """Test: Bob updates Alice's entry -> Alice gets notified (deduped as she's both owner & creator)."""
        event = mock_factory.create_entry_update_by_bob_on_alice()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_update(event)

            # Should send 1 notification (deduplicated since Alice is both owner and creator)
            assert mock_send.call_count == 1

            # Check notification
            call_args = mock_send.call_args
            assert call_args[0][0] == "alice"  # As both owner and original creator

            # Verify notification content
            assert "bob" in call_args[0][2]
            assert "typo" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_entry_update_by_owner(self, handler, mock_factory):
        """Test: Charlie updates Bob's entry in Alice's document -> Both Alice and Bob get notified."""
        event = mock_factory.create_entry_update_by_charlie_on_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_update(event)

            # Bob should be notified his entry was edited
            # Alice should also be notified as document owner
            assert mock_send.call_count == 2

            calls = mock_send.call_args_list
            usernames = [call[0][0] for call in calls]
            assert "bob" in usernames
            assert "alice" in usernames

    @pytest.mark.asyncio
    async def test_reply_add_by_collaborator(self, handler, mock_factory):
        """Test: Charlie replies to Bob's entry in Alice's document -> Both Alice and Bob get notified."""
        event = mock_factory.create_reply_add_by_charlie_to_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_reply_add(event)

            # Bob gets notified as entry creator
            # Alice gets notified as document owner
            assert mock_send.call_count == 2

            calls = mock_send.call_args_list
            usernames = [call[0][0] for call in calls]
            assert "bob" in usernames  # Entry creator
            assert "alice" in usernames  # Document owner

            # Check notification content
            for call in calls:
                assert "charlie" in call[0][2].lower()

    @pytest.mark.asyncio
    async def test_reply_add_by_owner(self, handler, mock_factory):
        """Test: Alice replies to Bob's entry in her own document -> Bob gets notified."""
        event = mock_factory.create_reply_add_by_alice_to_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_reply_add(event)

            # Only Bob should be notified as entry creator
            # Alice doesn't get notified (she's the one replying to her own document)
            assert mock_send.call_count == 1

            call_args = mock_send.call_args
            assert call_args[0][0] == "bob"
            assert "alice" in call_args[0][2].lower()

    @pytest.mark.asyncio
    async def test_reply_update(self, handler, mock_factory):
        """Test: Charlie updates reply on Bob's entry in Alice's document -> Both Alice and Bob get notified."""
        event = mock_factory.create_reply_update_by_charlie_on_bob_entry()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_reply_update(event)

            # Bob should be notified as entry creator
            # Alice should be notified as document owner
            assert mock_send.call_count == 2

            calls = mock_send.call_args_list
            usernames = [call[0][0] for call in calls]
            assert "bob" in usernames  # Entry creator
            assert "alice" in usernames  # Document owner

            # Check that charlie is mentioned in notifications
            for call in calls:
                assert "charlie" in call[0][2].lower()

    @pytest.mark.asyncio
    async def test_reaction_add(self, handler, mock_factory):
        """Test: Bob adds reaction to Alice's entry -> Alice gets notified."""
        event = mock_factory.create_reaction_add_by_bob_to_alice()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_reaction_add(event)

            # Alice should be notified about the reaction
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "alice"
            # Alice has email configured, so should get email-style subject with action
            assert "Re: Log: Project Alpha Documentation" in call_args[0][1]
            assert "bob" in call_args[0][1]  # Action by bob should be in subject
            assert "🎉" in call_args[0][2]
            assert "tada" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_reaction_delete(self, handler, mock_factory):
        """Test: Bob removes reaction from Alice's entry -> Alice gets notified."""
        event = mock_factory.create_reaction_delete_by_bob_from_alice()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_reaction_delete(event)

            # Alice should be notified about the reaction removal
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "alice"
            # Alice has email configured, so should get email-style subject with action
            assert "Re: Log: Project Alpha Documentation" in call_args[0][1]
            assert "bob" in call_args[0][1]  # Action by bob should be in subject
            assert "👍" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_self_reaction_no_notification(self, handler, mock_factory):
        """Test: Alice reacts to her own entry -> No notification sent."""
        event = mock_factory.create_self_reaction_by_alice()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_reaction_add(event)

            # No notification should be sent for self-reactions
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_settings_respected(self, handler, mock_factory):
        """Test: Notification settings are respected (Bob has reactions disabled)."""
        from bely_mqtt.models import ReactionId, LogReactionInfo, ReactionInfo

        # Create a reaction event where Alice reacts to Bob's entry
        event = LogReactionAddEvent(
            eventTimestamp=mock_factory.timestamp,
            eventTriggedByUsername="alice",
            entityName="LogReaction",
            entityId=ReactionId(logId=2, reactionId=3, userId=1),
            parentLogDocumentInfo=mock_factory.document,
            parentLogInfo=mock_factory.bob_entry,  # Bob's entry
            logReaction=LogReactionInfo(
                id=ReactionId(logId=2, reactionId=3, userId=1),
                reaction=ReactionInfo(
                    id=3, emoji="💯", name="100", emojiCode=128175, description="Perfect"
                ),
                username="alice",
            ),
            description="Perfect solution!",
        )

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_reaction_add(event)

            # Bob has reactions disabled, so no notification
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_permalink_generation(self, handler, mock_factory):
        """Test: Permalinks are correctly generated in notifications."""
        event = mock_factory.create_entry_add_by_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_add(event)

            call_args = mock_send.call_args
            body = call_args[0][2]

            # Check for permalink
            assert "https://bely.example.com/views/item/view?id=100&logId=2" in body
            assert "View entry:" in body

    @pytest.mark.asyncio
    async def test_trigger_description(self, handler, mock_factory):
        """Test: Trigger descriptions are included in notifications."""
        event = mock_factory.create_entry_add_by_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_add(event)

            call_args = mock_send.call_args
            body = call_args[0][2]

            # Check for trigger description
            assert "This notification was sent because" in body
            assert "bob" in body
            assert "new_entries" in body

    @pytest.mark.asyncio
    async def test_error_handling(self, handler, mock_factory):
        """Test: Errors are handled gracefully without crashing."""
        event = mock_factory.create_entry_add_by_bob()

        # Mock the logger
        with patch.object(handler, "logger") as mock_logger:
            # Simulate an error in send_notification
            with patch.object(
                handler.processor, "send_notification", side_effect=Exception("Network error")
            ):
                # Should not raise an exception
                await handler.handle_log_entry_add(event)

                # Check that error was logged
                assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_entry_delete_by_collaborator(self, handler, mock_factory):
        """Test: Bob deletes Alice's entry -> Alice gets notified."""
        event = mock_factory.create_entry_delete_by_bob_on_alice()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_delete(event)

            # Alice should be notified as both owner and original creator (deduplicated)
            assert mock_send.call_count == 1

            call_args = mock_send.call_args
            assert call_args[0][0] == "alice"
            # Alice has email configured, so should get email-style subject
            assert "Re: Log: Project Alpha Documentation" in call_args[0][1]
            assert "[Entry Deleted]" in call_args[0][1]
            assert "bob" in call_args[0][2]
            assert "Deleted content" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_entry_delete_by_third_party(self, handler, mock_factory):
        """Test: Charlie deletes Bob's entry in Alice's document -> Both Alice and Bob get notified."""
        event = mock_factory.create_entry_delete_by_charlie_on_bob()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_delete(event)

            # Bob should be notified his entry was deleted
            # Alice should also be notified as document owner
            assert mock_send.call_count == 2

            calls = mock_send.call_args_list
            usernames = [call[0][0] for call in calls]
            assert "bob" in usernames
            assert "alice" in usernames

            # Check notification content
            for call in calls:
                assert "charlie" in call[0][2].lower()
                assert "deleted" in call[0][2].lower()

    @pytest.mark.asyncio
    async def test_reply_delete(self, handler, mock_factory):
        """Test: Charlie deletes reply on Bob's entry in Alice's document -> Both Alice and Bob get notified."""
        event = mock_factory.create_reply_delete_by_charlie_on_bob_entry()

        with patch.object(
            handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await handler.handle_log_entry_reply_delete(event)

            # Bob should be notified as entry creator
            # Alice should be notified as document owner
            assert mock_send.call_count == 2

            calls = mock_send.call_args_list
            usernames = [call[0][0] for call in calls]
            assert "bob" in usernames  # Entry creator
            assert "alice" in usernames  # Document owner

            # Check that charlie is mentioned in notifications
            for call in calls:
                assert "charlie" in call[0][2].lower()
                assert "deleted" in call[0][2].lower()

    @pytest.mark.asyncio
    async def test_no_config_handler(self):
        """Test: Handler works without config (no notifications sent)."""
        # Mock AppriseWithEmailHeaders class
        mock_apprise_wrapper = MagicMock()
        mock_apprise_wrapper.return_value.notify = MagicMock(return_value=True)
        mock_apprise_wrapper.return_value.add = MagicMock(return_value=True)
        mock_apprise_wrapper.return_value.__bool__ = MagicMock(return_value=True)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_wrapper):
            # Create handler without config - should not raise an error
            handler = AppriseSmartNotificationHandler()

            # Verify processor has no user configurations
            assert handler.processor.user_apprise_instances == {}

            factory = MockEventFactory()
            event = factory.create_entry_add_by_bob()

            # Should handle event without error even without config
            await handler.handle_log_entry_add(event)

            # Try other event types too - all should work without errors
            await handler.handle_log_entry_update(factory.create_entry_update_by_bob_on_alice())
            await handler.handle_log_entry_reply_add(factory.create_reply_add_by_charlie_to_bob())
            await handler.handle_log_reaction_add(factory.create_reaction_add_by_bob_to_alice())
            await handler.handle_log_entry_delete(factory.create_entry_delete_by_bob_on_alice())
            await handler.handle_log_entry_reply_delete(
                factory.create_reply_delete_by_charlie_on_bob_entry()
            )

            # Verify handler can process events without config
            # (it just won't send notifications)


class TestNotificationContent:
    """Test the content and formatting of notifications."""

    @pytest.fixture
    def formatter(self):
        """Create a formatter instance."""
        from formatters import NotificationFormatter

        return NotificationFormatter(
            bely_url="https://bely.example.com", logger=logging.getLogger("test")
        )

    def test_entry_add_formatting(self, formatter):
        """Test formatting of entry add notifications."""
        factory = MockEventFactory()
        event = factory.create_entry_add_by_bob()

        body = formatter.format_entry_added(event)

        assert "New entry added to Project Alpha Documentation" in body
        assert "By: bob" in body
        assert "Performance improved by 20%" in body
        assert "<pre" in body  # Check for formatted text diff

    def test_reaction_formatting(self, formatter):
        """Test formatting of reaction notifications."""
        factory = MockEventFactory()
        event = factory.create_reaction_add_by_bob_to_alice()

        body = formatter.format_reaction_added(event)

        assert "New reaction added to entry" in body
        assert "By: bob" in body
        assert "🎉 tada" in body
        assert "Celebrating the achievement" in body

    def test_html_escaping(self, formatter):
        """Test that HTML in user content is properly handled."""
        factory = MockEventFactory()
        event = factory.create_entry_add_by_bob()
        event.text_diff = "<script>alert('xss')</script>"

        body = formatter.format_entry_added(event)

        # The script tag should be in a pre block, not executed
        assert "<pre" in body
        assert "<script>alert('xss')</script>" in body


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
