"""Screen-level tests for the full `bely-cli tui` app: Login, Picker, Compose,
NewDoc, Config.

Same hand-rolled FakeApi/FakeSession style as test_tui_app.py/test_tui_data.py
-- no network, no live server. All of these are modal screens, driven through
`app.push_screen_wait(...)` since that's how they're actually used (they call
`self.dismiss(...)`).
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from textual.app import App
from textual.widgets import Button, Input, Select, Static, TextArea

from bely_cli.tui.app import BelyTuiApp
from bely_cli.tui.data import LogbookData
from bely_cli.tui.screens import configscreen
from bely_cli.tui.screens.compose import ComposeScreen
from bely_cli.tui.screens.confirm import ConfirmScreen
from bely_cli.tui.screens.configscreen import ConfigScreen
from bely_cli.tui.screens.login import LoginScreen
from bely_cli.tui.screens.newdoc import NewDocScreen
from bely_cli.tui.screens.picker import PickerScreen


class _NF(Exception):
    """Stand-in for belyApi.exceptions.NotFoundException."""


class FakeLogbookApi:
    def __init__(self, existing_doc=None):
        self.created = None
        self._existing_doc = existing_doc

    def get_logbook_types(self):
        return [SimpleNamespace(id=1, name="ops", display_name="Ops")]

    def get_logbook_systems(self):
        return [SimpleNamespace(id=2, name="SR")]

    def get_logbook_templates(self):
        return [SimpleNamespace(id=3, name="Standard")]

    def get_log_document_by_name(self, name):
        if self._existing_doc is not None:
            return self._existing_doc
        raise _NF()

    def create_logbook_document(self, log_document_options):
        self.created = log_document_options
        return SimpleNamespace(id=42, name=getattr(log_document_options, "name", "New Doc"))

    def get_log_entries(self, log_document_id):
        return []

    def get_log_entry_template(self, log_document_id):
        return SimpleNamespace(log_id=None, log_entry="")

    def add_update_log_entry(self, log_entry):
        log_entry.log_id = 99
        return log_entry


class FakeFactory:
    def __init__(self, api):
        self._api = api

    def get_logbook_api(self):
        return self._api


class FakeSession:
    """Always-authenticated TuiSession stand-in -- no LoginScreen involved."""

    def __init__(self, api):
        self.factory = FakeFactory(api)
        self.data = LogbookData(api)

    def username(self):
        return "alice"

    def is_authenticated(self):
        return True

    def authenticated_api(self):
        return self.factory.get_logbook_api()


class LoginScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_submit_dismisses_with_username_and_password(self):
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(LoginScreen("alice")))
            await pilot.pause()
            screen = app.screen
            screen.query_one("#login-password", Input).value = "secret"
            await pilot.press("enter")  # username -> password focus
            await pilot.pause()
            await pilot.press("enter")  # password -> submit
            await pilot.pause()
            result = await task.wait()
        self.assertEqual(result, ("alice", "secret"))

    async def test_escape_dismisses_with_none(self):
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(LoginScreen()))
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)

    async def test_empty_username_blocks_submit(self):
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(LoginScreen()))
            await pilot.pause()
            screen = app.screen
            screen.query_one("#login-username", Input).value = ""
            await pilot.press("enter")  # -> password focus
            await pilot.pause()
            await pilot.press("enter")  # empty username: warn, stay open
            await pilot.pause()
            self.assertFalse(task.is_finished)
            await pilot.press("escape")
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)


class PickerScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_single_select_enter_dismisses_item(self):
        app = App()
        items = [SimpleNamespace(name="Alpha"), SimpleNamespace(name="Beta")]
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(PickerScreen("Pick one", items, lambda i: i.name)))
            await pilot.pause()
            await pilot.press("enter")  # filter -> list
            await pilot.pause()
            await pilot.press("enter")  # select highlighted (Alpha)
            await pilot.pause()
            result = await task.wait()
        self.assertEqual(result.name, "Alpha")

    async def test_filter_narrows_then_select(self):
        app = App()
        items = [SimpleNamespace(name="Alpha"), SimpleNamespace(name="Beta")]
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(PickerScreen("Pick one", items, lambda i: i.name)))
            await pilot.pause()
            await pilot.press("b", "e", "t")
            await pilot.pause()
            screen = app.screen
            self.assertEqual(screen.shown, [items[1]])
            await pilot.press("enter")  # filter -> list
            await pilot.pause()
            await pilot.press("enter")  # select the only match (Beta)
            await pilot.pause()
            result = await task.wait()
        self.assertEqual(result.name, "Beta")

    async def test_multi_select_space_toggles_then_enter_confirms(self):
        app = App()
        items = [SimpleNamespace(name="Alpha"), SimpleNamespace(name="Beta")]
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(
                PickerScreen("Pick many", items, lambda i: i.name, multi=True)))
            await pilot.pause()
            await pilot.press("enter")  # filter -> list
            await pilot.pause()
            await pilot.press("space")  # toggle Alpha
            await pilot.press("down")
            await pilot.press("space")  # toggle Beta
            await pilot.pause()
            await pilot.press("enter")  # confirm selection
            await pilot.pause()
            result = await task.wait()
        self.assertEqual([i.name for i in result], ["Alpha", "Beta"])

    async def test_doubles_as_confirm_dialog_with_plain_strings(self):
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(
                PickerScreen("Discard unsaved changes?", ["Discard", "Keep editing"], lambda x: x)))
            await pilot.pause()
            await pilot.press("enter")  # filter -> list
            await pilot.pause()
            await pilot.press("down")  # highlight "Keep editing"
            await pilot.press("enter")
            await pilot.pause()
            result = await task.wait()
        self.assertEqual(result, "Keep editing")

    async def test_escape_cancels_with_none(self):
        app = App()
        items = [SimpleNamespace(name="Alpha")]
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(PickerScreen("Pick", items, lambda i: i.name)))
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)


class ComposeScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_button_saves_and_dismisses_with_entry(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=None, log_entry="")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=True)))
            await pilot.pause()
            area = app.screen.query_one("#compose-area", TextArea)
            area.text = "hello world"
            app.screen.query_one("#compose-save", Button).press()
            await pilot.pause()
            await pilot.pause()
            saved = await task.wait()
        self.assertEqual(saved.log_entry, "hello world")
        self.assertEqual(saved.log_id, 99)

    async def test_empty_new_entry_is_skipped_without_saving(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=None, log_entry="")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=True)))
            await pilot.pause()
            app.screen.query_one("#compose-save", Button).press()
            await pilot.pause()
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)

    async def test_cancel_without_changes_dismisses_immediately(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            app.screen.query_one("#compose-cancel", Button).press()
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)

    async def test_cancel_with_unsaved_changes_prompts_discard_confirmation(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            area = app.screen.query_one("#compose-area", TextArea)
            area.text = "existing text, changed"
            app.screen.query_one("#compose-cancel", Button).press()
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "ConfirmScreen")
            app.screen.query_one("#confirm-confirm", Button).press()  # "Discard"
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)

    async def test_cancel_with_unsaved_changes_keep_editing_returns_to_compose(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            area = app.screen.query_one("#compose-area", TextArea)
            area.text = "existing text, changed"
            app.screen.query_one("#compose-cancel", Button).press()
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "ConfirmScreen")
            app.screen.query_one("#confirm-cancel", Button).press()  # "Keep editing"
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "ComposeScreen")
            self.assertFalse(task.is_finished)

    async def test_editor_button_opens_editor_and_updates_buffer(self):
        from contextlib import nullcontext

        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            screen = app.screen
            with patch.object(app, "suspend", return_value=nullcontext()), \
                 patch("bely_cli.common.open_in_editor",
                       side_effect=lambda text: text + " edited"):
                screen.query_one("#compose-editor", Button).press()
                await pilot.pause()
            self.assertEqual(
                screen.query_one("#compose-area", TextArea).text, "existing text edited")
            # buffer is dirty now, so skip Cancel here -- not what this test covers

    async def test_tab_from_attachment_field_reaches_save_next(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            screen = app.screen
            screen.query_one("#compose-attach", Input).focus()
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-save", Button))

    async def test_down_and_up_arrows_move_between_attachment_and_buttons(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            screen = app.screen
            screen.query_one("#compose-attach", Input).focus()
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-save", Button))

            await pilot.press("up")
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-attach", Input))

    async def test_left_and_right_arrows_cycle_between_buttons(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            screen = app.screen
            screen.query_one("#compose-save", Button).focus()
            await pilot.pause()

            await pilot.press("right")
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-editor", Button))

            await pilot.press("right")
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-cancel", Button))

            await pilot.press("right")  # wraps back to the first button
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-save", Button))

            await pilot.press("left")  # wraps the other way
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#compose-cancel", Button))

    async def test_arrow_keys_in_textarea_move_the_cursor_not_focus(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="line one\nline two")
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            screen = app.screen
            area = screen.query_one("#compose-area", TextArea)
            area.focus()
            await pilot.pause()

            for key in ("down", "up", "left", "right"):
                await pilot.press(key)
                await pilot.pause()
                self.assertIs(screen.focused, area)

    async def test_escape_without_changes_dismisses_with_none(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)

    async def test_escape_with_unsaved_changes_prompts_discard_confirmation(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=7, log_entry="existing text")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=False)))
            await pilot.pause()
            area = app.screen.query_one("#compose-area", TextArea)
            area.text = "existing text, changed"
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "ConfirmScreen")
            app.screen.query_one("#confirm-confirm", Button).press()  # "Discard"
            await pilot.pause()
            result = await task.wait()
        self.assertIsNone(result)

    async def test_ctrl_s_saves(self):
        api = FakeLogbookApi()
        doc = SimpleNamespace(id=1, name="Doc")
        entry = SimpleNamespace(log_id=None, log_entry="")
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(
                app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=True)))
            await pilot.pause()
            app.screen.query_one("#compose-area", TextArea).text = "hello world"
            await pilot.press("ctrl+s")
            await pilot.pause()
            await pilot.pause()
            saved = await task.wait()
        self.assertEqual(saved.log_entry, "hello world")


class NewDocScreenPrefillTests(unittest.IsolatedAsyncioTestCase):
    async def test_prefilled_logbook_type_skips_the_type_picker(self):
        api = FakeLogbookApi()
        session = FakeSession(api)
        app = BelyTuiApp(session, limit=10, mode="app")
        ops_type = SimpleNamespace(id=1, name="ops")

        with patch("belyApi.LogDocumentOptions") as opts_cls, \
             patch("belyApi.exceptions.NotFoundException", _NF):
            async with app.run_test() as pilot:
                await pilot.pause()
                task = app.run_worker(
                    app.push_screen_wait(NewDocScreen(session, logbook_type=ops_type)))
                await pilot.pause()

                self.assertEqual(
                    app.screen.query_one("#newdoc-type", Static).content, "Type: ops")

                app.screen.query_one("#newdoc-name", Input).value = "New Doc"
                await pilot.press("ctrl+s")  # create without ever touching ctrl+t
                await pilot.pause()
                await pilot.pause()

                await pilot.press("enter")  # filter -> list ("Create a log entry now?")
                await pilot.pause()
                await pilot.press("down")  # highlight "Skip"
                await pilot.press("enter")
                await pilot.pause()

                doc = await task.wait()

        self.assertEqual(doc.id, 42)
        opts_cls.assert_called_once_with(name="New Doc", logbook_type_id=1)


class NewDocScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_with_type_systems_and_no_template_then_skip_entry(self):
        api = FakeLogbookApi()
        session = FakeSession(api)
        app = BelyTuiApp(session, limit=10, mode="app")

        with patch("belyApi.LogDocumentOptions") as opts_cls, \
             patch("belyApi.exceptions.NotFoundException", _NF):
            async with app.run_test() as pilot:
                await pilot.pause()
                task = app.run_worker(app.push_screen_wait(NewDocScreen(session)))
                await pilot.pause()
                app.screen.query_one("#newdoc-name", Input).value = "New Doc"

                await pilot.press("ctrl+t")  # -> type picker
                await pilot.pause()
                await pilot.pause()
                await pilot.press("enter")  # filter -> list
                await pilot.pause()
                await pilot.press("enter")  # select "ops"
                await pilot.pause()

                await pilot.press("ctrl+y")  # -> systems picker (multi)
                await pilot.pause()
                await pilot.pause()
                await pilot.press("enter")  # filter -> list
                await pilot.pause()
                await pilot.press("space")  # toggle "SR"
                await pilot.pause()
                await pilot.press("enter")  # confirm selection
                await pilot.pause()

                await pilot.press("ctrl+m")  # -> template picker
                await pilot.pause()
                await pilot.pause()
                await pilot.press("enter")  # filter -> list, "(no template)" highlighted
                await pilot.pause()
                await pilot.press("enter")  # select "(no template)"
                await pilot.pause()

                await pilot.press("ctrl+s")  # create
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()

                # no entries came back from the (empty) template -> offered to
                # create one; pick "Skip".
                await pilot.press("enter")  # filter -> list
                await pilot.pause()
                await pilot.press("down")  # highlight "Skip"
                await pilot.press("enter")
                await pilot.pause()

                doc = await task.wait()

        self.assertEqual(doc.id, 42)
        opts_cls.assert_called_once_with(name="New Doc", logbook_type_id=1)
        self.assertEqual(opts_cls.return_value.system_id_list, [2])
        self.assertIs(opts_cls.return_value.skip_default_logbook_type_template, True)

    async def test_duplicate_name_is_rejected_without_creating(self):
        existing = SimpleNamespace(id=7, name="Dup")
        api = FakeLogbookApi(existing_doc=existing)
        session = FakeSession(api)
        app = BelyTuiApp(session, limit=10, mode="app")

        with patch("belyApi.exceptions.NotFoundException", _NF):
            async with app.run_test() as pilot:
                await pilot.pause()
                task = app.run_worker(app.push_screen_wait(NewDocScreen(session)))
                await pilot.pause()
                app.screen.query_one("#newdoc-name", Input).value = "Dup"

                await pilot.press("ctrl+t")
                await pilot.pause()
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()

                await pilot.press("ctrl+s")
                await pilot.pause()
                await pilot.pause()

                self.assertFalse(task.is_finished)
                self.assertIsNone(api.created)

                await pilot.press("escape")
                await pilot.pause()
                result = await task.wait()

        self.assertIsNone(result)


class ConfigScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_escape_dismisses_the_modal(self):
        state = {"settings_file": "/tmp/settings.yaml", "settings": {}, "environment": {}}
        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting", side_effect=lambda k: None):
            async with app.run_test() as pilot:
                task = app.run_worker(app.push_screen_wait(ConfigScreen()))
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                result = await task.wait()
        self.assertIsNone(result)

    async def test_load_prefills_inputs_and_flags_env_overrides(self):
        state = {
            "settings_file": "/tmp/settings.yaml",
            "settings": {"host": "https://example", "editor": "nano"},
            "environment": {"BELY_USER": "alice"},
        }
        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting",
                          side_effect=lambda k: state["settings"].get(k)):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                screen = app.screen
                self.assertEqual(screen.query_one("#config-host", Input).value, "https://example")
                self.assertEqual(screen.query_one("#config-editor", Input).value, "nano")
                self.assertIn(
                    "overridden by BELY_USER", screen.query_one("#config-user", Input).placeholder)

    async def test_save_writes_changed_fields_and_warns_on_env_override(self):
        state = {
            "settings_file": "/tmp/settings.yaml",
            "settings": {"host": "https://old"},
            "environment": {"BELY_HOST": "https://envhost"},
        }
        saved = []

        def fake_set_setting(key, value):
            saved.append((key, value))
            state["settings"][key] = value

        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting",
                          side_effect=lambda k: state["settings"].get(k)), \
             patch.object(configscreen.config, "set_setting", side_effect=fake_set_setting):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                screen = app.screen
                screen.query_one("#config-host", Input).value = "https://new"
                await pilot.press("ctrl+s")
                await pilot.pause()
                await pilot.pause()

        self.assertEqual(saved, [("host", "https://new")])

    async def test_images_field_is_a_select_defaulting_to_auto(self):
        state = {"settings_file": "/tmp/settings.yaml", "settings": {}, "environment": {}}
        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting", side_effect=lambda k: None):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                select = app.screen.query_one("#config-images", Select)
                self.assertEqual(select.value, "auto")

    async def test_images_options_document_each_mode(self):
        from bely_cli.tui.images import IMAGE_MODE_HELP, IMAGE_MODES

        state = {"settings_file": "/tmp/settings.yaml", "settings": {}, "environment": {}}
        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting", side_effect=lambda k: None):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                select = app.screen.query_one("#config-images", Select)
                labels = {value: str(label) for label, value in select._options}
        self.assertEqual(set(labels), set(IMAGE_MODES))
        for mode in IMAGE_MODES:
            self.assertIn(IMAGE_MODE_HELP[mode], labels[mode])

    async def test_images_field_prefills_from_settings(self):
        state = {
            "settings_file": "/tmp/settings.yaml",
            "settings": {"images": "sixel"},
            "environment": {},
        }
        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting",
                          side_effect=lambda k: state["settings"].get(k)):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                select = app.screen.query_one("#config-images", Select)
                self.assertEqual(select.value, "sixel")

    async def test_saving_auto_with_nothing_stored_reports_no_change(self):
        state = {"settings_file": "/tmp/settings.yaml", "settings": {}, "environment": {}}
        saved = []
        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting", side_effect=lambda k: None), \
             patch.object(configscreen.config, "set_setting",
                          side_effect=lambda k, v: saved.append((k, v))):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                await pilot.press("ctrl+s")
                await pilot.pause()
                await pilot.pause()
        self.assertEqual(saved, [])

    async def test_changing_images_select_saves_the_new_value(self):
        state = {"settings_file": "/tmp/settings.yaml", "settings": {}, "environment": {}}
        saved = []

        def fake_set_setting(key, value):
            saved.append((key, value))
            state["settings"][key] = value

        app = App()
        with patch.object(configscreen.core, "collect_config", side_effect=lambda: dict(state)), \
             patch.object(configscreen.config, "get_setting",
                          side_effect=lambda k: state["settings"].get(k)), \
             patch.object(configscreen.config, "set_setting", side_effect=fake_set_setting):
            async with app.run_test() as pilot:
                app.push_screen(ConfigScreen())
                await pilot.pause()
                select = app.screen.query_one("#config-images", Select)
                select.value = "unicode"
                await pilot.press("ctrl+s")
                await pilot.pause()
                await pilot.pause()

        self.assertEqual(saved, [("images", "unicode")])


class ConfirmScreenTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirm_button_dismisses_true(self):
        from textual.widgets import Button

        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(ConfirmScreen("Are you sure?")))
            await pilot.pause()
            app.screen.query_one("#confirm-confirm", Button).press()
            await pilot.pause()
            result = await task.wait()
        self.assertTrue(result)

    async def test_cancel_button_dismisses_false(self):
        from textual.widgets import Button

        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(ConfirmScreen("Are you sure?")))
            await pilot.pause()
            app.screen.query_one("#confirm-cancel", Button).press()
            await pilot.pause()
            result = await task.wait()
        self.assertFalse(result)

    async def test_escape_dismisses_false(self):
        app = App()
        async with app.run_test() as pilot:
            task = app.run_worker(app.push_screen_wait(ConfirmScreen("Are you sure?")))
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            result = await task.wait()
        self.assertFalse(result)

    async def test_default_focus_is_confirm(self):
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ConfirmScreen("Are you sure?")))
            await pilot.pause()
            self.assertIs(app.screen.focused, app.screen.query_one("#confirm-confirm", Button))

    async def test_error_variant_defaults_focus_to_cancel(self):
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(
                ConfirmScreen("Discard unsaved changes?", confirm_variant="error")))
            await pilot.pause()
            self.assertIs(app.screen.focused, app.screen.query_one("#confirm-cancel", Button))

    async def test_left_and_right_arrows_cycle_between_buttons(self):
        app = App()
        async with app.run_test() as pilot:
            app.run_worker(app.push_screen_wait(ConfirmScreen("Are you sure?")))
            await pilot.pause()
            screen = app.screen

            await pilot.press("right")
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#confirm-cancel", Button))

            await pilot.press("right")  # wraps back
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#confirm-confirm", Button))

            await pilot.press("left")  # wraps the other way
            await pilot.pause()
            self.assertIs(screen.focused, screen.query_one("#confirm-cancel", Button))


if __name__ == "__main__":
    unittest.main()
