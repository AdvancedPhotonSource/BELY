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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
