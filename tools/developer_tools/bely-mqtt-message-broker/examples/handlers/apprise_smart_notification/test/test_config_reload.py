"""
Tests for runtime configuration reload triggered by NotificationConfiguration events.

When a NotificationConfiguration is created, updated, or deleted via the BELY UI/API,
the handler receives a generic CoreEvent and debounce-reloads config from the API.
"""

import asyncio
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

from bely_mqtt import CoreEvent  # noqa: E402
from bely_mqtt.config import GlobalConfig  # noqa: E402

# Add parent directory to path to import handler module
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))

from handler import AppriseSmartNotificationHandler  # noqa: E402


def make_mock_nc(username, notification_endpoint, handler_preferences_by_name=None, id=1):
    """Create a mock NotificationConfiguration object."""
    mock = MagicMock()
    mock.username = username
    mock.notification_endpoint = notification_endpoint
    mock.handler_preferences_by_name = handler_preferences_by_name
    mock.id = id
    return mock


def make_mock_api_factory(configs):
    """Create a mock api_factory that returns the given configs."""
    mock_factory = MagicMock()
    mock_nc_api = MagicMock()
    mock_nc_api.get_all.return_value = configs
    mock_factory.getNotificationConfigurationApi.return_value = mock_nc_api
    return mock_factory


def make_core_event(entity_name, entity_id=1):
    """Create a CoreEvent with the given entity name."""
    return CoreEvent(
        description=f"{entity_name} changed",
        eventTimestamp=datetime.now().isoformat(),
        entityName=entity_name,
        entityId=entity_id,
        eventTriggedByUsername="admin",
    )


@pytest.fixture
def mock_apprise_cls():
    """Provide a mock AppriseWithEmailHeaders class."""
    mock_cls = MagicMock()
    mock_cls.return_value.add = MagicMock(return_value=True)
    mock_cls.return_value.notify = MagicMock(return_value=True)
    mock_cls.return_value.__bool__ = MagicMock(return_value=True)
    return mock_cls


@pytest.fixture
def initial_api_configs():
    """Initial API configs with one user."""
    return [
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
    ]


@pytest.fixture
def handler_with_api(mock_apprise_cls, initial_api_configs):
    """Create a handler initialized via API factory."""
    factory = make_mock_api_factory(initial_api_configs)
    global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

    with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
        handler = AppriseSmartNotificationHandler(
            api_factory=factory,
            global_config=global_config,
        )
    return handler


class TestNotificationConfigEventDetection:
    """Tests that only NotificationConfiguration events trigger reload."""

    @pytest.mark.asyncio
    async def test_add_notification_config_triggers_reload(self, handler_with_api):
        event = make_core_event("NotificationConfiguration")
        with patch.object(handler_with_api, "_schedule_config_reload") as mock_schedule:
            await handler_with_api.handle_generic_add(event)
            mock_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_notification_config_triggers_reload(self, handler_with_api):
        event = make_core_event("NotificationConfiguration")
        with patch.object(handler_with_api, "_schedule_config_reload") as mock_schedule:
            await handler_with_api.handle_generic_update(event)
            mock_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification_config_triggers_reload(self, handler_with_api):
        event = make_core_event("NotificationConfiguration")
        with patch.object(handler_with_api, "_schedule_config_reload") as mock_schedule:
            await handler_with_api.handle_generic_delete(event)
            mock_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_other_entity_add_ignored(self, handler_with_api):
        event = make_core_event("Log")
        with patch.object(handler_with_api, "_schedule_config_reload") as mock_schedule:
            await handler_with_api.handle_generic_add(event)
            mock_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_other_entity_update_ignored(self, handler_with_api):
        event = make_core_event("UserInfo")
        with patch.object(handler_with_api, "_schedule_config_reload") as mock_schedule:
            await handler_with_api.handle_generic_update(event)
            mock_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_other_entity_delete_ignored(self, handler_with_api):
        event = make_core_event("LogEntry")
        with patch.object(handler_with_api, "_schedule_config_reload") as mock_schedule:
            await handler_with_api.handle_generic_delete(event)
            mock_schedule.assert_not_called()


class TestDebounce:
    """Tests for debounced config reload scheduling."""

    @pytest.mark.asyncio
    async def test_debounce_coalesces_rapid_events(self, handler_with_api):
        """Multiple rapid events result in only one reload."""
        handler_with_api._reload_debounce_seconds = 0.1

        with patch.object(
            handler_with_api, "_reload_config", new_callable=AsyncMock
        ) as mock_reload:
            # Fire three events rapidly
            for _ in range(3):
                event = make_core_event("NotificationConfiguration")
                await handler_with_api.handle_generic_update(event)

            # Wait for debounce to fire
            await asyncio.sleep(0.2)

            # Should only reload once
            mock_reload.assert_called_once()

    @pytest.mark.asyncio
    async def test_debounce_resets_timer(self, handler_with_api):
        """Later events reset the debounce timer."""
        handler_with_api._reload_debounce_seconds = 0.15

        with patch.object(
            handler_with_api, "_reload_config", new_callable=AsyncMock
        ) as mock_reload:
            event = make_core_event("NotificationConfiguration")
            await handler_with_api.handle_generic_update(event)

            # Wait less than debounce, then fire another event
            await asyncio.sleep(0.05)
            await handler_with_api.handle_generic_update(event)

            # Wait less than debounce from the first event, but before the second fires
            await asyncio.sleep(0.1)
            mock_reload.assert_not_called()

            # Wait for the second timer to fire
            await asyncio.sleep(0.1)
            mock_reload.assert_called_once()


class TestNoApiFactory:
    """Tests for handler without API factory."""

    @pytest.mark.asyncio
    async def test_no_api_factory_warns_on_reload(self, mock_apprise_cls):
        """Without api_factory, schedule logs warning and skips."""
        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler()

        with patch.object(handler, "logger") as mock_logger:
            handler._schedule_config_reload()
            mock_logger.warning.assert_called_once()

        assert handler._reload_timer is None


class TestReloadConfig:
    """Tests for the actual config reload logic."""

    @pytest.mark.asyncio
    async def test_successful_reload_updates_config(self, mock_apprise_cls):
        """Successful API reload swaps user_endpoint_configs."""
        initial_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
        ]
        factory = make_mock_api_factory(initial_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert "alice" in handler.processor.user_endpoint_configs
        assert "bob" not in handler.processor.user_endpoint_configs

        # Update API to return new configs including bob
        new_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
            make_mock_nc(
                "bob", "mailto://bob@example.com", {"entry_updates": True, "reactions": False}, id=2
            ),
        ]
        nc_api = factory.getNotificationConfigurationApi()
        nc_api.get_all.return_value = new_configs

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler._reload_config()

        assert "alice" in handler.processor.user_endpoint_configs
        assert "bob" in handler.processor.user_endpoint_configs

    @pytest.mark.asyncio
    async def test_failed_reload_preserves_existing(self, mock_apprise_cls):
        """API failure during reload keeps existing config intact."""
        initial_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
        ]
        factory = make_mock_api_factory(initial_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        original_configs = handler.processor.user_endpoint_configs.copy()

        # Make API fail on next call
        nc_api = factory.getNotificationConfigurationApi()
        nc_api.get_all.side_effect = Exception("API connection refused")

        await handler._reload_config()

        # Existing config should be preserved
        assert handler.processor.user_endpoint_configs == original_configs
        assert "alice" in handler.processor.user_endpoint_configs

    @pytest.mark.asyncio
    async def test_reload_preserves_global_config(self, mock_apprise_cls, tmp_path):
        """Global config from YAML is preserved/merged during reload."""
        yaml_config = {
            "global": {
                "mail_server": "smtp.example.com",
                "mail_from": "noreply@example.com",
                "mail_port": 25,
            },
        }
        config_path = tmp_path / "global.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_config, f)

        initial_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
        ]
        factory = make_mock_api_factory(initial_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                config_path=str(config_path),
                api_factory=factory,
                global_config=global_config,
            )

        assert handler.global_config_data["mail_server"] == "smtp.example.com"

        # Reload should pass global config to the temp processor
        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch.object(handler.config_loader, "load_config_from_api") as mock_load_api:
                mock_load_api.return_value = {
                    "users": {
                        "bob": {
                            "configs": [
                                {"apprise_url": "mailto://bob@example.com", "notifications": {}}
                            ]
                        }
                    }
                }

                await handler._reload_config()

                # Verify global config was passed
                call_args = mock_load_api.call_args
                assert call_args is not None

        # Global config data should still be intact
        assert handler.global_config_data["mail_server"] == "smtp.example.com"

    @pytest.mark.asyncio
    async def test_reload_clears_removed_user(self, mock_apprise_cls):
        """When a user's config is removed from API, they're no longer configured after reload."""
        initial_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
            make_mock_nc("bob", "mailto://bob@example.com", {"entry_updates": True}, id=2),
        ]
        factory = make_mock_api_factory(initial_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert "alice" in handler.processor.user_endpoint_configs
        assert "bob" in handler.processor.user_endpoint_configs

        # Remove bob from API
        new_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
        ]
        nc_api = factory.getNotificationConfigurationApi()
        nc_api.get_all.return_value = new_configs

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler._reload_config()

        assert "alice" in handler.processor.user_endpoint_configs
        assert "bob" not in handler.processor.user_endpoint_configs


class TestConfigIdTracking:
    """Tests for config_id storage, reverse index, and lookup/removal methods."""

    def test_api_configs_store_config_id(self, mock_apprise_cls):
        """Config IDs from API are stored in endpoint dicts."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=42),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        endpoints = handler.processor.user_endpoint_configs["alice"]
        assert endpoints[0]["config_id"] == 42

    def test_reverse_index_maps_config_id_to_username(self, mock_apprise_cls):
        """Reverse index maps config_id to username correctly."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
            make_mock_nc("bob", "mailto://bob@example.com", {}, id=20),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert handler.processor._config_id_to_username == {10: "alice", 20: "bob"}

    def test_get_username_by_config_id_returns_correct_username(self, mock_apprise_cls):
        """get_username_by_config_id() returns correct username."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert handler.processor.get_username_by_config_id(10) == "alice"

    def test_get_username_by_config_id_returns_none_for_unknown(self, mock_apprise_cls):
        """get_username_by_config_id() returns None for unknown ID."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert handler.processor.get_username_by_config_id(999) is None

    def test_remove_endpoint_by_config_id(self, mock_apprise_cls):
        """remove_endpoint_by_config_id() removes correct endpoint and cleans up reverse index."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
            make_mock_nc("alice", "slack://token", {}, id=11),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert len(handler.processor.user_endpoint_configs["alice"]) == 2
        result = handler.processor.remove_endpoint_by_config_id(10)

        assert result is True
        assert len(handler.processor.user_endpoint_configs["alice"]) == 1
        assert handler.processor.user_endpoint_configs["alice"][0]["config_id"] == 11
        assert 10 not in handler.processor._config_id_to_username
        assert handler.processor._config_id_to_username[11] == "alice"

    def test_remove_last_endpoint_removes_user_key(self, mock_apprise_cls):
        """remove_endpoint_by_config_id() removes user key when last endpoint removed."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        result = handler.processor.remove_endpoint_by_config_id(10)

        assert result is True
        assert "alice" not in handler.processor.user_endpoint_configs
        assert 10 not in handler.processor._config_id_to_username

    def test_remove_unknown_config_id_returns_false(self, mock_apprise_cls):
        """remove_endpoint_by_config_id() returns False for unknown ID."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        result = handler.processor.remove_endpoint_by_config_id(999)
        assert result is False

    def test_yaml_configs_have_none_config_id(self, mock_apprise_cls, tmp_path):
        """YAML-loaded configs have config_id: None and don't pollute reverse index."""
        yaml_config = {
            "users": {
                "alice": {
                    "apprise_urls": ["mailto://alice@example.com"],
                    "notifications": {"entry_updates": True},
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_config, f)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(config_path=str(config_path))

        endpoints = handler.processor.user_endpoint_configs["alice"]
        assert endpoints[0]["config_id"] is None
        assert handler.processor._config_id_to_username == {}

    @pytest.mark.asyncio
    async def test_reverse_index_rebuilt_on_reload(self, mock_apprise_cls):
        """After full reload, reverse index is rebuilt correctly."""
        initial_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {}, id=10),
        ]
        factory = make_mock_api_factory(initial_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        assert handler.processor._config_id_to_username == {10: "alice"}

        # Update API to return different configs
        new_configs = [
            make_mock_nc("bob", "mailto://bob@example.com", {}, id=20),
            make_mock_nc("bob", "slack://token", {}, id=21),
        ]
        nc_api = factory.getNotificationConfigurationApi()
        nc_api.get_all.return_value = new_configs

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler._reload_config()

        # Old index should be gone, new one built
        assert 10 not in handler.processor._config_id_to_username
        assert handler.processor._config_id_to_username == {20: "bob", 21: "bob"}


class TestEndToEnd:
    """End-to-end test: event -> debounce -> reload."""

    @pytest.mark.asyncio
    async def test_notification_config_event_triggers_full_reload(self, mock_apprise_cls):
        """A NotificationConfiguration update event triggers a full config reload."""
        initial_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
        ]
        factory = make_mock_api_factory(initial_configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            handler = AppriseSmartNotificationHandler(
                api_factory=factory,
                global_config=global_config,
            )

        handler._reload_debounce_seconds = 0.05

        # Update API to include bob
        new_configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=1),
            make_mock_nc("bob", "mailto://bob@example.com", {"entry_updates": True}, id=2),
        ]
        nc_api = factory.getNotificationConfigurationApi()
        nc_api.get_all.return_value = new_configs

        event = make_core_event("NotificationConfiguration", entity_id=2)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler.handle_generic_add(event)
            await asyncio.sleep(0.1)

        assert "bob" in handler.processor.user_endpoint_configs


class TestUnsubscribeLink:
    """Tests for per-endpoint unsubscribe link injection in email notifications."""

    @pytest.mark.asyncio
    async def test_email_endpoint_with_config_id_includes_unsubscribe_link(self, mock_apprise_cls):
        """Email endpoint with config_id and bely_url includes unsubscribe URL in body."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=42),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com/bely"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                    global_config=global_config,
                )

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                await handler.processor.send_notification(
                    "alice", "Test", "<p>Body</p>", notification_type="entry_updates"
                )

        call_args = mock_apprise_cls.return_value.notify.call_args
        body = call_args[1]["body"]
        assert "Unsubscribe from entry updates notifications" in body
        assert "configId=42" in body
        assert "notificationType=entry_updates" in body
        assert "bely.example.com/bely/views/notificationConfiguration/unsubscribe" in body

    @pytest.mark.asyncio
    async def test_non_email_endpoint_no_unsubscribe_link(self, mock_apprise_cls):
        """Non-email endpoints do not get unsubscribe links."""
        configs = [
            make_mock_nc("alice", "slack://token", {"entry_updates": True}, id=42),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com/bely"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=False):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                    global_config=global_config,
                )

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler.processor.send_notification(
                "alice", "Test", "<p>Body</p>", notification_type="entry_updates"
            )

        call_args = mock_apprise_cls.return_value.notify.call_args
        body = call_args[1]["body"]
        assert "Unsubscribe" not in body

    @pytest.mark.asyncio
    async def test_config_id_none_no_unsubscribe_link(self, mock_apprise_cls):
        """YAML configs with config_id=None do not get unsubscribe links."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=10),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com/bely"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                    global_config=global_config,
                )

        # Manually set config_id to None to simulate YAML config
        handler.processor.user_endpoint_configs["alice"][0]["config_id"] = None

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler.processor.send_notification(
                "alice", "Test", "<p>Body</p>", notification_type="entry_updates"
            )

        call_args = mock_apprise_cls.return_value.notify.call_args
        body = call_args[1]["body"]
        assert "Unsubscribe" not in body

    @pytest.mark.asyncio
    async def test_bely_url_none_no_unsubscribe_link(self, mock_apprise_cls):
        """When bely_url is None, no unsubscribe link is added."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=42),
        ]
        factory = make_mock_api_factory(configs)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                )

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler.processor.send_notification(
                "alice", "Test", "<p>Body</p>", notification_type="entry_updates"
            )

        call_args = mock_apprise_cls.return_value.notify.call_args
        body = call_args[1]["body"]
        assert "Unsubscribe" not in body

    @pytest.mark.asyncio
    async def test_notification_type_none_no_unsubscribe_link(self, mock_apprise_cls):
        """When notification_type is None, no unsubscribe link is added."""
        configs = [
            make_mock_nc("alice", "mailto://alice@example.com", {"entry_updates": True}, id=42),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com/bely"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                    global_config=global_config,
                )

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            await handler.processor.send_notification(
                "alice", "Test", "<p>Body</p>", notification_type=None
            )

        call_args = mock_apprise_cls.return_value.notify.call_args
        body = call_args[1]["body"]
        assert "Unsubscribe" not in body

    @pytest.mark.asyncio
    async def test_two_email_endpoints_get_distinct_unsubscribe_urls(self, mock_apprise_cls):
        """Two email endpoints with different config_ids get distinct unsubscribe URLs."""
        configs = [
            make_mock_nc("alice", "mailto://alice@work.com", {"entry_updates": True}, id=10),
            make_mock_nc("alice", "mailto://alice@home.com", {"entry_updates": True}, id=20),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com/bely"})

        # Each endpoint gets its own mock Apprise instance
        mock_instances = [MagicMock(), MagicMock()]
        for m in mock_instances:
            m.add = MagicMock(return_value=True)
            m.notify = MagicMock(return_value=True)
        call_count = {"i": 0}

        def create_mock():
            idx = call_count["i"]
            call_count["i"] += 1
            return mock_instances[idx % len(mock_instances)]

        mock_cls = MagicMock(side_effect=create_mock)

        with patch("notification_processor.AppriseWithEmailHeaders", mock_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                    global_config=global_config,
                )

        await handler.processor.send_notification(
            "alice", "Test", "<p>Body</p>", notification_type="entry_updates"
        )

        # Both endpoints should have been notified
        assert mock_instances[0].notify.called
        assert mock_instances[1].notify.called

        body1 = mock_instances[0].notify.call_args[1]["body"]
        body2 = mock_instances[1].notify.call_args[1]["body"]

        assert "configId=10" in body1
        assert "configId=20" in body2
        assert "configId=20" not in body1
        assert "configId=10" not in body2


class TestReactionNotificationType:
    """Tests that reaction events pass notification_type='reactions' for unsubscribe links."""

    @pytest.mark.asyncio
    async def test_reaction_event_passes_notification_type(self, mock_apprise_cls):
        """Reaction add event should pass notification_type='reactions' to send_notification_with_threading."""
        configs = [
            make_mock_nc(
                "alice",
                "mailto://alice@example.com",
                {"reactions": True, "entry_updates": True},
                id=42,
            ),
        ]
        factory = make_mock_api_factory(configs)
        global_config = GlobalConfig({"bely_url": "https://bely.example.com/bely"})

        with patch("notification_processor.AppriseWithEmailHeaders", mock_apprise_cls):
            with patch("notification_processor.is_email_notification", return_value=True):
                handler = AppriseSmartNotificationHandler(
                    api_factory=factory,
                    global_config=global_config,
                )

        with patch.object(
            handler.processor, "send_notification_with_threading", new_callable=AsyncMock
        ) as mock_send:
            # Create a mock reaction add event
            event = MagicMock()
            event.event_triggered_by_username = "bob"
            event.parent_log_info.entered_by_username = "alice"
            event.parent_log_info.id = "entry-1"
            event.parent_log_document_info.id = "doc-1"
            event.parent_log_document_info.name = "Test Doc"

            await handler._handle_reaction_event(event, is_add=True)

            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["notification_type"] == "reactions"
            assert call_kwargs["username"] == "alice"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
