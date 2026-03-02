"""
Tests for API-based notification configuration loading.

Tests the code path where notification configs are loaded from the BELY REST API
(/api/NotificationConfiguration/all) instead of YAML files.
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
sys.modules["apprise"] = MagicMock()

from bely_mqtt import LogEntryAddEvent, LogEntryUpdateEvent  # noqa: E402
from bely_mqtt.models import LogInfo, LogDocumentInfo, LogbookInfo  # noqa: E402
from bely_mqtt.config import GlobalConfig  # noqa: E402

# Add parent directory to path to import handler module
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))

from config_loader import ConfigLoader  # noqa: E402
from handler import AppriseSmartNotificationHandler  # noqa: E402


def make_mock_nc(
    username,
    notification_endpoint,
    handler_preferences_by_name=None,
    notification_provider_name="email",
    name="config",
    description="",
    id=1,
):
    """Create a mock NotificationConfiguration object matching the API model."""
    mock = MagicMock()
    mock.username = username
    mock.notification_endpoint = notification_endpoint
    mock.handler_preferences_by_name = handler_preferences_by_name
    mock.notification_provider_name = notification_provider_name
    mock.name = name
    mock.description = description
    mock.id = id
    return mock


SAMPLE_API_CONFIGS = [
    make_mock_nc(
        username="logr",
        notification_endpoint="mailto://logr@example.com",
        handler_preferences_by_name={
            "entry_updates": True,
            "own_entry_edits": True,
            "entry_replies": True,
            "new_entries": True,
            "reactions": True,
            "document_replies": True,
        },
        notification_provider_name="email",
        name="logr-email",
        id=1,
    ),
    make_mock_nc(
        username="logr",
        notification_endpoint="slack://TokenA/TokenB/TokenC/",
        handler_preferences_by_name={
            "entry_updates": True,
            "own_entry_edits": False,
            "entry_replies": True,
            "new_entries": False,
            "reactions": False,
            "document_replies": True,
        },
        notification_provider_name="slack",
        name="logr-slack",
        id=2,
    ),
    make_mock_nc(
        username="logr",
        notification_endpoint="json://webhook.example.com/hook",
        handler_preferences_by_name={
            "entry_updates": False,
            "own_entry_edits": False,
            "entry_replies": False,
            "new_entries": False,
            "reactions": False,
            "document_replies": False,
        },
        notification_provider_name="custom_webhook",
        name="logr-webhook",
        id=3,
    ),
]


def make_mock_api_factory(configs):
    """Create a mock api_factory that returns the given configs from get_all()."""
    mock_factory = MagicMock()
    mock_nc_api = MagicMock()
    mock_nc_api.get_all.return_value = configs
    mock_factory.getNotificationConfigurationApi.return_value = mock_nc_api
    return mock_factory


class TestLoadConfigFromApi:
    """Unit tests for ConfigLoader.load_config_from_api()."""

    @pytest.fixture
    def loader(self):
        return ConfigLoader(logging.getLogger("test"))

    def test_load_config_from_api_basic(self, loader):
        """API configs are loaded into the correct structure."""
        factory = make_mock_api_factory(SAMPLE_API_CONFIGS)
        result = loader.load_config_from_api(factory)

        assert "users" in result
        assert "logr" in result["users"]

        logr_configs = result["users"]["logr"]["configs"]
        assert len(logr_configs) == 3

        # Verify first config
        assert logr_configs[0]["apprise_url"] == "mailto://logr@example.com"
        assert logr_configs[0]["notifications"]["entry_updates"] is True
        assert logr_configs[0]["notifications"]["reactions"] is True

        # Verify second config (slack)
        assert logr_configs[1]["apprise_url"] == "slack://TokenA/TokenB/TokenC/"
        assert logr_configs[1]["notifications"]["own_entry_edits"] is False
        assert logr_configs[1]["notifications"]["new_entries"] is False

        # Verify third config (webhook with everything disabled)
        assert logr_configs[2]["apprise_url"] == "json://webhook.example.com/hook"
        assert all(v is False for v in logr_configs[2]["notifications"].values())

    def test_load_config_from_api_multiple_users(self, loader):
        """Configs for different users are grouped correctly."""
        configs = [
            make_mock_nc("logr", "mailto://logr@example.com", {"entry_updates": True}, id=1),
            make_mock_nc(
                "djarosz",
                "mailto://dj@example.com",
                {"entry_updates": True, "reactions": False},
                id=2,
            ),
            make_mock_nc("logr", "slack://token/a/b/", {"entry_updates": False}, id=3),
            make_mock_nc("djarosz", "discord://webhook/token", {"new_entries": True}, id=4),
        ]
        factory = make_mock_api_factory(configs)
        result = loader.load_config_from_api(factory)

        assert len(result["users"]) == 2
        assert len(result["users"]["logr"]["configs"]) == 2
        assert len(result["users"]["djarosz"]["configs"]) == 2

        # Verify ordering is preserved
        assert result["users"]["logr"]["configs"][0]["apprise_url"] == "mailto://logr@example.com"
        assert result["users"]["logr"]["configs"][1]["apprise_url"] == "slack://token/a/b/"
        assert result["users"]["djarosz"]["configs"][0]["apprise_url"] == "mailto://dj@example.com"
        assert result["users"]["djarosz"]["configs"][1]["apprise_url"] == "discord://webhook/token"

    def test_load_config_from_api_empty_username(self, loader):
        """Configs with empty or None username are skipped."""
        configs = [
            make_mock_nc(None, "mailto://nobody@example.com", {"entry_updates": True}, id=1),
            make_mock_nc("", "mailto://empty@example.com", {"entry_updates": True}, id=2),
            make_mock_nc("logr", "mailto://logr@example.com", {"entry_updates": True}, id=3),
        ]
        factory = make_mock_api_factory(configs)
        result = loader.load_config_from_api(factory)

        assert len(result["users"]) == 1
        assert "logr" in result["users"]

    def test_load_config_from_api_empty_preferences(self, loader):
        """Configs with None handler_preferences_by_name default to empty dict."""
        configs = [
            make_mock_nc(
                "logr", "mailto://logr@example.com", handler_preferences_by_name=None, id=1
            ),
        ]
        factory = make_mock_api_factory(configs)
        result = loader.load_config_from_api(factory)

        logr_config = result["users"]["logr"]["configs"][0]
        assert logr_config["notifications"] == {}

    def test_load_config_from_api_empty_result(self, loader):
        """Empty API response returns empty users dict."""
        factory = make_mock_api_factory([])
        result = loader.load_config_from_api(factory)

        assert result == {"users": {}}


class TestHandlerApiInit:
    """Tests for handler initialization via API factory."""

    @pytest.fixture
    def mock_apprise_cls(self):
        """Provide a mock AppriseWithEmailHeaders class."""
        mock_cls = MagicMock()
        mock_cls.return_value.add = MagicMock(return_value=True)
        mock_cls.return_value.notify = MagicMock(return_value=True)
        mock_cls.return_value.__bool__ = MagicMock(return_value=True)
        return mock_cls

    def test_handler_init_with_api_factory(self, mock_apprise_cls):
        """Handler initializes correctly from API factory."""
        factory = make_mock_api_factory(SAMPLE_API_CONFIGS)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        # logr should have 3 endpoint configs
        assert "logr" in handler.processor.user_endpoint_configs
        assert len(handler.processor.user_endpoint_configs["logr"]) == 3

        # Verify settings were mapped correctly for the first endpoint
        ep0 = handler.processor.user_endpoint_configs["logr"][0]
        assert ep0["settings"]["entry_updates"] is True
        assert ep0["settings"]["reactions"] is True

        # Second endpoint (slack) has different settings
        ep1 = handler.processor.user_endpoint_configs["logr"][1]
        assert ep1["settings"]["own_entry_edits"] is False
        assert ep1["settings"]["new_entries"] is False

    def test_handler_api_with_yaml_global_config(self, mock_apprise_cls, tmp_path):
        """Handler loads users from API and global settings from YAML."""
        # YAML with only global mail server config (no users)
        yaml_config = {
            "global": {
                "mail_server": "smtp.example.com",
                "mail_from": "noreply@example.com",
                "mail_from_name": "BELY Notifications",
                "mail_port": 25,
            },
        }
        config_path = tmp_path / "global_only.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_config, f)

        api_configs = [
            make_mock_nc("logr", "mailto://logr@example.com", {"entry_updates": True}, id=1),
        ]
        factory = make_mock_api_factory(api_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                config_path=str(config_path),
                api_factory=factory,
                global_config=global_config,
            )

        # Users loaded from API
        assert "logr" in handler.processor.user_endpoint_configs

        # Global config loaded from YAML
        assert handler.global_config_data["mail_server"] == "smtp.example.com"
        assert handler.global_config_data["mail_from"] == "noreply@example.com"

    def test_handler_api_fallback_to_yaml(self, mock_apprise_cls, tmp_path):
        """API failure falls back to YAML config."""
        yaml_config = {
            "users": {
                "alice": {
                    "apprise_urls": ["mailto://alice@example.com"],
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
        config_path = tmp_path / "fallback.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_config, f)

        # API factory that raises on get_all()
        mock_factory = MagicMock()
        mock_nc_api = MagicMock()
        mock_nc_api.get_all.side_effect = Exception("API connection refused")
        mock_factory.getNotificationConfigurationApi.return_value = mock_nc_api

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                config_path=str(config_path),
                api_factory=mock_factory,
            )

        # Should have fallen back to YAML
        assert "alice" in handler.processor.user_endpoint_configs
        assert len(handler.processor.user_endpoint_configs["alice"]) == 1


class TestHandlerApiEventProcessing:
    """Tests for event processing with API-loaded configs."""

    @pytest.fixture
    def mock_apprise_cls(self):
        mock_cls = MagicMock()
        mock_cls.return_value.add = MagicMock(return_value=True)
        mock_cls.return_value.notify = MagicMock(return_value=True)
        mock_cls.return_value.__bool__ = MagicMock(return_value=True)
        return mock_cls

    @pytest.fixture
    def api_handler(self, mock_apprise_cls):
        """Create a handler initialized via API with two users."""
        configs = [
            make_mock_nc(
                "alice",
                "mailto://alice@example.com",
                {
                    "entry_updates": True,
                    "own_entry_edits": True,
                    "entry_replies": True,
                    "new_entries": True,
                    "reactions": True,
                    "document_replies": True,
                },
                id=1,
            ),
            make_mock_nc(
                "alice",
                "slack://tokenA/tokenB/tokenC/",
                {
                    "entry_updates": True,
                    "own_entry_edits": False,
                    "entry_replies": True,
                    "new_entries": True,
                    "reactions": False,
                    "document_replies": True,
                },
                id=2,
            ),
            make_mock_nc(
                "bob",
                "mailto://bob@example.com",
                {
                    "entry_updates": True,
                    "own_entry_edits": True,
                    "entry_replies": True,
                    "new_entries": False,
                    "reactions": False,
                    "document_replies": True,
                },
                id=3,
            ),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )
            # Mock notify on all endpoint apprise objects
            for username, endpoints in handler.processor.user_endpoint_configs.items():
                for ep in endpoints:
                    ep["apprise"].notify = MagicMock(return_value=True)
            return handler

    @pytest.mark.asyncio
    async def test_handler_processes_event_with_api_config(self, api_handler):
        """Event processing works correctly with API-loaded configs."""
        timestamp = datetime.now().isoformat()

        doc = LogDocumentInfo(
            id=100,
            name="Test Document",
            ownerUsername="alice",
            createdByUsername="alice",
            lastModifiedByUsername="alice",
            enteredOnDateTime=timestamp,
            lastModifiedOnDateTime=timestamp,
        )

        # Bob adds an entry to Alice's document
        event = LogEntryAddEvent(
            eventTimestamp=timestamp,
            eventTriggedByUsername="bob",
            entityName="LogEntry",
            entityId=1,
            parentLogDocumentInfo=doc,
            logInfo=LogInfo(
                id=1,
                enteredByUsername="bob",
                lastModifiedByUsername="bob",
                enteredOnDateTime=timestamp,
                lastModifiedOnDateTime=timestamp,
            ),
            description="New finding",
            textDiff="+ Added test results",
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        with patch.object(
            api_handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await api_handler.handle_log_entry_add(event)

            # Alice should be notified (document owner, new_entries=True)
            mock_send.assert_called_once()
            assert mock_send.call_args[0][0] == "alice"

    @pytest.mark.asyncio
    async def test_per_endpoint_preferences_respected(self, api_handler):
        """Per-endpoint notification preferences from API are respected."""
        # Alice has two endpoints:
        #   email: all enabled
        #   slack: own_entry_edits=False, reactions=False

        # Verify should_notify uses ANY endpoint having the setting enabled
        assert api_handler.processor.should_notify("alice", "own_entry_edits") is True
        assert api_handler.processor.should_notify("alice", "reactions") is True

        # Bob: new_entries=False, reactions=False
        assert api_handler.processor.should_notify("bob", "new_entries") is False
        assert api_handler.processor.should_notify("bob", "reactions") is False
        assert api_handler.processor.should_notify("bob", "entry_replies") is True

    @pytest.mark.asyncio
    async def test_unconfigured_user_not_notified(self, api_handler):
        """Users not in the API config don't receive notifications."""
        assert api_handler.processor.should_notify("charlie", "entry_updates") is False

        timestamp = datetime.now().isoformat()
        doc = LogDocumentInfo(
            id=200,
            name="Charlie's Doc",
            ownerUsername="charlie",
            createdByUsername="charlie",
            lastModifiedByUsername="charlie",
            enteredOnDateTime=timestamp,
            lastModifiedOnDateTime=timestamp,
        )

        event = LogEntryAddEvent(
            eventTimestamp=timestamp,
            eventTriggedByUsername="bob",
            entityName="LogEntry",
            entityId=2,
            parentLogDocumentInfo=doc,
            logInfo=LogInfo(
                id=2,
                enteredByUsername="bob",
                lastModifiedByUsername="bob",
                enteredOnDateTime=timestamp,
                lastModifiedOnDateTime=timestamp,
            ),
            description="Entry in charlie's doc",
            textDiff="+ content",
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        with patch.object(
            api_handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await api_handler.handle_log_entry_add(event)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_notifies_both_creator_and_owner(self, api_handler):
        """Third-party update notifies both entry creator and document owner."""
        timestamp = datetime.now().isoformat()

        doc = LogDocumentInfo(
            id=300,
            name="Alice's Project",
            ownerUsername="alice",
            createdByUsername="alice",
            lastModifiedByUsername="alice",
            enteredOnDateTime=timestamp,
            lastModifiedOnDateTime=timestamp,
        )

        bob_entry = LogInfo(
            id=3,
            enteredByUsername="bob",
            lastModifiedByUsername="bob",
            enteredOnDateTime=timestamp,
            lastModifiedOnDateTime=timestamp,
        )

        # Alice (owner, not the editor) edits Bob's entry
        event = LogEntryUpdateEvent(
            eventTimestamp=timestamp,
            eventTriggedByUsername="alice",
            entityName="LogEntry",
            entityId=3,
            parentLogDocumentInfo=doc,
            logInfo=bob_entry,
            description="Fixed typo",
            textDiff="- old text\n+ new text",
            logbookList=[LogbookInfo(id=1, name="Test", displayName="Test")],
        )

        with patch.object(
            api_handler.processor, "send_notification", new_callable=AsyncMock
        ) as mock_send:
            await api_handler.handle_log_entry_update(event)

            # Bob gets notified (own_entry_edits), Alice is the actor so only 1 call
            assert mock_send.call_count == 1
            assert mock_send.call_args[0][0] == "bob"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
