"""Textual application for `bely-cli tui lookup`.

Master/detail browser: a nav widget on the left drills through logbook type ->
document -> entry. The logbook/document levels are full-width tables with an
optional side info panel ('i'); the entry level always shows a preview pane
(Rich metadata table + rendered markdown body) since the row itself is just a
one-line snippet. All network calls go through LogbookData inside
@work(thread=True) methods so the UI never blocks on belyApi's synchronous
HTTP calls.
"""

from rich.table import Table
from textual import work
from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Input, Markdown, OptionList, Static

from ..common import open_in_editor, write_entry_to_file
from .format import (
    DOC_COLUMNS,
    TYPE_COLUMNS,
    doc_metadata_rows,
    doc_row,
    entry_metadata_rows,
    entry_row,
    filter_items,
    format_attachment,
    format_doc,
    format_type,
    reference_command,
    type_metadata_rows,
    type_row,
)


def _rows_table(rows):
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column(ratio=1)
    for label, value in rows:
        table.add_row(label, value)
    return table


class BrowseScreen(Screen):
    """Logbook type -> document -> entry drill-down with a live preview."""

    LEVEL_TYPES, LEVEL_DOCS, LEVEL_ENTRIES = range(3)

    # Levels rendered as a DataTable; LEVEL_ENTRIES stays an OptionList.
    TABLE_LEVELS = (LEVEL_TYPES, LEVEL_DOCS)
    LEVEL_COLUMNS = {LEVEL_TYPES: TYPE_COLUMNS, LEVEL_DOCS: DOC_COLUMNS}
    LEVEL_ROW_FN = {LEVEL_TYPES: type_row, LEVEL_DOCS: doc_row, LEVEL_ENTRIES: entry_row}

    # Per-level nav pane width (%), used whenever a preview/info panel is visible.
    LEVEL_WIDTH = {LEVEL_TYPES: 42, LEVEL_DOCS: 60, LEVEL_ENTRIES: 42}

    # Actions that only make sense at one kind of level. check_action() below
    # returns None for the rest, which hides the binding from the Footer
    # entirely (rather than showing it disabled) so only relevant keys appear.
    ENTRY_ONLY_ACTIONS = frozenset(
        {"toggle_full", "save_entry", "copy_reference", "open_editor"}
    )
    TABLE_ONLY_ACTIONS = frozenset({"toggle_info"})

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("backspace", "back", "Back", show=False),
        Binding("q", "quit_app", "Quit"),
        Binding("slash", "focus_filter", "Filter"),
        Binding("f", "toggle_full", "Full"),
        Binding("s", "save_entry", "Save"),
        Binding("y", "copy_reference", "Copy ref"),
        Binding("e", "open_editor", "Editor"),
        Binding("r", "refresh_level", "Refresh"),
        Binding("i", "toggle_info", "Info"),
    ]

    def __init__(self, data, limit):
        super().__init__()
        self.data = data
        self.limit = limit
        self.level = self.LEVEL_TYPES
        self.sel_type = None
        self.sel_doc = None
        self.all_items = []
        self.shown_items = []
        self._entry_key = None
        self._nav_hidden = False
        self._info_open = False
        self._table_columns_for = None

    def compose(self):
        yield Static(id="breadcrumb")
        with Horizontal(id="body"):
            yield DataTable(id="nav-table", cursor_type="row", zebra_stripes=True)
            yield OptionList(id="nav-list")
            with VerticalScroll(id="preview"):
                yield Static(id="meta")
                yield Markdown(id="body-md")
        with Horizontal(id="filter-bar"):
            yield Static("Filter:", id="filter-label")
            yield Input(id="filter", placeholder="type to filter, / to focus")
        yield Footer()

    def on_mount(self):
        self.query_one("#body-md", Markdown).display = False
        self.show_level(self.LEVEL_TYPES)

    # -- nav widget (table for types/docs, list for entries) --

    def _nav(self):
        """The nav widget backing the current level."""
        if self.level in self.TABLE_LEVELS:
            return self.query_one("#nav-table", DataTable)
        return self.query_one("#nav-list", OptionList)

    def _preview_visible(self):
        """Entries always show the preview; table levels only with the 'i' toggle on."""
        return self.level == self.LEVEL_ENTRIES or self._info_open

    def _sync_panes(self):
        """Show the right widget(s) for the current level/toggles and size the nav pane.

        Table levels default to a full-width table with no preview; the entry level
        always shows the preview (it's the reading pane, not a duplicate of the row).
        """
        use_table = self.level in self.TABLE_LEVELS
        table = self.query_one("#nav-table", DataTable)
        lst = self.query_one("#nav-list", OptionList)
        table.display = use_table and not self._nav_hidden
        lst.display = (not use_table) and not self._nav_hidden
        preview_on = self._preview_visible()
        self.query_one("#preview", VerticalScroll).display = preview_on
        nav = table if use_table else lst
        nav.set_class(not preview_on, "-full-width")
        nav.styles.width = f"{self.LEVEL_WIDTH[self.level]}%" if preview_on else "100%"

    def _ensure_columns(self):
        """(Re)build #nav-table's columns when the level's column set changes."""
        if self.level not in self.TABLE_LEVELS:
            return
        if self._table_columns_for == self.level:
            return
        table = self.query_one("#nav-table", DataTable)
        table.clear(columns=True)
        for label, width in self.LEVEL_COLUMNS[self.level]:
            table.add_column(label, width=width)
        self._table_columns_for = self.level

    # -- level loading --

    def show_level(self, level, *, preserve_filter=False):
        self.level = level
        self._sync_panes()
        self.refresh_bindings()
        nav = self._nav()
        if not preserve_filter:
            self.query_one("#filter", Input).value = ""
        nav.set_loading(True)
        self.query_one("#body-md", Markdown).display = False
        self.query_one("#meta", Static).update("")
        if level == self.LEVEL_TYPES:
            self._load_types()
        elif level == self.LEVEL_DOCS:
            self._load_docs(self.sel_type.id)
        else:
            self._load_entries(self.sel_doc.id)

    @work(thread=True, exclusive=True, group="fetch")
    def _load_types(self):
        try:
            items = self.data.logbook_types()
        except Exception as e:
            self.app.call_from_thread(self._fetch_failed, str(e))
            return
        self.app.call_from_thread(self._populate, items)

    @work(thread=True, exclusive=True, group="fetch")
    def _load_docs(self, type_id):
        try:
            items = self.data.documents(type_id, self.limit)
        except Exception as e:
            self.app.call_from_thread(self._fetch_failed, str(e))
            return
        self.app.call_from_thread(self._populate, items)

    @work(thread=True, exclusive=True, group="fetch")
    def _load_entries(self, doc_id):
        try:
            items = self.data.entries(doc_id)
        except Exception as e:
            self.app.call_from_thread(self._fetch_failed, str(e))
            return
        self.app.call_from_thread(self._populate, items)

    def _fetch_failed(self, message):
        self._nav().set_loading(False)
        self.notify(f"Fetch failed: {message}", severity="error", timeout=6)
        if self.level == self.LEVEL_DOCS:
            self.level = self.LEVEL_TYPES
        elif self.level == self.LEVEL_ENTRIES:
            self.level = self.LEVEL_DOCS
        self._sync_panes()
        self.refresh_bindings()
        self._update_breadcrumb()

    def _populate(self, items):
        nav = self._nav()
        nav.set_loading(False)
        self.all_items = items
        self._apply_filter("")
        self._update_breadcrumb()
        nav.focus()

    def _apply_filter(self, query):
        row_fn = self.LEVEL_ROW_FN[self.level]
        self.shown_items = filter_items(
            self.all_items, query,
            lambda it: " ".join(str(c) for c in row_fn(it)),
        )
        if self.level in self.TABLE_LEVELS:
            self._ensure_columns()
            table = self.query_one("#nav-table", DataTable)
            table.clear()
            if self.shown_items:
                for it in self.shown_items:
                    table.add_row(*row_fn(it))
                # DataTable.clear() leaves the cursor at (0, 0); if it was
                # already there, RowHighlighted won't fire, so drive the
                # initial preview explicitly instead of relying on it.
                self._render_meta(self.shown_items[0])
                self.query_one("#body-md", Markdown).display = False
            else:
                self.query_one("#meta", Static).update("(no matches)")
                self.query_one("#body-md", Markdown).display = False
        else:
            nav = self.query_one("#nav-list", OptionList)
            nav.clear_options()
            if self.shown_items:
                nav.add_options([row_fn(it)[0] for it in self.shown_items])
                nav.highlighted = 0
            else:
                self.query_one("#meta", Static).update("(no matches)")
                self.query_one("#body-md", Markdown).display = False

    def _update_breadcrumb(self):
        parts = ["BELY"]
        if self.sel_type is not None:
            parts.append(format_type(self.sel_type))
        if self.sel_doc is not None:
            parts.append(format_doc(self.sel_doc))
        if self.level == self.LEVEL_ENTRIES:
            parts.append("entries")
        self.query_one("#breadcrumb", Static).update("  ›  ".join(parts))

    # -- preview --

    async def on_option_list_option_highlighted(self, event):
        if event.option_list.id != "nav-list":
            return
        item = self.shown_items[event.option_index]
        await self._show_preview(item)

    async def on_data_table_row_highlighted(self, event):
        if event.data_table.id != "nav-table":
            return
        if event.cursor_row >= len(self.shown_items):
            return
        item = self.shown_items[event.cursor_row]
        await self._show_preview(item)

    def _render_meta(self, item):
        """Sync metadata render for the current level (types/docs have no async work)."""
        meta = self.query_one("#meta", Static)
        if self.level == self.LEVEL_TYPES:
            meta.update(_rows_table(type_metadata_rows(item)))
        elif self.level == self.LEVEL_DOCS:
            meta.update(_rows_table(doc_metadata_rows(item)))
        else:
            meta.update(_rows_table(entry_metadata_rows(item, self.sel_doc)))

    async def _show_preview(self, item):
        self._render_meta(item)
        body_md = self.query_one("#body-md", Markdown)
        if self.level == self.LEVEL_ENTRIES:
            body_md.display = True
            await body_md.update(item.log_entry or "")
            self._load_attachments(item)
        else:
            body_md.display = False

    def _load_attachments(self, entry):
        key = (self.sel_doc.id, entry.log_id)
        self._entry_key = key
        self._fetch_attachments(self.sel_doc.id, entry.log_id, entry, key)

    @work(thread=True, exclusive=True, group="attachments")
    def _fetch_attachments(self, doc_id, log_id, entry, key):
        try:
            attachments = self.data.attachments(doc_id, log_id)
        except Exception:
            attachments = []
        self.app.call_from_thread(self._apply_attachments, key, entry, attachments)

    def _apply_attachments(self, key, entry, attachments):
        if key != self._entry_key or not attachments:
            return
        meta = self.query_one("#meta", Static)
        rows = entry_metadata_rows(entry, self.sel_doc)
        rows.append(("attachments", "; ".join(format_attachment(a) for a in attachments)))
        meta.update(_rows_table(rows))

    # -- filter input --

    def on_input_changed(self, event):
        if event.input.id == "filter":
            self._apply_filter(event.value)

    def on_input_submitted(self, event):
        if event.input.id == "filter":
            self._nav().focus()

    # -- selection / navigation --

    def on_option_list_option_selected(self, event):
        if event.option_list.id != "nav-list":
            return
        item = self.shown_items[event.option_index]
        if self.level == self.LEVEL_TYPES:
            self.sel_type = item
            self.show_level(self.LEVEL_DOCS)
        elif self.level == self.LEVEL_DOCS:
            self.sel_doc = item
            self.show_level(self.LEVEL_ENTRIES)
        else:
            self.app.exit((self.sel_doc, item))

    def on_data_table_row_selected(self, event):
        if event.data_table.id != "nav-table":
            return
        if event.cursor_row >= len(self.shown_items):
            return
        item = self.shown_items[event.cursor_row]
        if self.level == self.LEVEL_TYPES:
            self.sel_type = item
            self.show_level(self.LEVEL_DOCS)
        else:
            self.sel_doc = item
            self.show_level(self.LEVEL_ENTRIES)

    def action_back(self):
        filter_input = self.query_one("#filter", Input)
        if filter_input.has_focus:
            self._nav().focus()
            return
        if self.level == self.LEVEL_ENTRIES:
            self.sel_doc = None
            self.show_level(self.LEVEL_DOCS)
        elif self.level == self.LEVEL_DOCS:
            self.sel_type = None
            self.show_level(self.LEVEL_TYPES)
        else:
            self.app.exit(None)

    def action_quit_app(self):
        self.app.exit(None)

    def action_focus_filter(self):
        self.query_one("#filter", Input).focus()

    def action_toggle_full(self):
        self._nav_hidden = not self._nav_hidden
        self._sync_panes()

    def action_toggle_info(self):
        self._info_open = not self._info_open
        self._sync_panes()

    def check_action(self, action, parameters):
        if action in self.ENTRY_ONLY_ACTIONS:
            return self.level == self.LEVEL_ENTRIES or None
        if action in self.TABLE_ONLY_ACTIONS:
            return self.level in self.TABLE_LEVELS or None
        return True

    def action_refresh_level(self):
        if self.level == self.LEVEL_TYPES:
            self.data.invalidate("types")
        elif self.level == self.LEVEL_DOCS:
            self.data.invalidate("docs", type_id=self.sel_type.id)
        else:
            self.data.invalidate("entries", doc_id=self.sel_doc.id)
        self.show_level(self.level, preserve_filter=True)

    # -- entry actions --

    def _current_entry(self):
        if self.level != self.LEVEL_ENTRIES:
            return None
        nav = self.query_one("#nav-list", OptionList)
        if nav.highlighted is None or not self.shown_items:
            return None
        return self.shown_items[nav.highlighted]

    def action_save_entry(self):
        entry = self._current_entry()
        if entry is None:
            self.notify("Select an entry first.", severity="warning")
            return
        doc_name = getattr(self.sel_doc, "name", None) or str(self.sel_doc.id)
        try:
            path = write_entry_to_file(entry, doc_name, output_dir=None, fmt="text", quiet=True)
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")
            return
        self.notify(f"Saved to {path}")

    def action_copy_reference(self):
        entry = self._current_entry()
        if entry is None:
            self.notify("Select an entry first.", severity="warning")
            return
        ref = reference_command(self.sel_doc.id, entry.log_id)
        self.app.copy_to_clipboard(ref)
        self.notify(f"Copied: {ref}")

    def action_open_editor(self):
        entry = self._current_entry()
        if entry is None:
            self.notify("Select an entry first.", severity="warning")
            return
        with self.app.suspend():
            open_in_editor(entry.log_entry or "")
        self.notify("Back from editor (view-only; nothing was saved).")


class BelyTuiApp(App):
    """Top-level app: pushes BrowseScreen and returns its exit result."""

    TITLE = "BELY"

    CSS = """
    #breadcrumb {
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
    }

    #body {
        height: 1fr;
    }

    #nav-list, #nav-table {
        border-right: solid $primary;
    }

    #nav-list.-full-width, #nav-table.-full-width {
        border-right: none;
    }

    #preview {
        width: 1fr;
        padding: 0 1;
    }

    #meta {
        height: auto;
        border-bottom: solid $primary-darken-1;
        margin-bottom: 1;
    }

    #filter-bar {
        height: 1;
        padding: 0 1;
    }

    #filter-label {
        width: auto;
        padding-right: 1;
    }

    #filter {
        width: 1fr;
    }
    """

    def __init__(self, data, limit=100):
        super().__init__()
        self.data = data
        self.limit = limit

    def on_mount(self):
        self.push_screen(BrowseScreen(self.data, self.limit))
