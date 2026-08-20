"""BrowseScreen: logbook type -> document -> entry drill-down with a live preview.

This is the entry screen for both `bely-cli tui` modes -- BelyTuiApp pushes it
directly on mount, there is no separate landing/home screen:
  - `bely-cli tui lookup` (select_mode=True, source="types"): the original
    select-and-exit contract. Enter on an entry exits the app with
    (doc, entry).
  - `bely-cli tui` (select_mode=False): Enter on an entry is a no-op (the
    preview is already live). source="recent" starts at the document level
    with the current user's recently modified documents
    (core.recent_documents) instead of drilling in from logbook types.

Escape at the top level pops back to whatever pushed this screen, or (when `root=True`) does nothing -- `q` quits instead.

All three levels (types/docs/entries) render as one #nav-table DataTable, so
navigation, filtering, and the info/full-width toggles share a single code
path. All network calls go through LogbookData/`core` inside worker methods
so the UI never blocks on belyApi's synchronous HTTP calls: plain fetches use
`@work(thread=True)` + `call_from_thread`; the mutation keys ('n'/'u'/'d') use
a plain async `@work` so they can `await` the auth gate and a modal screen.
"""

import asyncio
from functools import partial

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Markdown, Static

from ... import config
from . import rows_table
from ..format import (
    DOC_COLUMNS,
    ENTRY_COLUMNS,
    TYPE_COLUMNS,
    doc_metadata_rows,
    doc_row,
    entry_metadata_rows,
    entry_node_row,
    entry_row,
    filter_items,
    flatten_entries,
    format_attachment,
    format_doc,
    format_type,
    reference_command,
    type_metadata_rows,
    type_row,
)
from ..mdimages import split_entry_markdown

LEVEL_TITLES = {0: "Logbooks", 1: "Documents", 2: "Entries"}


def decode_image_bytes(data):
    """Decode raw image bytes into a PIL Image, fully loaded; separate so tests can patch it without Pillow."""
    import io

    from PIL import Image as PILImage

    image = PILImage.open(io.BytesIO(data))
    image.load()  # decode fully while still off the event loop
    return image


class BrowseScreen(Screen):
    """Logbook type -> document -> entry drill-down with a live preview."""

    LEVEL_TYPES, LEVEL_DOCS, LEVEL_ENTRIES = range(3)

    LEVEL_COLUMNS = {LEVEL_TYPES: TYPE_COLUMNS, LEVEL_DOCS: DOC_COLUMNS, LEVEL_ENTRIES: ENTRY_COLUMNS}
    LEVEL_ROW_FN = {LEVEL_TYPES: type_row, LEVEL_DOCS: doc_row, LEVEL_ENTRIES: entry_node_row}
    # Entries render via entry_node_row (tree glyphs) but filter on the plain entry cells.
    LEVEL_SEARCH_FN = {LEVEL_ENTRIES: lambda node: entry_row(node.entry)}

    # Per-level nav pane width (%), used whenever a preview/info panel is visible.
    LEVEL_WIDTH = {LEVEL_TYPES: 42, LEVEL_DOCS: 60, LEVEL_ENTRIES: 42}

    # Which levels each action is relevant at. check_action() below returns
    # None for the rest, which hides the binding from the Footer entirely
    # (rather than showing it disabled) so only relevant keys ever appear.
    ACTION_LEVELS = {
        "toggle_full": (LEVEL_ENTRIES,),
        "save_entry": (LEVEL_ENTRIES,),
        "copy_reference": (LEVEL_ENTRIES,),
        "open_editor": (LEVEL_ENTRIES,),
        "update_entry": (LEVEL_ENTRIES,),
        "new_entry": (LEVEL_DOCS, LEVEL_ENTRIES),
        "new_doc": (LEVEL_TYPES, LEVEL_DOCS),
        "toggle_info": (LEVEL_TYPES, LEVEL_DOCS),
    }

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("backspace", "back", "Back", show=False),
        Binding("q", "quit_app", "Quit"),
        Binding("slash", "focus_filter", "Filter"),
        Binding("f", "toggle_full", "Full"),
        Binding("s", "save_entry", "Save"),
        Binding("y", "copy_reference", "Copy ref"),
        Binding("e", "open_editor", "Edit in editor"),
        Binding("n", "new_entry", "New entry"),
        Binding("u", "update_entry", "Edit in TUI"),
        Binding("d", "new_doc", "New doc"),
        Binding("r", "refresh_level", "Refresh"),
        Binding("i", "toggle_info", "Info"),
    ]

    def __init__(self, session, limit, *, select_mode=True, source="types", root=False):
        super().__init__()
        self.session = session
        self.data = session.data
        self.limit = limit
        self.select_mode = select_mode
        self.source = source
        self.root = root
        self.level = self.LEVEL_DOCS if source == "recent" else self.LEVEL_TYPES
        self.sel_type = None
        self.sel_doc = None
        self.all_items = []
        self.shown_items = []
        self.entry_tree = []
        self._collapsed = set()
        self._entry_key = None
        self._render_token = 0
        self._nav_hidden = False
        self._info_open = False
        self._table_columns_for = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield DataTable(id="nav-table", cursor_type="row", zebra_stripes=True)
            with VerticalScroll(id="preview"):
                yield Static(id="meta")
                yield Markdown(id="body-md")
                yield Vertical(id="body-blocks")
        with Horizontal(id="status-bar"):
            yield Static(id="status-left")
            yield Input(id="filter", placeholder="type to filter", compact=True)
            yield Static(id="status-right")
        yield Footer()

    def on_mount(self):
        self.query_one("#body-md", Markdown).display = False
        self.query_one("#body-blocks", Vertical).display = False
        self.query_one("#filter", Input).display = False
        self._update_auth_status()
        self.show_level(self.level)

    def on_screen_resume(self):
        self._update_auth_status()

    # -- nav widget --

    def _nav(self):
        return self.query_one("#nav-table", DataTable)

    def _preview_visible(self):
        """Entries always show the preview; other levels only with the 'i' toggle on."""
        return self.level == self.LEVEL_ENTRIES or self._info_open

    def _sync_panes(self):
        table = self._nav()
        table.display = not self._nav_hidden
        preview_on = self._preview_visible()
        self.query_one("#preview", VerticalScroll).display = preview_on
        table.styles.width = f"{self.LEVEL_WIDTH[self.level]}%" if preview_on else "100%"
        table.border_title = LEVEL_TITLES[self.level]
        self.query_one("#preview", VerticalScroll).border_title = (
            "Entry" if self.level == self.LEVEL_ENTRIES else "Details"
        )

    def _ensure_columns(self):
        """(Re)build #nav-table's columns when the level's column set changes."""
        if self._table_columns_for == self.level:
            return
        table = self._nav()
        table.clear(columns=True)
        for label, width in self.LEVEL_COLUMNS[self.level]:
            table.add_column(label, width=width)
        self._table_columns_for = self.level

    # -- level loading --

    def show_level(self, level, *, preserve_filter=False):
        self.level = level
        # "f" full-screen and the reply tree only apply at the entries level; reset when leaving.
        if level != self.LEVEL_ENTRIES:
            self._nav_hidden = False
            self.entry_tree = []
            self._collapsed = set()
        # cancel any in-flight preview/image workers so a stale, now-mistyped item can't reach _show_preview
        self.app.workers.cancel_group(self, "preview")
        self.app.workers.cancel_group(self, "images")
        self._sync_panes()
        self.refresh_bindings()
        nav = self._nav()
        if not preserve_filter:
            # Avoid a stale-item preview if clearing the filter's async Changed lands before the new level's fetch does.
            self.all_items = []
            self.shown_items = []
            filt = self.query_one("#filter", Input)
            filt.value = ""
            filt.display = False
        nav.set_loading(True)
        self.query_one("#body-md", Markdown).display = False
        self.query_one("#body-blocks", Vertical).display = False
        self.query_one("#meta", Static).update("")
        if level == self.LEVEL_TYPES:
            self._load_types()
        elif level == self.LEVEL_DOCS:
            if self.source == "recent":
                self._load_recent_docs()
            else:
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
    def _load_recent_docs(self):
        try:
            username = self.session.username()
            if not username:
                raise RuntimeError("cannot determine username. Set BELY_USER or 'user' in settings.")
            items = self.data.recent_documents(self.session.factory, username, self.limit)
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
            self.level = self.LEVEL_TYPES if self.source == "types" else self.LEVEL_DOCS
        elif self.level == self.LEVEL_ENTRIES:
            self.level = self.LEVEL_DOCS
        self._sync_panes()
        self.refresh_bindings()
        self._update_header()

    def _populate(self, items):
        nav = self._nav()
        nav.set_loading(False)
        if self.level == self.LEVEL_ENTRIES:
            self.entry_tree = items
            items = flatten_entries(items, self._collapsed)
        self.all_items = items
        self._apply_filter("")
        self._update_header()
        nav.focus()

    def _apply_filter(self, query):
        row_fn = self.LEVEL_ROW_FN[self.level]
        search_fn = self.LEVEL_SEARCH_FN.get(self.level, row_fn)
        self.shown_items = filter_items(
            self.all_items, query,
            lambda it: " ".join(str(c) for c in search_fn(it)),
        )
        self._ensure_columns()
        table = self._nav()
        table.clear()
        self._update_status_left(query)
        if self.shown_items:
            for it in self.shown_items:
                table.add_row(*row_fn(it))
            # DataTable.clear() leaves the cursor at (0, 0); if it was
            # already there, RowHighlighted won't fire, so drive the
            # initial preview explicitly instead of relying on it.
            self.run_worker(partial(self._show_preview, self.shown_items[0]), exclusive=True, group="preview")
        else:
            self.query_one("#meta", Static).update("(no matches)")
            self.query_one("#body-md", Markdown).display = False
            self.query_one("#body-blocks", Vertical).display = False

    def _update_status_left(self, query):
        count = len(self.shown_items)
        total = len(self.all_items)
        noun = "row" if count == 1 else "rows"
        text = f"{count} {noun}" if count == total else f'filter "{query}" -- {count} of {total}'
        self.query_one("#status-left", Static).update(text)

    def _update_header(self):
        parts = []
        if self.sel_type is not None:
            parts.append(format_type(self.sel_type))
        if self.sel_doc is not None:
            parts.append(format_doc(self.sel_doc))
        if self.level == self.LEVEL_ENTRIES:
            parts.append("entries")
        self.sub_title = "  ›  ".join(parts)

    def _update_auth_status(self):
        username = self.session.username()
        if self.session.is_authenticated():
            status = f"{username or 'authenticated'}  ●"
        else:
            status = f"{username}  ○" if username else "no user configured"
        self.query_one("#status-right", Static).update(status)

    # -- preview --

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
            meta.update(rows_table(type_metadata_rows(item)))
        elif self.level == self.LEVEL_DOCS:
            meta.update(rows_table(doc_metadata_rows(item)))
        else:
            meta.update(rows_table(entry_metadata_rows(item.entry, self.sel_doc, parent=item.parent)))

    async def _show_preview(self, item):
        self._render_meta(item)
        body_md = self.query_one("#body-md", Markdown)
        body_blocks = self.query_one("#body-blocks", Vertical)
        if self.level != self.LEVEL_ENTRIES:
            body_md.display = False
            body_blocks.display = False
            return

        entry = item.entry
        key = (self.sel_doc.id, entry.log_id)
        self._entry_key = key
        self._load_attachments(item)

        segments = split_entry_markdown(entry.log_entry or "")
        widget_cls = getattr(self.app, "image_widget", None)
        image_segments_present = any(seg[0] == "image" for seg in segments)

        if widget_cls is None or not image_segments_present:
            if widget_cls is None and image_segments_present:
                self._maybe_hint_images_unavailable()
            body_blocks.display = False
            body_md.display = True
            await body_md.update(entry.log_entry or "")
            return

        body_md.display = False
        body_blocks.display = True
        await self._render_segments(key, segments, widget_cls)

    def _maybe_hint_images_unavailable(self):
        """Nudge toward the optional extra, once per session, unless images are off."""
        if getattr(self.app, "_images_hint_shown", False):
            return
        if config.get_setting("images") == "off":
            return
        self.app._images_hint_shown = True
        self.notify(
            "This entry has images -- install the optional extra to view them "
            "inline: pip install 'bely-cli[images]'",
            timeout=8,
            markup=False,
        )

    async def _render_segments(self, key, segments, widget_cls):
        """Mount markdown/image placeholders and fetch each image; _render_token guards _show_preview's double-call race."""
        self._render_token += 1
        token = self._render_token
        self.app.workers.cancel_group(self, "images")
        body_blocks = self.query_one("#body-blocks", Vertical)
        await body_blocks.remove_children()
        if key != self._entry_key or token != self._render_token:
            return

        widgets = []
        pending_images = []  # (placeholder, stored_name, alt)
        for segment in segments:
            if segment[0] == "markdown":
                widgets.append(Markdown(segment[1]))
            else:
                _, stored_name, alt = segment
                placeholder = Static(
                    f"\U0001f5bc  {alt or stored_name}  (loading...)", classes="img-loading")
                widgets.append(placeholder)
                pending_images.append((placeholder, stored_name, alt))

        await body_blocks.mount_all(widgets)
        if key != self._entry_key or token != self._render_token:
            return
        for placeholder, stored_name, alt in pending_images:
            self._fetch_image(key, token, stored_name, alt, placeholder, widget_cls)

    @work(thread=True, group="images")
    def _fetch_image(self, key, token, stored_name, alt, placeholder, widget_cls):
        try:
            data = self.data.attachment_bytes(stored_name)
            pil_image = decode_image_bytes(data)
        except Exception as e:
            self.app.call_from_thread(
                self._image_failed, key, token, placeholder, stored_name, str(e))
            return
        self.app.call_from_thread(self._apply_image, key, token, placeholder, widget_cls, pil_image)

    def _stale_render(self, key, token, placeholder):
        return key != self._entry_key or token != self._render_token or not placeholder.is_mounted

    async def _apply_image(self, key, token, placeholder, widget_cls, pil_image):
        if self._stale_render(key, token, placeholder):
            return
        image_widget = widget_cls(pil_image, classes="entry-image")
        await self.query_one("#body-blocks", Vertical).mount(image_widget, after=placeholder)
        await placeholder.remove()

    async def _image_failed(self, key, token, placeholder, stored_name, message):
        if self._stale_render(key, token, placeholder):
            return
        placeholder.update(f"\U0001f5bc  {stored_name}  (failed to load: {message})")
        placeholder.remove_class("img-loading")
        placeholder.add_class("img-error")

    def _load_attachments(self, node):
        self._fetch_attachments(self.sel_doc.id, node.entry.log_id, node, self._entry_key)

    @work(thread=True, exclusive=True, group="attachments")
    def _fetch_attachments(self, doc_id, log_id, node, key):
        try:
            attachments = self.data.attachments(doc_id, log_id)
        except Exception:
            attachments = []
        self.app.call_from_thread(self._apply_attachments, key, node, attachments)

    def _apply_attachments(self, key, node, attachments):
        if key != self._entry_key or not attachments:
            return
        meta = self.query_one("#meta", Static)
        rows = entry_metadata_rows(node.entry, self.sel_doc, parent=node.parent)
        rows.append(("attachments", "; ".join(format_attachment(a) for a in attachments)))
        meta.update(rows_table(rows))

    # -- filter input --

    def on_input_changed(self, event):
        if event.input.id == "filter":
            self._apply_filter(event.value)

    def on_input_submitted(self, event):
        if event.input.id == "filter":
            self._nav().focus()
            event.input.display = bool(event.input.value)

    # -- selection / navigation --

    def on_data_table_row_selected(self, event):
        if event.data_table.id != "nav-table":
            return
        if event.cursor_row >= len(self.shown_items):
            return
        item = self.shown_items[event.cursor_row]
        if self.level == self.LEVEL_TYPES:
            self.sel_type = item
            self.show_level(self.LEVEL_DOCS)
        elif self.level == self.LEVEL_DOCS:
            self.sel_doc = item
            self.show_level(self.LEVEL_ENTRIES)
        elif self.select_mode:
            self.app.exit((self.sel_doc, item.entry))
        # else: entry already selected is just the live preview; Enter is a no-op.

    def action_back(self):
        filter_input = self.query_one("#filter", Input)
        if filter_input.has_focus:
            self._nav().focus()
            filter_input.display = bool(filter_input.value)
            return
        if self.level == self.LEVEL_ENTRIES:
            self.sel_doc = None
            self.show_level(self.LEVEL_DOCS)
        elif self.level == self.LEVEL_DOCS and self.source == "types":
            self.sel_type = None
            self.show_level(self.LEVEL_TYPES)
        else:
            self._exit_top()

    def _exit_top(self):
        """Escape at the top level: pop back to whatever pushed this screen, or notify if this is the landing screen."""
        if not self.root:
            self.app.pop_screen()
            return
        self.notify("Press q to quit.")

    def action_quit_app(self):
        self.app.exit(None)

    def action_focus_filter(self):
        filt = self.query_one("#filter", Input)
        filt.display = True
        filt.focus()

    def action_toggle_full(self):
        self._nav_hidden = not self._nav_hidden
        self._sync_panes()

    def action_toggle_info(self):
        self._info_open = not self._info_open
        self._sync_panes()

    def check_action(self, action, parameters):
        levels = self.ACTION_LEVELS.get(action)
        return True if levels is None else (self.level in levels or None)

    def action_refresh_level(self):
        if self.level == self.LEVEL_TYPES:
            self.data.invalidate("types")
        elif self.level == self.LEVEL_DOCS:
            if self.source == "recent":
                self.data.invalidate("recent", username=self.session.username())
            else:
                self.data.invalidate("docs", type_id=self.sel_type.id)
        else:
            self.data.invalidate("entries", doc_id=self.sel_doc.id)
        self.show_level(self.level, preserve_filter=True)

    # -- current-selection helpers --

    def _current_node(self):
        if self.level != self.LEVEL_ENTRIES:
            return None
        table = self._nav()
        if table.cursor_row is None or table.cursor_row >= len(self.shown_items):
            return None
        return self.shown_items[table.cursor_row]

    def _current_entry(self):
        node = self._current_node()
        return node.entry if node else None

    def _current_doc(self):
        """The document the 'n'/'u' actions apply to: the drilled-into doc at the
        entry level, or the highlighted row at the doc level."""
        if self.level == self.LEVEL_ENTRIES:
            return self.sel_doc
        if self.level == self.LEVEL_DOCS:
            table = self._nav()
            if table.cursor_row is None or table.cursor_row >= len(self.shown_items):
                return None
            return self.shown_items[table.cursor_row]
        return None

    def _current_type(self):
        """The logbook type the 'd' (new document) action applies to: the
        drilled-into type at the doc level, or the highlighted row at the
        type level."""
        if self.level == self.LEVEL_DOCS:
            return self.sel_type
        if self.level == self.LEVEL_TYPES:
            table = self._nav()
            if table.cursor_row is None or table.cursor_row >= len(self.shown_items):
                return None
            return self.shown_items[table.cursor_row]
        return None

    # -- entry actions --

    def action_save_entry(self):
        from ...common import write_entry_to_file

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
        self._edit_entry_externally(entry)

    @work
    async def _edit_entry_externally(self, entry):
        from ...common import editor_changed, open_in_editor
        from .confirm import ConfirmScreen

        original = entry.log_entry or ""
        try:
            with self.app.suspend():
                edited = open_in_editor(original)
        except RuntimeError as e:
            self.notify(str(e), severity="error")
            return

        if not editor_changed(original, edited):
            self.notify("No changes made.")
            return

        save = await self.app.push_screen_wait(
            ConfirmScreen(
                f"Save changes to entry #{entry.log_id}?",
                confirm_label="Save",
                cancel_label="Discard",
            )
        )
        if not save:
            return

        api = await self.app.ensure_auth()
        if api is None:
            return

        from ... import core

        try:
            await asyncio.to_thread(core.save_entry, api, entry, edited)
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")
            return

        self.data.invalidate("entries", doc_id=self.sel_doc.id)
        self.show_level(self.LEVEL_ENTRIES, preserve_filter=True)
        self.notify("Entry saved.")

    # -- add / update entry (mutating: goes through the auth gate) --

    def action_new_entry(self):
        doc = self._current_doc()
        if doc is None:
            self.notify("Select a document first.", severity="warning")
            return
        self._run_compose(doc, None)

    def action_update_entry(self):
        entry = self._current_entry()
        if entry is None:
            self.notify("Select an entry first.", severity="warning")
            return
        self._run_compose(self.sel_doc, entry)

    @work
    async def _run_compose(self, doc, entry):
        """Authenticate, then push ComposeScreen for a new or existing entry."""
        from .compose import open_composer

        api = await self.app.ensure_auth()
        if api is None:
            return

        saved = await open_composer(self.app, doc, api, entry=entry)
        if not saved:
            return
        self.sel_doc = doc
        self.data.invalidate("entries", doc_id=doc.id)
        if self.level == self.LEVEL_ENTRIES:
            self.show_level(self.LEVEL_ENTRIES, preserve_filter=True)
        else:
            self.show_level(self.LEVEL_ENTRIES)

    # -- new document (mutating: goes through the auth gate) --

    def action_new_doc(self):
        self._run_new_doc()

    @work
    async def _run_new_doc(self):
        from .newdoc import NewDocScreen

        logbook_type = self._current_type()
        doc = await self.app.push_screen_wait(NewDocScreen(self.session, logbook_type=logbook_type))
        if doc is None:
            return
        self.notify(f'Document "{doc.name}" created.')
        if logbook_type is not None:
            self.data.invalidate("docs", type_id=logbook_type.id)
        username = self.session.username()
        if username:
            self.data.invalidate("recent", username=username)
        if self.level == self.LEVEL_DOCS:
            self.show_level(self.LEVEL_DOCS, preserve_filter=True)
