"""
Test suite for email threading functionality in Apprise Smart Notification Handler.

This module tests the email threading capabilities that ensure email notifications
are properly threaded together in email clients like Gmail, Outlook, and Thunderbird.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import yaml

# Add src directory to path to import bely_mqtt
src_path = Path(__file__).parent.parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Mock apprise before importing handler
sys.modules["apprise"] = MagicMock()

from bely_mqtt import (  # noqa: E402
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryDeleteEvent,
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

# Add parent directory to path for imports
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))

from handler import AppriseSmartNotificationHandler  # noqa: E402
from email_threading import (  # noqa: E402
    EmailThreadingStrategy,
    NotificationEventType,
    detect_event_type,
)


class TestEmailThreadingStrategy:
    """Test the EmailThreadingStrategy class."""

    @pytest.fixture
    def strategy(self):
        """Create an EmailThreadingStrategy instance."""
        return EmailThreadingStrategy(domain="test.example.com")

    def test_email_url_detection(self, strategy):
        """Test detection of email notification URLs."""
        # Email URLs that should be detected
        email_urls = [
            "mailto://user:pass@gmail.com",
            "mailtos://user:pass@mail.example.com:587",
        ]

        # Non-email URLs that should not be detected
        non_email_urls = [
            "slack://TokenA/TokenB/TokenC",
            "discord://webhook_id/webhook_token",
            "telegram://bot_token/chat_id",
            "pushover://user_key@app_token",
            "teams://webhook_url",
        ]

        for url in email_urls:
            assert EmailThreadingStrategy.is_email_notification(
                url
            ), f"Should detect {url} as email"

        for url in non_email_urls:
            assert not EmailThreadingStrategy.is_email_notification(
                url
            ), f"Should not detect {url} as email"

    def test_thread_id_generation(self, strategy):
        """Test generation of consistent thread IDs."""
        document_id = "doc123"
        entry_id = "entry456"

        # Thread IDs should be consistent for the same input
        doc_thread_1 = strategy.generate_document_thread_id(document_id)
        doc_thread_2 = strategy.generate_document_thread_id(document_id)
        assert doc_thread_1 == doc_thread_2
        assert "@test.example.com" in doc_thread_1

        entry_thread_1 = strategy.generate_entry_thread_id(entry_id)
        entry_thread_2 = strategy.generate_entry_thread_id(entry_id)
        assert entry_thread_1 == entry_thread_2
        assert "@test.example.com" in entry_thread_1

        # Different IDs should produce different thread IDs
        assert doc_thread_1 != entry_thread_1

    def test_email_headers_for_document_creation(self, strategy):
        """Test email headers for document creation (starts thread)."""
        headers = strategy.get_email_headers(
            event_type=NotificationEventType.DOCUMENT_CREATE,
            document_id="doc100",
            document_name="Sprint Planning",
        )

        assert "Thread-Topic" in headers
        assert "Sprint Planning" in headers["Thread-Topic"]
        assert "References" in headers
        assert "In-Reply-To" not in headers  # Document creation starts the thread

    def test_email_headers_for_entry_addition(self, strategy):
        """Test email headers for entry addition (replies to document)."""
        headers = strategy.get_email_headers(
            event_type=NotificationEventType.ENTRY_ADD,
            document_id="doc100",
            document_name="Sprint Planning",
            entry_id="entry200",
        )

        assert "Thread-Topic" in headers
        assert "References" in headers
        assert "In-Reply-To" in headers
        assert headers["In-Reply-To"] == strategy.generate_document_thread_id("doc100")
        assert "X-Entry-Id" in headers
        assert headers["X-Entry-Id"] == "entry200"

    def test_email_headers_for_nested_reply(self, strategy):
        """Test email headers for reply to entry (nested threading)."""
        headers = strategy.get_email_headers(
            event_type=NotificationEventType.ENTRY_REPLY,
            document_id="doc100",
            document_name="Sprint Planning",
            entry_id="reply300",
            parent_entry_id="entry200",
        )

        assert "Thread-Topic" in headers
        assert "References" in headers
        assert "In-Reply-To" in headers
        assert headers["In-Reply-To"] == strategy.generate_entry_thread_id("entry200")
        assert "X-Entry-Id" in headers
        assert headers["X-Entry-Id"] == "reply300"
        assert "X-Parent-Entry-Id" in headers
        assert headers["X-Parent-Entry-Id"] == "entry200"

        # References should include both document and parent entry
        references = headers["References"].split()
        assert strategy.generate_document_thread_id("doc100") in references
        assert strategy.generate_entry_thread_id("entry200") in references

    def test_subject_generation_for_email(self, strategy):
        """Test subject line generation for email notifications."""
        document_title = "Q4 Planning Document"

        # Email subjects should use Re: for threading
        subjects = [
            (NotificationEventType.DOCUMENT_CREATE, None, "New Log: Q4 Planning Document"),
            (NotificationEventType.ENTRY_ADD, "by Alice", "Re: Log: Q4 Planning Document"),
            (NotificationEventType.ENTRY_UPDATE, None, "Re: Log: Q4 Planning Document"),
            (NotificationEventType.ENTRY_REPLY, "by Bob", "Re: Log: Q4 Planning Document"),
            (NotificationEventType.REACTION_ADD, "by Charlie", "Re: Log: Q4 Planning Document"),
        ]

        for event_type, action, expected_prefix in subjects:
            subject = strategy.generate_subject(
                event_type=event_type,
                document_title=document_title,
                action_description=action,
                is_email=True,
            )
            assert subject.startswith(expected_prefix)
            if action:
                assert action in subject

    def test_subject_generation_for_non_email(self, strategy):
        """Test subject line generation for non-email notifications."""
        document_title = "Q4 Planning Document"

        # Non-email subjects should include emojis
        emoji_map = {
            NotificationEventType.DOCUMENT_CREATE: "📄",
            NotificationEventType.ENTRY_ADD: "➕",
            NotificationEventType.ENTRY_UPDATE: "✏️",
            NotificationEventType.ENTRY_DELETE: "🗑️",
            NotificationEventType.ENTRY_REPLY: "💬",
            NotificationEventType.REACTION_ADD: "👍",
        }

        for event_type, emoji in emoji_map.items():
            subject = strategy.generate_subject(
                event_type=event_type, document_title=document_title, is_email=False
            )
            assert emoji in subject
            assert document_title in subject

    def test_event_type_detection(self):
        """Test detection of event types from context."""
        mock_event = MagicMock()

        test_cases = [
            # (is_reply, is_update, is_delete, is_reaction, is_reaction_delete, expected)
            (False, False, False, False, False, NotificationEventType.ENTRY_ADD),
            (False, True, False, False, False, NotificationEventType.ENTRY_UPDATE),
            (False, False, True, False, False, NotificationEventType.ENTRY_DELETE),
            (True, False, False, False, False, NotificationEventType.ENTRY_REPLY),
            (True, True, False, False, False, NotificationEventType.REPLY_UPDATE),
            (True, False, True, False, False, NotificationEventType.REPLY_DELETE),
            (False, False, False, True, False, NotificationEventType.REACTION_ADD),
            (False, False, False, True, True, NotificationEventType.REACTION_DELETE),
        ]

        for is_reply, is_update, is_delete, is_reaction, is_reaction_delete, expected in test_cases:
            result = detect_event_type(
                mock_event,
                is_reply=is_reply,
                is_update=is_update,
                is_delete=is_delete,
                is_reaction=is_reaction,
                is_reaction_delete=is_reaction_delete,
            )
            assert result == expected, f"Expected {expected}, got {result}"


class TestEmailThreadingIntegration:
    """Integration tests for email threading with the handler."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create a test configuration with email notifications."""
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
                "alice": {
                    "apprise_urls": [
                        "mailto://alice@company.com",
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
                "bob": {
                    "apprise_urls": [
                        "mailto://bob@company.com",
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
                "charlie": {
                    "apprise_urls": [
                        "teams://webhook_url",  # No email for Charlie
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

        config_path = tmp_path / "threading_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    @pytest.fixture
    def handler(self, test_config):
        """Create handler with test configuration."""
        global_config = GlobalConfig({"bely_url": "https://bely.company.com"})

        # Mock AppriseWithEmailHeaders class
        mock_apprise_wrapper = MagicMock()
        mock_apprise_wrapper.return_value.notify = MagicMock(return_value=True)
        mock_apprise_wrapper.return_value.add = MagicMock(return_value=True)
        mock_apprise_wrapper.return_value.__bool__ = MagicMock(return_value=True)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_wrapper):
            handler = AppriseSmartNotificationHandler(
                config_path=str(test_config), global_config=global_config
            )

            # Mock Apprise notify for all users
            for username, apobj in handler.processor.user_apprise_instances.items():
                apobj.notify = MagicMock(return_value=True)

            return handler

    @pytest.mark.asyncio
    async def test_email_thread_conversation(self, handler):
        """Test a complete email thread conversation."""
        base_time = datetime.now()

        # Track all notifications sent
        notifications = []

        async def track_notification(username, title, body, attach=None):
            notifications.append(
                {
                    "username": username,
                    "title": title,
                    "body": body,
                    "attach": attach,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return True

        handler.processor.send_notification = AsyncMock(side_effect=track_notification)

        # Create a document
        doc = LogDocumentInfo(
            id=1000,
            name="Team Retrospective",
            ownerUsername="alice",
            createdByUsername="alice",
            lastModifiedByUsername="alice",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # 1. Bob adds an entry to Alice's document
        event1 = LogEntryAddEvent(
            eventTimestamp=(base_time + timedelta(minutes=5)).isoformat(),
            eventTriggedByUsername="bob",
            entityName="LogEntry",
            entityId=1001,
            parentLogDocumentInfo=doc,
            logInfo=LogInfo(
                id=1001,
                enteredByUsername="bob",
                lastModifiedByUsername="bob",
                enteredOnDateTime=(base_time + timedelta(minutes=5)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(minutes=5)).isoformat(),
            ),
            description="Added retrospective feedback",
            textDiff="+ What went well: Sprint velocity improved\n+ To improve: Better testing coverage",
            logbookList=[LogbookInfo(id=1, name="Retrospectives", displayName="Retrospectives")],
        )

        await handler.handle_log_entry_add(event1)

        # Alice should get notified (document owner)
        assert len(notifications) == 1
        assert notifications[0]["username"] == "alice"

        # Check if email threading headers would be applied
        # (In real implementation, these would be in the attach parameter)
        # For email notifications, the subject should use "Re:" for threading

        # 2. Alice replies to Bob's entry
        event2 = LogEntryReplyAddEvent(
            eventTimestamp=(base_time + timedelta(minutes=10)).isoformat(),
            eventTriggedByUsername="alice",
            entityName="LogEntryReply",
            entityId=1002,
            parentLogDocumentInfo=doc,
            parentLogInfo=LogInfo(
                id=1001,
                enteredByUsername="bob",
                lastModifiedByUsername="bob",
                enteredOnDateTime=(base_time + timedelta(minutes=5)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(minutes=5)).isoformat(),
            ),
            logInfo=LogInfo(
                id=1002,
                enteredByUsername="alice",
                lastModifiedByUsername="alice",
                enteredOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
            ),
            textDiff="Great points! Let's schedule a meeting to discuss the testing strategy.",
            logbookList=[LogbookInfo(id=1, name="Retrospectives", displayName="Retrospectives")],
            description="Response to feedback",
        )

        await handler.handle_log_entry_reply_add(event2)

        # Bob should get notified (entry creator)
        assert len(notifications) == 2
        assert notifications[1]["username"] == "bob"

        # 3. Bob reacts to Alice's reply
        from bely_mqtt.models import ReactionId

        event3 = LogReactionAddEvent(
            eventTimestamp=(base_time + timedelta(minutes=15)).isoformat(),
            eventTriggedByUsername="bob",
            entityName="LogReaction",
            entityId=ReactionId(logId=1002, reactionId=1, userId=2),
            parentLogDocumentInfo=doc,
            parentLogInfo=LogInfo(
                id=1002,
                enteredByUsername="alice",
                lastModifiedByUsername="alice",
                enteredOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
                lastModifiedOnDateTime=(base_time + timedelta(minutes=10)).isoformat(),
            ),
            logReaction=LogReactionInfo(
                id=ReactionId(logId=1002, reactionId=1, userId=2),
                reaction=ReactionInfo(
                    id=1, emoji="👍", name="thumbsup", emojiCode=128077, description="Agreed"
                ),
                username="bob",
            ),
            description="Agreed with meeting proposal",
        )

        await handler.handle_log_reaction_add(event3)

        # Alice should get notified about the reaction
        assert len(notifications) == 3
        assert notifications[2]["username"] == "alice"

        # Verify all notifications are part of the same conversation thread
        # In a real email client, these would all be grouped together

    @pytest.mark.asyncio
    async def test_mixed_notification_types(self, handler):
        """Test that email and non-email notifications are handled differently."""
        base_time = datetime.now()

        # Track notifications with their types
        notifications = []

        async def track_notification(username, title, body, attach=None):
            # Determine if this is an email notification based on user config
            is_email = False
            if username in ["alice", "bob"]:  # These users have email configured
                is_email = True

            notifications.append(
                {
                    "username": username,
                    "title": title,
                    "body": body,
                    "is_email": is_email,
                }
            )
            return True

        handler.processor.send_notification = AsyncMock(side_effect=track_notification)

        # Create a document owned by Charlie (no email)
        doc = LogDocumentInfo(
            id=2000,
            name="Technical Specs",
            ownerUsername="charlie",
            createdByUsername="charlie",
            lastModifiedByUsername="charlie",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # Alice (has email) adds an entry
        event = LogEntryAddEvent(
            eventTimestamp=base_time.isoformat(),
            eventTriggedByUsername="alice",
            entityName="LogEntry",
            entityId=2001,
            parentLogDocumentInfo=doc,
            logInfo=LogInfo(
                id=2001,
                enteredByUsername="alice",
                lastModifiedByUsername="alice",
                enteredOnDateTime=base_time.isoformat(),
                lastModifiedOnDateTime=base_time.isoformat(),
            ),
            description="Added API specifications",
            textDiff="+ API endpoint: /api/v2/users",
            logbookList=[LogbookInfo(id=2, name="Tech Specs", displayName="Tech Specs")],
        )

        await handler.handle_log_entry_add(event)

        # Charlie should get notified (document owner)
        assert len(notifications) == 1
        assert notifications[0]["username"] == "charlie"
        assert not notifications[0]["is_email"]  # Charlie doesn't have email

    @pytest.mark.asyncio
    async def test_threading_with_updates_and_deletes(self, handler):
        """Test that updates and deletes maintain thread continuity."""
        base_time = datetime.now()

        notifications = []

        async def track_notification(username, title, body, attach=None):
            notifications.append(
                {
                    "username": username,
                    "title": title,
                    "body": body,
                }
            )
            return True

        handler.processor.send_notification = AsyncMock(side_effect=track_notification)

        # Alice's document
        doc = LogDocumentInfo(
            id=3000,
            name="Project Roadmap",
            ownerUsername="alice",
            createdByUsername="alice",
            lastModifiedByUsername="alice",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # Bob's entry
        bob_entry = LogInfo(
            id=3001,
            enteredByUsername="bob",
            lastModifiedByUsername="bob",
            enteredOnDateTime=base_time.isoformat(),
            lastModifiedOnDateTime=base_time.isoformat(),
        )

        # 1. Bob updates his own entry
        event1 = LogEntryUpdateEvent(
            eventTimestamp=(base_time + timedelta(minutes=5)).isoformat(),
            eventTriggedByUsername="bob",
            entityName="LogEntry",
            entityId=3001,
            parentLogDocumentInfo=doc,
            logInfo=bob_entry,
            description="Updated timeline",
            textDiff="- Q3 delivery\n+ Q4 delivery",
            logbookList=[LogbookInfo(id=3, name="Roadmap", displayName="Roadmap")],
        )

        await handler.handle_log_entry_update(event1)

        # Alice should be notified (document owner)
        # Bob shouldn't be notified (he's the one updating)
        assert len(notifications) == 1
        assert notifications[0]["username"] == "alice"

        # 2. Alice deletes Bob's entry
        event2 = LogEntryDeleteEvent(
            eventTimestamp=(base_time + timedelta(minutes=10)).isoformat(),
            eventTriggedByUsername="alice",
            entityName="LogEntry",
            entityId=3001,
            parentLogDocumentInfo=doc,
            logInfo=bob_entry,
            description="Removed outdated entry",
            textDiff="- Deleted: Q4 delivery timeline",
            logbookList=[LogbookInfo(id=3, name="Roadmap", displayName="Roadmap")],
        )

        await handler.handle_log_entry_delete(event2)

        # Bob should be notified (his entry was deleted)
        assert len(notifications) == 2
        assert notifications[1]["username"] == "bob"

        # All these notifications should be part of the same email thread


class TestEmailThreadingEdgeCases:
    """Test edge cases and error handling for email threading."""

    @pytest.fixture
    def strategy(self):
        """Create an EmailThreadingStrategy instance."""
        return EmailThreadingStrategy()

    def test_missing_domain(self, strategy):
        """Test thread ID generation without a domain."""
        # Should use default domain
        thread_id = strategy.generate_document_thread_id("doc123")
        assert "@" in thread_id
        assert thread_id.endswith(">")

    def test_empty_document_name(self, strategy):
        """Test handling of empty document names."""
        headers = strategy.get_email_headers(
            event_type=NotificationEventType.ENTRY_ADD,
            document_id="doc123",
            document_name="",  # Empty name
            entry_id="entry456",
        )

        assert "Thread-Topic" in headers
        # Should handle empty name gracefully

    def test_special_characters_in_ids(self, strategy):
        """Test handling of special characters in IDs."""
        # IDs with special characters
        doc_id = "doc-123_test@special"
        entry_id = "entry/456\\test"

        doc_thread = strategy.generate_document_thread_id(doc_id)
        entry_thread = strategy.generate_entry_thread_id(entry_id)

        # Should generate valid message IDs
        assert doc_thread.startswith("<")
        assert doc_thread.endswith(">")
        assert entry_thread.startswith("<")
        assert entry_thread.endswith(">")

    def test_very_long_document_name(self, strategy):
        """Test handling of very long document names."""
        long_name = "A" * 500  # Very long document name

        subject = strategy.generate_subject(
            event_type=NotificationEventType.ENTRY_ADD, document_title=long_name, is_email=True
        )

        # Should truncate or handle gracefully
        assert len(subject) < 1000  # Reasonable subject length

    def test_unicode_in_document_name(self, strategy):
        """Test handling of Unicode characters in document names."""
        unicode_name = "Project 项目 🚀 Проект"

        headers = strategy.get_email_headers(
            event_type=NotificationEventType.ENTRY_ADD,
            document_id="doc123",
            document_name=unicode_name,
            entry_id="entry456",
        )

        subject = strategy.generate_subject(
            event_type=NotificationEventType.ENTRY_ADD, document_title=unicode_name, is_email=True
        )

        assert "Thread-Topic" in headers
        assert unicode_name in headers["Thread-Topic"]
        assert unicode_name in subject


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
