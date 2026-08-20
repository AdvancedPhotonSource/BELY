import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from textual.containers import Vertical
from textual.widgets import DataTable, Input, Markdown, Static

from bely_cli.tui.app import BelyTuiApp
from bely_cli.tui.data import LogbookData
from bely_cli.tui.screens import browse
from bely_cli.tui.screens.browse import BrowseScreen


class FakeSession:
    """Just enough of TuiSession for BrowseScreen -- select_mode="lookup" tests never
    touch auth, so `factory`/`authenticated` default to values that make the n/u
    (auth-gated) flows work out of the box too."""

    def __init__(self, data, *, factory=None, username="alice", authenticated=True):
        self.data = data
        self.factory = factory
        self._username = username
        self._authenticated = authenticated

    def username(self):
        return self._username

    def is_authenticated(self):
        return self._authenticated

    def authenticated_api(self):
        return self.factory.get_logbook_api()

    def try_token(self):
        return self._authenticated


class FakeLogbookApi:
    def get_logbook_types(self):
        return [SimpleNamespace(id=1, name="ops", display_name="Ops")]

    def get_log_documents(self, logbook_type_id, limit):
        return [SimpleNamespace(
            id=10, name="Shift Report", description=None, entity_type_list=None,
            item_type_list=None, more_info=None, log_lockout_hours=None,
        )]

    def get_log_entries(self, log_document_id, load_replies, load_reactions):
        return [SimpleNamespace(
            log_id=100, entered_by_username="alice", entered_on_date_time=None,
            last_modified_by_username=None, last_modified_on_date_time=None,
            log_replies=None, log_reactions=None, log_entry="# Hello\n\nBody text",
        )]

    def get_log_entry_attachments(self, log_document_id, log_id):
        return []

    def get_log_entry_template(self, log_document_id):
        return SimpleNamespace(log_id=None, log_entry="")

    def add_update_log_entry(self, log_entry):
        log_entry.log_id = 101
        return log_entry


class FakeLogbookApiWithImage(FakeLogbookApi):
    """Entry body is a single image-only paragraph (as the server appends after upload)."""

    def get_log_entries(self, log_document_id, load_replies, load_reactions):
        return [SimpleNamespace(
            log_id=100, entered_by_username="alice", entered_on_date_time=None,
            last_modified_by_username=None, last_modified_on_date_time=None,
            log_replies=None, log_reactions=None,
            log_entry="Body text.\n\n![logo](/log/attachments/attachment.1.png)",
        )]


class FakeDownloadApi:
    def get_attachment1_without_preload_content(self, attachment_name, scaling):
        return SimpleNamespace(data=b"fake-scaled-bytes")

    def get_attachment_without_preload_content(self, attachment_name):
        return SimpleNamespace(data=b"fake-bytes")


class FakeImageWidget(Static):
    """Stand-in for textual_image.widget.Image: never touches a real terminal."""

    def __init__(self, image, classes=None):
        super().__init__(f"<image {image!r}>", classes=classes)
        self.image = image


class FakeUsersApi:
    def __init__(self, calls):
        self._calls = calls

    def get_user_by_username(self, username):
        self._calls.append(("user", username))
        return SimpleNamespace(id=99)


class FakeSearchResults:
    def __init__(self, docs):
        self.document_results = docs


class FakeSearchApi:
    def __init__(self, calls, docs):
        self._calls = calls
        self._docs = docs

    def search_logbook(self, search_text, user_id):
        self._calls.append(("search", search_text, tuple(user_id)))
        return FakeSearchResults(self._docs)


class FakeFactory:
    """Combined stand-in for the bits of BelyApiFactory the n/u and recent-docs
    flows touch: get_logbook_api() for ensure_auth(), get_users_api()/
    get_search_api() for core.recent_documents()."""

    def __init__(self, api=None, docs=None):
        self.calls = []
        self._api = api
        self._docs = docs or []

    def get_logbook_api(self):
        return self._api

    def get_users_api(self):
        return FakeUsersApi(self.calls)

    def get_search_api(self):
        return FakeSearchApi(self.calls, self._docs)


class TuiAppSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_browse_populates_list_and_drives_preview(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            table = screen.query_one("#nav-table", DataTable)
            self.assertEqual(table.row_count, 1)
            self.assertEqual(screen.shown_items[0].name, "ops")
            # No info panel open yet: the table gets the full width, no preview.
            self.assertFalse(screen.query_one("#preview").display)
            self.assertEqual(table.styles.width.value, 100)

            await pilot.press("enter")  # descend: type -> docs
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_DOCS)
            self.assertEqual(table.row_count, 1)
            self.assertEqual(screen.shown_items[0].name, "Shift Report")
            self.assertFalse(screen.query_one("#preview").display)

            await pilot.press("enter")  # descend: docs -> entries
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)
            self.assertEqual(table.row_count, 1)
            self.assertEqual(screen.shown_items[0].log_id, 100)
            self.assertTrue(screen.query_one("#body-md", Markdown).display)
            # Entries always show the preview, even though 'i' was never pressed.
            self.assertTrue(screen.query_one("#preview").display)

    async def test_info_toggle_at_table_levels(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            table = screen.query_one("#nav-table", DataTable)
            preview = screen.query_one("#preview")
            self.assertFalse(preview.display)
            # The meta content is kept current even while the panel is hidden.
            self.assertTrue(str(screen.query_one("#meta", Static).render()))

            await pilot.press("i")
            await pilot.pause()
            self.assertTrue(preview.display)
            self.assertEqual(table.styles.width.value, screen.LEVEL_WIDTH[screen.LEVEL_TYPES])

            await pilot.press("i")
            await pilot.pause()
            self.assertFalse(preview.display)
            self.assertEqual(table.styles.width.value, 100)

    async def test_f_key_is_a_no_op_at_table_levels(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            table = screen.query_one("#nav-table", DataTable)

            await pilot.press("f")
            await pilot.pause()
            self.assertTrue(table.display)
            self.assertFalse(screen.query_one("#preview").display)

    async def test_filter_narrows_the_list(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            screen._apply_filter("nonexistent")
            self.assertEqual(screen.shown_items, [])
            screen._apply_filter("")
            self.assertEqual(len(screen.shown_items), 1)

    async def test_filter_box_fits_the_one_row_status_bar(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            await pilot.press("/")
            await pilot.pause()
            filt = screen.query_one("#filter", Input)
            status_bar = screen.query_one("#status-bar")
            self.assertTrue(filt.display)
            self.assertEqual(filt.region.height, status_bar.region.height)

    async def test_show_level_clears_stale_items_so_a_filter_race_cant_preview_them(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_DOCS)

            screen._apply_filter("Shift")  # non-empty filter, like the user hit '/'
            self.assertEqual(len(screen.shown_items), 1)

            screen.sel_doc = screen.shown_items[0]
            screen.show_level(screen.LEVEL_ENTRIES)  # drill in, entries fetch still pending
            self.assertEqual(screen.all_items, [])
            self.assertEqual(screen.shown_items, [])

            # simulate the filter's queued Input.Changed landing before the fetch does
            screen._apply_filter("")  # must not crash previewing the stale doc's .log_entry

            await pilot.pause()  # let the real entries fetch complete and repopulate
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)
            self.assertEqual(screen.shown_items[0].log_id, 100)

    async def test_filter_narrows_table_row_count(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            table = screen.query_one("#nav-table", DataTable)
            self.assertEqual(table.row_count, 1)
            screen._apply_filter("nonexistent")
            self.assertEqual(table.row_count, 0)
            screen._apply_filter("")
            self.assertEqual(table.row_count, 1)

    async def test_footer_shortcuts_track_the_current_level(self):
        # check_action() returns None to hide a binding from the Footer entirely
        # (rather than showing it disabled), so only relevant keys ever appear.
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen

            entry_only_actions = [
                a for a, levels in screen.ACTION_LEVELS.items() if levels == (screen.LEVEL_ENTRIES,)
            ]
            self.assertTrue(screen.check_action("toggle_info", ()))
            self.assertTrue(screen.check_action("refresh_level", ()))
            for action in entry_only_actions:
                self.assertIsNone(screen.check_action(action, ()))

            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.press("enter")  # docs -> entries
            await pilot.pause()
            await pilot.pause()

            self.assertIsNone(screen.check_action("toggle_info", ()))
            for action in entry_only_actions:
                self.assertTrue(screen.check_action(action, ()))

    async def test_escape_at_landing_screen_quits_the_app(self):
        # mode="app" has no separate landing/home screen -- BrowseScreen IS the
        # landing screen, so escape at its top level exits like tui lookup does.
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="app")
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertFalse(app.screen.select_mode)
            await pilot.press("escape")
            await pilot.pause()
        self.assertIsNone(app.return_value)

    async def test_command_palette_offers_config_recent_and_login(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="app")
        async with app.run_test() as pilot:
            await pilot.pause()
            titles = {cmd.title for cmd in app.get_system_commands(app.screen)}
            self.assertIn("Configuration", titles)
            self.assertIn("My documents", titles)
            self.assertIn("Refresh cache", titles)
            self.assertIn("Log in", titles)

    async def test_search_and_resize_bindings_are_gone(self):
        keys = {b.key for b in BrowseScreen.BINDINGS}
        self.assertNotIn("ctrl+s", keys)
        self.assertNotIn("left_square_bracket", keys)
        self.assertNotIn("right_square_bracket", keys)

    async def test_recent_command_pushes_docs_and_escape_returns_to_landing(self):
        import datetime

        docs = [SimpleNamespace(
            object_id=1, object_name="Doc A", logbook_type="ops",
            last_modified_on=datetime.datetime(2024, 1, 1))]
        data = LogbookData(FakeLogbookApi())
        session = FakeSession(data, factory=FakeFactory(docs=docs))
        app = BelyTuiApp(session, limit=10, mode="app")
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "BrowseScreen")
            landing = app.screen

            app._cmd_recent()  # command palette's "My documents" entry
            await pilot.pause()
            await pilot.pause()
            screen = app.screen
            self.assertIsNot(screen, landing)
            self.assertEqual(type(screen).__name__, "BrowseScreen")
            self.assertEqual(screen.source, "recent")
            self.assertEqual(screen.level, screen.LEVEL_DOCS)
            self.assertEqual(screen.shown_items[0].name, "Doc A")

            await pilot.press("escape")  # pops back to the landing browse screen
            await pilot.pause()
            self.assertIs(app.screen, landing)

    async def test_new_entry_action_visible_at_docs_and_entries_not_types(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            self.assertIsNone(screen.check_action("new_entry", ()))

            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            self.assertTrue(screen.check_action("new_entry", ()))

            await pilot.press("enter")  # docs -> entries
            await pilot.pause()
            await pilot.pause()
            self.assertTrue(screen.check_action("new_entry", ()))

    async def test_new_entry_key_creates_entry_and_refreshes(self):
        api = FakeLogbookApi()
        data = LogbookData(api)
        session = FakeSession(data, factory=FakeFactory(api=api))
        app = BelyTuiApp(session, limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen

            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_DOCS)

            await pilot.press("n")  # new entry on the highlighted doc
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "ComposeScreen")

            from textual.widgets import Button, TextArea

            app.screen.query_one("#compose-area", TextArea).text = "new content"
            app.screen.query_one("#compose-save", Button).press()
            await pilot.pause()
            await pilot.pause()

            self.assertEqual(type(app.screen).__name__, "BrowseScreen")
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)
            self.assertEqual(len(screen.shown_items), 1)

    async def test_update_entry_key_opens_compose_prefilled_and_cancel_returns(self):
        api = FakeLogbookApi()
        data = LogbookData(api)
        session = FakeSession(data, factory=FakeFactory(api=api))
        app = BelyTuiApp(session, limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen

            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.press("enter")  # docs -> entries
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)

            await pilot.press("u")  # update the highlighted entry
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "ComposeScreen")

            from textual.widgets import Button, TextArea

            self.assertEqual(
                app.screen.query_one("#compose-area", TextArea).text, "# Hello\n\nBody text")

            # no changes made -> Cancel dismisses immediately, no confirmation, no save
            app.screen.query_one("#compose-cancel", Button).press()
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "BrowseScreen")
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)

    async def test_edit_key_with_no_editor_changes_does_not_save(self):
        api = FakeLogbookApi()
        data = LogbookData(api)
        session = FakeSession(data, factory=FakeFactory(api=api))
        app = BelyTuiApp(session, limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.press("enter")  # docs -> entries
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)

            with patch.object(app, "suspend", return_value=nullcontext()), \
                 patch("bely_cli.common.open_in_editor", side_effect=lambda text: text):
                await pilot.press("e")
                await pilot.pause()
                await pilot.pause()

            self.assertEqual(type(app.screen).__name__, "BrowseScreen")

    async def test_edit_key_with_editor_changes_offers_save_and_saves(self):
        api = FakeLogbookApi()
        data = LogbookData(api)
        session = FakeSession(data, factory=FakeFactory(api=api))
        app = BelyTuiApp(session, limit=10, mode="lookup")
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.press("enter")  # docs -> entries
            await pilot.pause()
            await pilot.pause()
            self.assertEqual(screen.level, screen.LEVEL_ENTRIES)

            with patch.object(app, "suspend", return_value=nullcontext()), \
                 patch("bely_cli.common.open_in_editor",
                       side_effect=lambda text: text + "\nedited in $EDITOR"), \
                 patch.object(api, "add_update_log_entry", wraps=api.add_update_log_entry) as save_call:
                await pilot.press("e")
                await pilot.pause()
                await pilot.pause()
                self.assertEqual(type(app.screen).__name__, "ConfirmScreen")

                await pilot.press("enter")  # confirm button is focused -> Save
                await pilot.pause()
                await pilot.pause()

            self.assertEqual(type(app.screen).__name__, "BrowseScreen")
            saved_entry = save_call.call_args.kwargs["log_entry"]
            self.assertIn("edited in $EDITOR", saved_entry.log_entry)


class ThemePersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_saved_theme_falls_back_to_default(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        with patch("bely_cli.tui.app.config.get_setting", return_value=None), \
             patch("bely_cli.tui.app.config.set_setting") as set_setting:
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertEqual(app.theme, "textual-dark")
            set_setting.assert_not_called()

    async def test_saved_valid_theme_is_loaded_without_repersisting(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        with patch("bely_cli.tui.app.config.get_setting", return_value="nord"), \
             patch("bely_cli.tui.app.config.set_setting") as set_setting:
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertEqual(app.theme, "nord")
            set_setting.assert_not_called()

    async def test_unknown_saved_theme_falls_back_to_default(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        with patch("bely_cli.tui.app.config.get_setting", return_value="not-a-real-theme"), \
             patch("bely_cli.tui.app.config.set_setting"):
            async with app.run_test() as pilot:
                await pilot.pause()
                self.assertEqual(app.theme, "textual-dark")

    async def test_changing_theme_after_mount_persists_it(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(FakeSession(data), limit=10, mode="lookup")
        with patch("bely_cli.tui.app.config.get_setting", return_value=None), \
             patch("bely_cli.tui.app.config.set_setting") as set_setting:
            async with app.run_test() as pilot:
                await pilot.pause()
                app.theme = "gruvbox"
                await pilot.pause()
            set_setting.assert_called_once_with("theme", "gruvbox")


async def _wait_until(pilot, predicate, attempts=30):
    """Poll for `predicate()`; pilot.pause() alone can return before _fetch_image's worker thread lands."""
    for _ in range(attempts):
        if predicate():
            return
        await pilot.pause(0.01)
    raise AssertionError("condition never became true")


class ImagePreviewTests(unittest.IsolatedAsyncioTestCase):
    """BrowseScreen's image-segment rendering path; patches decode_image_bytes so no Pillow install is needed."""

    def _make_app(self, *, image_widgets):
        data = LogbookData(FakeLogbookApiWithImage(), FakeDownloadApi())
        app = BelyTuiApp(
            FakeSession(data), limit=10, mode="lookup", image_widgets=image_widgets)
        return app

    async def test_image_only_entry_renders_fake_widget_and_hides_markdown(self):
        app = self._make_app(image_widgets={"auto": FakeImageWidget})
        with patch("bely_cli.tui.app.config.get_setting", return_value=None), \
             patch.object(browse, "decode_image_bytes", return_value="decoded-image"):
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("enter")  # type -> docs
                await pilot.pause()
                await pilot.press("enter")  # docs -> entries
                await pilot.pause()
                await pilot.pause()

                screen = app.screen
                body_blocks = screen.query_one("#body-blocks", Vertical)
                await _wait_until(pilot, lambda: screen.query(FakeImageWidget))

                self.assertFalse(screen.query_one("#body-md", Markdown).display)
                self.assertTrue(body_blocks.display)
                images = list(screen.query(FakeImageWidget))
                self.assertEqual(len(images), 1)
                self.assertEqual(images[0].image, "decoded-image")
                # The markdown segment before the image is still rendered.
                markdown_segments = list(body_blocks.query(Markdown))
                self.assertEqual(len(markdown_segments), 1)

    async def test_no_image_widget_falls_back_to_plain_markdown(self):
        # image_widgets={} -- as if textual_image weren't installed, or images: off.
        app = self._make_app(image_widgets={})
        with patch("bely_cli.tui.app.config.get_setting", return_value=None):
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()

                screen = app.screen
                self.assertTrue(screen.query_one("#body-md", Markdown).display)
                self.assertFalse(screen.query_one("#body-blocks", Vertical).display)
                self.assertEqual(len(list(screen.query(FakeImageWidget))), 0)

    async def test_non_image_entry_uses_plain_markdown_even_with_image_widget(self):
        # FakeLogbookApi (not the *WithImage variant): text-only entry, so the
        # fast path applies even though an image widget is available.
        data = LogbookData(FakeLogbookApi(), FakeDownloadApi())
        app = BelyTuiApp(
            FakeSession(data), limit=10, mode="lookup",
            image_widgets={"auto": FakeImageWidget})
        with patch("bely_cli.tui.app.config.get_setting", return_value=None):
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()

                screen = app.screen
                self.assertTrue(screen.query_one("#body-md", Markdown).display)
                self.assertFalse(screen.query_one("#body-blocks", Vertical).display)

    async def test_image_fetch_failure_shows_error_placeholder(self):
        app = self._make_app(image_widgets={"auto": FakeImageWidget})
        with patch("bely_cli.tui.app.config.get_setting", return_value=None), \
             patch.object(browse, "decode_image_bytes", side_effect=RuntimeError("bad image")):
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()

                screen = app.screen

                def has_error():
                    return screen.query(".img-error")

                await _wait_until(pilot, has_error)
                self.assertEqual(len(list(screen.query(FakeImageWidget))), 0)

    async def test_switching_entries_before_fetch_completes_does_not_mount_stale_image(self):
        """Arrowing away mid-fetch must not land an image in the wrong entry's preview."""
        import threading

        class TwoEntryApi(FakeLogbookApiWithImage):
            def get_log_entries(self, log_document_id, load_replies, load_reactions):
                return super().get_log_entries(log_document_id, load_replies, load_reactions) + [
                    SimpleNamespace(
                        log_id=200, entered_by_username="alice", entered_on_date_time=None,
                        last_modified_by_username=None, last_modified_on_date_time=None,
                        log_replies=None, log_reactions=None, log_entry="Plain second entry.",
                    ),
                ]

        data = LogbookData(TwoEntryApi(), FakeDownloadApi())
        app = BelyTuiApp(
            FakeSession(data), limit=10, mode="lookup",
            image_widgets={"auto": FakeImageWidget})
        release = threading.Event()

        def slow_decode(data):
            # Block the worker thread until the test moves the cursor away.
            release.wait(timeout=2)
            return "decoded-image"

        with patch("bely_cli.tui.app.config.get_setting", return_value=None), \
             patch.object(browse, "decode_image_bytes", side_effect=slow_decode):
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()

                screen = app.screen
                self.assertEqual(screen._entry_key, (10, 100))

                await pilot.press("down")  # move to the second (image-free) entry
                await pilot.pause()
                await pilot.pause()
                self.assertEqual(screen._entry_key, (10, 200))

                release.set()
                await _wait_until(pilot, lambda: True, attempts=5)  # let the worker drain

                self.assertEqual(len(list(screen.query(FakeImageWidget))), 0)


if __name__ == "__main__":
    unittest.main()
