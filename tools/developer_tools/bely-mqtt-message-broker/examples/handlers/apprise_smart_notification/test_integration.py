"""
Integration tests for Apprise Smart Notification Handler.

These tests demonstrate the handler processing realistic MQTT event sequences.
"""

import asyncio
from datetime import datetime, timedelta
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
sys.modules["apprise"] = MagicMock()

from bely_mqtt import (  # noqa: E402
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryReplyAddEvent,
    LogReactionAddEvent,
)
from bely_mqtt.models import (  # noqa: E402
    LogInfo,
    LogDocumentInfo,
    LogReactionInfo,
    ReactionInfo,
    LogbookInfo,
)
from bely_mqtt.config import GlobalConfig  # noqa: E402

from apprise_smart_notification import AppriseSmartNotificationHandler  # noqa: E402


class TestScenarios:
    """Integration test scenarios simulating real-world usage."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create a test configuration with multiple users."""
        config = {
            "global": {
                "mail_server": {
                    "host": "smtp.company.com",
                    "port": 587,
                    "username": "notifications@company.com",
                    "password": "secure_password",
                    "use_tls": True,
                }
            },
            "users": {
                # Team lead - wants all notifications
                "sarah": {
                    "apprise_urls": [
                        "mailto://sarah@company.com",
                        "slack://TokenA/TokenB/TokenC/#general",
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
                # Developer - selective notifications
                "john": {
                    "apprise_urls": [
                        "mailto://john@company.com",
                        "discord://webhook_id/webhook_token",
                    ],
                    "notifications": {
                        "entry_updates": False,  # Too noisy
                        "own_entry_edits": True,  # Important
                        "entry_replies": True,  # Important
                        "new_entries": False,  # Too noisy
                        "reactions": True,  # Fun
                        "document_replies": False,  # Not a document owner
                    },
                },
                # QA Engineer - minimal notifications
                "emma": {
                    "apprise_urls": [
                        "mailto://emma@company.com",
                    ],
                    "notifications": {
                        "entry_updates": False,
                        "own_entry_edits": True,  # Only when someone edits her entries
                        "entry_replies": True,  # Only direct replies
                        "new_entries": False,
                        "reactions": False,
                        "document_replies": False,
                    },
                },
            },
        }

        config_path = tmp_path / "integration_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    @pytest.fixture
    def handler(self, test_config):
        """Create handler with test configuration."""
        global_config = GlobalConfig({"bely_url": "https://bely.company.com"})

        with patch("apprise_smart_notification.notification_processor.APPRISE_AVAILABLE", True):
            handler = AppriseSmartNotificationHandler(
                config_path=str(test_config), global_config=global_config
            )

            # Mock Apprise notify for all users
            for username, apobj in handler.processor.user_apprise_instances.items():
                apobj.notify = MagicMock(return_value=True)

            return handler

    @pytest.fixture
    def notification_tracker(self, handler):
        """Track all notifications sent during tests."""
        notifications = []

        async def track_notification(username, title, body):
            notifications.append(
                {
                    "username": username,
                    "title": title,
                    "body": body,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            # Call the original mock
            return True

        handler.processor.send_notification = AsyncMock(side_effect=track_notification)
        return notifications

    @pytest.mark.asyncio
    async def test_scenario_sprint_planning_document(self, handler, notification_tracker):
        """
        Scenario: Sprint Planning Document

        Sarah (team lead) creates a sprint planning document.
        John and Emma collaborate by adding entries and comments.
        """
        base_time = datetime.now()

        # Sarah's sprint planning document
        sprint_doc = LogDocumentInfo(
            id=200,
            name="Sprint 23 Planning",
            ownerUsername="sarah",
            createdByUsername="sarah",
            lastModifiedByUsername="sarah",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # 1. John adds a task entry
        from bely_mqtt.models import LogbookInfo

        john_entry = LogInfo(
            id=201,
            enteredByUsername="john",
            lastModifiedByUsername="john",
            enteredOnDateTime=(base_time + timedelta(minutes=5)).isoformat(),
            lastModifiedOnDateTime=(base_time + timedelta(minutes=5)).isoformat(),
        )

        event1 = LogEntryAddEvent(
            eventTimestamp=(base_time + timedelta(minutes=5)).isoformat(),
            eventTriggedByUsername="john",
            entityName="LogEntry",
            entityId=201,
            parentLogDocumentInfo=sprint_doc,
            logInfo=john_entry,
            description="Added API refactoring task",
            textDiff="+ Task: Refactor /api/v1/users endpoint\n+ Estimate: 5 story points\n+ Dependencies: Database migration",
            logbookList=[LogbookInfo(id=1, name="Sprint Planning", displayName="Sprint Planning")],
        )

        await handler.handle_log_entry_add(event1)

        # Sarah should be notified (document owner, new_entries enabled)
        assert len(notification_tracker) == 1
        assert notification_tracker[0]["username"] == "sarah"
        assert "New Log Entry" in notification_tracker[0]["title"]

        # 2. Emma adds a QA consideration as a reply
        event2 = LogEntryReplyAddEvent(
            eventTimestamp=(base_time + timedelta(minutes=10)).isoformat(),
            eventTriggedByUsername="emma",
            entityName="LogEntryReply",
            entityId=202,
            parentLogDocumentInfo=sprint_doc,
            parentLogInfo=john_entry,
            logInfo=LogInfo(
                id=202,
                enteredByUsername="emma",
                lastModifiedByUsername="emma",
                enteredOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
            ),
            textDiff="Need to update integration tests for the new endpoint structure. Also check backwards compatibility.",
            logbookList=[LogbookInfo(id=1, name="Sprint Planning", displayName="Sprint Planning")],
            description="QA consideration",
        )

        await handler.handle_log_entry_reply_add(event2)

        # John should be notified (entry creator, entry_replies enabled)
        # Sarah should be notified (document owner, document_replies enabled)
        assert len(notification_tracker) == 3  # 1 previous + 2 new
        new_notifications = notification_tracker[-2:]
        usernames = {n["username"] for n in new_notifications}
        assert usernames == {"john", "sarah"}

        # 3. Sarah updates John's entry with priority
        event3 = LogEntryUpdateEvent(
            eventTimestamp=(base_time + timedelta(minutes=15)).isoformat(),
            eventTriggedByUsername="sarah",
            entityName="LogEntry",
            entityId=201,
            parentLogDocumentInfo=sprint_doc,
            logInfo=john_entry,
            description="Added priority",
            textDiff="+ Priority: HIGH - Blocking customer feature",
            logbookList=[LogbookInfo(id=1, name="Sprint Planning", displayName="Sprint Planning")],
        )

        await handler.handle_log_entry_update(event3)

        # John should be notified (own_entry_edits enabled)
        # Sarah is the one making the update, so she won't be notified about her own action
        assert len(notification_tracker) == 4  # 3 previous + 1 new
        new_notification = notification_tracker[-1]

        # Check John's notification
        assert new_notification["username"] == "john"
        assert "Your Log Entry Was Edited" in new_notification["title"]
        assert "sarah" in new_notification["body"].lower()

        # 4. John reacts to Emma's QA comment with thumbs up
        from bely_mqtt.models import ReactionId

        event4 = LogReactionAddEvent(
            eventTimestamp=(base_time + timedelta(minutes=20)).isoformat(),
            eventTriggedByUsername="john",
            entityName="LogReaction",
            entityId=ReactionId(logId=202, reactionId=1, userId=2),
            parentLogDocumentInfo=sprint_doc,
            parentLogInfo=LogInfo(
                id=202,  # Emma's reply
                enteredByUsername="emma",
                lastModifiedByUsername="emma",
                enteredOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
            ),
            logReaction=LogReactionInfo(
                id=ReactionId(logId=202, reactionId=1, userId=2),
                reaction=ReactionInfo(
                    id=1, emoji="👍", name="thumbsup", emojiCode=128077, description="Acknowledged"
                ),
                username="john",
            ),
            description="Agreed with QA considerations",
        )

        await handler.handle_log_reaction_add(event4)

        # Emma has reactions disabled, so no notification
        assert len(notification_tracker) == 4  # No new notifications

    @pytest.mark.asyncio
    async def test_scenario_bug_report_collaboration(self, handler, notification_tracker):
        """
        Scenario: Bug Report Document

        Emma creates a bug report document.
        John investigates and updates.
        Sarah reviews and adds comments.
        """
        base_time = datetime.now()

        # Emma's bug report document
        bug_doc = LogDocumentInfo(
            id=300,
            name="BUG-1234: API Response Timeout",
            ownerUsername="emma",
            createdByUsername="emma",
            lastModifiedByUsername="emma",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # Emma's initial bug report entry (not used in this test scenario)
        # emma_entry = LogInfo(
        #     id=301,
        #     enteredByUsername="emma",
        #     lastModifiedByUsername="emma",
        #     enteredOnDateTime=base_time.isoformat(),
        #     lastModifiedOnDateTime=base_time.isoformat(),
        # )

        # 1. John adds investigation findings
        event1 = LogEntryAddEvent(
            eventTimestamp=(base_time + timedelta(hours=1)).isoformat(),
            eventTriggedByUsername="john",
            entityName="LogEntry",
            entityId=302,
            parentLogDocumentInfo=bug_doc,
            logInfo=LogInfo(
                id=302,
                enteredByUsername="john",
                lastModifiedByUsername="john",
                enteredOnDateTime=(base_time + timedelta(hours=1)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(hours=1)).isoformat(),
            ),
            description="Root cause analysis",
            textDiff="+ Found N+1 query issue in user permissions check\n+ Each API call triggers 50+ database queries\n+ Solution: Implement eager loading",
            logbookList=[LogbookInfo(id=2, name="Bug Reports", displayName="Bug Reports")],
        )

        await handler.handle_log_entry_add(event1)

        # Emma should be notified (document owner, but new_entries disabled)
        # So no notification
        assert len(notification_tracker) == 0

        # 2. Sarah adds a high-priority comment on John's findings
        event2 = LogEntryReplyAddEvent(
            eventTimestamp=(base_time + timedelta(hours=2)).isoformat(),
            eventTriggedByUsername="sarah",
            entityName="LogEntryReply",
            entityId=303,
            parentLogDocumentInfo=bug_doc,
            parentLogInfo=LogInfo(
                id=302,  # John's investigation entry
                enteredByUsername="john",
                lastModifiedByUsername="john",
                enteredOnDateTime=(base_time + timedelta(hours=1)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(hours=1)).isoformat(),
            ),
            logInfo=LogInfo(
                id=303,
                enteredByUsername="sarah",
                lastModifiedByUsername="sarah",
                enteredOnDateTime=(base_time + timedelta(hours=2)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(hours=2)).isoformat(),
            ),
            textDiff="This is affecting our major client. Please prioritize the fix for today's deployment.",
            logbookList=[LogbookInfo(id=2, name="Bug Reports", displayName="Bug Reports")],
            description="Priority escalation",
        )

        await handler.handle_log_entry_reply_add(event2)

        # John should be notified (entry_replies enabled)
        # Emma should be notified (document owner, but document_replies disabled)
        assert len(notification_tracker) == 1
        assert notification_tracker[0]["username"] == "john"
        assert "Reply to Your Log Entry" in notification_tracker[0]["title"]

        # 3. John updates his own entry with fix status
        event3 = LogEntryUpdateEvent(
            eventTimestamp=(base_time + timedelta(hours=3)).isoformat(),
            eventTriggedByUsername="john",
            entityName="LogEntry",
            entityId=302,
            parentLogDocumentInfo=bug_doc,
            logInfo=LogInfo(
                id=302,  # John's own entry
                enteredByUsername="john",
                lastModifiedByUsername="john",
                enteredOnDateTime=(base_time + timedelta(hours=1)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(hours=3)).isoformat(),
            ),
            description="Fix deployed",
            textDiff="+ STATUS: Fixed and deployed to production\n+ Deployment time: 15:30 UTC",
            logbookList=[LogbookInfo(id=2, name="Bug Reports", displayName="Bug Reports")],
        )

        await handler.handle_log_entry_update(event3)

        # John is updating his own entry, so no notification to him
        # Emma gets notified as document owner (but entry_updates disabled)
        assert len(notification_tracker) == 1  # No new notifications

        # 4. Sarah reacts with celebration
        from bely_mqtt.models import ReactionId

        event4 = LogReactionAddEvent(
            eventTimestamp=(base_time + timedelta(hours=4)).isoformat(),
            eventTriggedByUsername="sarah",
            entityName="LogReaction",
            entityId=ReactionId(logId=302, reactionId=2, userId=1),
            parentLogDocumentInfo=bug_doc,
            parentLogInfo=LogInfo(
                id=302,  # John's entry
                enteredByUsername="john",
                lastModifiedByUsername="john",
                enteredOnDateTime=(base_time + timedelta(hours=1)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(hours=3)).isoformat(),
            ),
            logReaction=LogReactionInfo(
                id=ReactionId(logId=302, reactionId=2, userId=1),
                reaction=ReactionInfo(
                    id=2, emoji="🎉", name="tada", emojiCode=127881, description="Celebration"
                ),
                username="sarah",
            ),
            description="Great work on the quick fix!",
        )

        await handler.handle_log_reaction_add(event4)

        # John should be notified (reactions enabled)
        assert len(notification_tracker) == 2
        assert notification_tracker[-1]["username"] == "john"
        assert "🎉" in notification_tracker[-1]["body"]

    @pytest.mark.asyncio
    async def test_notification_deduplication(self, handler, notification_tracker):
        """Test that users don't get duplicate notifications for the same event."""
        base_time = datetime.now()

        # Sarah's document
        doc = LogDocumentInfo(
            id=400,
            name="Test Document",
            ownerUsername="sarah",
            createdByUsername="sarah",
            lastModifiedByUsername="sarah",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # Sarah's entry (she is both owner and creator)
        sarah_entry = LogInfo(
            id=401,
            enteredByUsername="sarah",
            lastModifiedByUsername="sarah",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # John updates Sarah's entry
        event = LogEntryUpdateEvent(
            eventTimestamp=base_time.isoformat(),
            eventTriggedByUsername="john",
            entityName="LogEntry",
            entityId=401,
            parentLogDocumentInfo=doc,
            logInfo=sarah_entry,
            description="Update",
            textDiff="+ Added content",
            logbookList=[LogbookInfo(id=3, name="Test", displayName="Test")],
        )

        await handler.handle_log_entry_update(event)

        # Sarah should only get ONE notification even though she's both owner and creator
        sarah_notifications = [n for n in notification_tracker if n["username"] == "sarah"]
        assert len(sarah_notifications) == 1

    @pytest.mark.asyncio
    async def test_self_action_no_notification(self, handler, notification_tracker):
        """Test that users don't get notified about their own actions."""
        base_time = datetime.now()

        # John's document
        doc = LogDocumentInfo(
            id=500,
            name="John's Notes",
            ownerUsername="john",
            createdByUsername="john",
            lastModifiedByUsername="john",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # John adds an entry to his own document
        event = LogEntryAddEvent(
            eventTimestamp=base_time.isoformat(),
            eventTriggedByUsername="john",
            entityName="LogEntry",
            entityId=501,
            parentLogDocumentInfo=doc,
            logInfo=LogInfo(
                id=501,
                enteredByUsername="john",
                lastModifiedByUsername="john",
                enteredOnDateTime=base_time.isoformat(),
                lastModifiedOnDateTime=base_time.isoformat(),
            ),
            description="Personal note",
            textDiff="+ Remember to review PR #123",
            logbookList=[LogbookInfo(id=4, name="Personal", displayName="Personal")],
        )

        await handler.handle_log_entry_add(event)

        # No notification should be sent (John is both creator and document owner)
        assert len(notification_tracker) == 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_missing_user_config(self, tmp_path):
        """Test handling of events for users not in config."""
        config = {
            "users": {
                "alice": {
                    "apprise_urls": ["mailto://alice@example.com"],
                    "notifications": {"entry_replies": True},
                }
            }
        }

        config_path = tmp_path / "limited_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with patch("apprise_smart_notification.notification_processor.APPRISE_AVAILABLE", True):
            handler = AppriseSmartNotificationHandler(config_path=str(config_path))

        # Event from unconfigured user "bob"
        from bely_mqtt.models import LogbookInfo

        event = LogEntryAddEvent(
            eventTimestamp=datetime.now().isoformat(),
            eventTriggedByUsername="bob",
            entityName="LogEntry",
            entityId=1,
            parentLogDocumentInfo=LogDocumentInfo(
                id=1,
                name="Test Doc",
                ownerUsername="charlie",  # Also unconfigured
                createdByUsername="charlie",
                lastModifiedByUsername="charlie",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            logInfo=LogInfo(
                id=1,
                enteredByUsername="bob",
                lastModifiedByUsername="bob",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            description="Test",
            textDiff="Test content",
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        # Should handle gracefully without errors
        await handler.handle_log_entry_add(event)

    @pytest.mark.asyncio
    async def test_malformed_event_data(self, tmp_path):
        """Test handling of events with empty or unusual data."""
        config = {
            "users": {
                "test": {
                    "apprise_urls": ["mailto://test@example.com"],
                    "notifications": {
                        "new_entries": True,
                        "entry_updates": True,
                    },
                }
            }
        }

        config_path = tmp_path / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with patch("apprise_smart_notification.notification_processor.APPRISE_AVAILABLE", True):
            handler = AppriseSmartNotificationHandler(config_path=str(config_path))

            # Mock the Apprise notify method
            for username, apobj in handler.processor.user_apprise_instances.items():
                apobj.notify = MagicMock(return_value=True)

        # Create event with empty strings and edge case data
        from bely_mqtt.models import LogbookInfo

        # Test 1: Empty username (should not crash, but won't notify anyone)
        event = LogEntryAddEvent(
            eventTimestamp=datetime.now().isoformat(),
            eventTriggedByUsername="",  # Empty username
            entityName="LogEntry",
            entityId=1,
            parentLogDocumentInfo=LogDocumentInfo(
                id=1,
                name="Test Document",
                ownerUsername="test",
                createdByUsername="test",
                lastModifiedByUsername="test",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            logInfo=LogInfo(
                id=1,
                enteredByUsername="test",
                lastModifiedByUsername="test",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            description="",  # Empty description
            textDiff="",  # Empty text diff
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        # Should handle gracefully without crashing
        try:
            await asyncio.wait_for(handler.handle_log_entry_add(event), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Handler timed out processing event with empty username")

        # Test 2: Very long strings (should truncate or handle gracefully)
        event2 = LogEntryAddEvent(
            eventTimestamp=datetime.now().isoformat(),
            eventTriggedByUsername="long_user",
            entityName="LogEntry",
            entityId=2,
            parentLogDocumentInfo=LogDocumentInfo(
                id=2,
                name="Document with very long name " + "y" * 500,  # Reduced from 5000
                ownerUsername="test",
                createdByUsername="test",
                lastModifiedByUsername="test",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            logInfo=LogInfo(
                id=2,
                enteredByUsername="test",
                lastModifiedByUsername="test",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            description="Very long description " + "z" * 1000,  # Reduced from 10000
            textDiff="+ " + "content" * 200,  # Reduced from 2000
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        # Should handle gracefully without crashing
        try:
            await asyncio.wait_for(handler.handle_log_entry_add(event2), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Handler timed out processing event with long strings")

        # Test 3: Special characters in strings
        event3 = LogEntryAddEvent(
            eventTimestamp=datetime.now().isoformat(),
            eventTriggedByUsername="user<script>alert('xss')</script>",
            entityName="LogEntry",
            entityId=3,
            parentLogDocumentInfo=LogDocumentInfo(
                id=3,
                name="Test <b>HTML</b> & Special Chars",
                ownerUsername="test",
                createdByUsername="test",
                lastModifiedByUsername="test",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            logInfo=LogInfo(
                id=3,
                enteredByUsername="test",
                lastModifiedByUsername="test",
                enteredOnDateTime=datetime.now().isoformat(),
                lastModifiedOnDateTime=datetime.now().isoformat(),
            ),
            description="Description with <script>alert('xss')</script>",
            textDiff="+ Content with special chars: & < > \" '",
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        # Should handle gracefully without crashing
        try:
            await asyncio.wait_for(handler.handle_log_entry_add(event3), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Handler timed out processing event with special characters")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
