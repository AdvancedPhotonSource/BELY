import unittest
from types import SimpleNamespace

from textual.widgets import DataTable, Markdown, OptionList, Static

from bely_cli.tui.app import BelyTuiApp, BrowseScreen
from bely_cli.tui.data import LogbookData


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


class TuiAppSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_browse_populates_list_and_drives_preview(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(data, limit=10)
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
            nav = screen.query_one("#nav-list", OptionList)
            self.assertEqual(nav.option_count, 1)
            self.assertEqual(screen.shown_items[0].log_id, 100)
            self.assertTrue(screen.query_one("#body-md", Markdown).display)
            # Entries always show the preview, even though 'i' was never pressed.
            self.assertTrue(screen.query_one("#preview").display)

    async def test_info_toggle_at_table_levels(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(data, limit=10)
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
        app = BelyTuiApp(data, limit=10)
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
        app = BelyTuiApp(data, limit=10)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            screen._apply_filter("nonexistent")
            self.assertEqual(screen.shown_items, [])
            screen._apply_filter("")
            self.assertEqual(len(screen.shown_items), 1)

    async def test_filter_narrows_table_row_count(self):
        data = LogbookData(FakeLogbookApi())
        app = BelyTuiApp(data, limit=10)
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
        app = BelyTuiApp(data, limit=10)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen

            self.assertTrue(screen.check_action("toggle_info", ()))
            self.assertTrue(screen.check_action("refresh_level", ()))
            for action in screen.ENTRY_ONLY_ACTIONS:
                self.assertIsNone(screen.check_action(action, ()))

            await pilot.press("enter")  # type -> docs
            await pilot.pause()
            await pilot.press("enter")  # docs -> entries
            await pilot.pause()
            await pilot.pause()

            self.assertIsNone(screen.check_action("toggle_info", ()))
            for action in screen.ENTRY_ONLY_ACTIONS:
                self.assertTrue(screen.check_action(action, ()))

    async def test_search_and_resize_bindings_are_gone(self):
        keys = {b.key for b in BrowseScreen.BINDINGS}
        self.assertNotIn("ctrl+s", keys)
        self.assertNotIn("left_square_bracket", keys)
        self.assertNotIn("right_square_bracket", keys)


if __name__ == "__main__":
    unittest.main()
