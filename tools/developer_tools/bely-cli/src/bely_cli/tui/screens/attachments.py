"""Attachment browser for a selected log entry."""

import asyncio
import os
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.suggester import Suggester
from textual.widgets import DataTable, DirectoryTree, Footer, Input, Markdown, Static

from ... import core
from ...common import format_error_message
from .confirm import ConfirmScreen
from .dialog import DialogScreen, LoadingScreen


_IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
_TEXT_EXTENSIONS = {
    ".csv", ".json", ".log", ".md", ".markdown", ".rst", ".text", ".txt", ".xml", ".yaml", ".yml",
}


def preview_kind(filename):
    """Classify an attachment as image, text, or metadata-only."""
    suffix = os.path.splitext(filename or "")[1].lower()
    if suffix in _IMAGE_EXTENSIONS:
        return "image"
    if suffix in _TEXT_EXTENSIONS:
        return "text"
    return "metadata"


class PathSuggester(Suggester):
    """Offer shell-like completion for local filesystem paths."""

    def __init__(self):
        super().__init__(use_cache=False, case_sensitive=True)

    async def get_suggestion(self, value):
        if not value:
            return None
        return await asyncio.to_thread(self._suggest, value)

    @staticmethod
    def _suggest(value):
        expanded = Path(value).expanduser()
        if value.endswith(os.sep):
            directory, prefix, base = expanded, "", value
        else:
            directory, prefix = expanded.parent, expanded.name
            base = value[:-len(prefix)] if prefix else value
        try:
            matches = sorted(
                (path for path in directory.iterdir() if path.name.startswith(prefix)),
                key=lambda path: (not path.is_dir(), path.name.casefold()),
            )
        except OSError:
            return None
        if not matches:
            return None
        match = matches[0]
        return f"{base}{match.name}{os.sep if match.is_dir() else ''}"


class PathInput(Input):
    """Path input where Tab accepts Textual's current suggestion."""

    BINDINGS = [
        Binding("tab", "complete", "Complete", show=False),
        Binding("ctrl+u", "clear_path", "Clear path", show=False),
    ]

    def action_complete(self):
        self.action_cursor_right()

    def action_clear_path(self):
        self.value = ""


class AttachmentDirectoryTree(DirectoryTree):
    """Directory tree with a slash-triggered name filter."""

    BINDINGS = [Binding("slash", "filter", "Filter", show=False)]

    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)
        self.filter_text = ""

    def filter_paths(self, paths):
        paths = super().filter_paths(paths)
        if not self.filter_text:
            return paths
        query = self.filter_text.casefold()
        return (
            path for path in paths
            if path.is_dir() or query in path.name.casefold()
        )

    def action_filter(self):
        self.screen.open_tree_filter()


class TreeFilterInput(Input):
    """Filter input whose Escape returns to the directory tree."""

    BINDINGS = [Binding("escape", "close_filter", "Close filter", show=False)]

    def action_close_filter(self):
        self.screen.close_tree_filter()


class AttachmentFileScreen(DialogScreen):
    """Select and preview a local attachment with Textual's filesystem browser."""

    DEFAULT_CSS = """
    #attachment-file-dialog { width: 80%; height: 80%; }
    #attachment-root { margin-top: 1; }
    #attachment-filter { display: none; margin-top: 1; }
    #attachment-file-body { height: 1fr; margin-top: 1; }
    #attachment-file-tree { width: 55%; }
    #attachment-file-preview { width: 1fr; border: round $primary-darken-1; padding: 0 1; }
    #attachment-file-image { width: auto; height: auto; max-width: 100%; max-height: 30; }
    """

    BINDINGS = [Binding("p", "toggle_preview", "Preview")]

    def __init__(self, path=None):
        super().__init__()
        self.path = path or os.getcwd()
        self._preview_open = True
        self._preview_token = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="attachment-file-dialog", classes="dialog"):
            yield Static("Select a local file to upload")
            yield PathInput(
                value=str(self.path), placeholder="Directory or file path",
                suggester=PathSuggester(), id="attachment-root",
            )
            yield TreeFilterInput(placeholder="Filter filenames", id="attachment-filter")
            with Horizontal(id="attachment-file-body"):
                yield AttachmentDirectoryTree(self.path, id="attachment-file-tree")
                with VerticalScroll(id="attachment-file-preview"):
                    yield Static("Highlight a file to preview it.", id="attachment-file-meta")
                    yield Markdown(id="attachment-file-text")
                    yield Vertical(id="attachment-file-media")
            yield Static(
                "Path: Ctrl+U clear · Ctrl+Shift+A select all · Tab/Right complete · Enter open\n"
                "Tree: / filter · p preview · Enter select/open · Esc cancel",
                classes="help-text",
            )

    def on_mount(self):
        root = self.query_one("#attachment-root", Input)
        root.cursor_position = len(root.value)
        root.focus()
        self.query_one("#attachment-file-text", Markdown).display = False

    def action_toggle_preview(self):
        self._preview_open = not self._preview_open
        preview = self.query_one("#attachment-file-preview", VerticalScroll)
        tree = self.query_one(AttachmentDirectoryTree)
        preview.display = self._preview_open
        tree.styles.width = "55%" if self._preview_open else "100%"

    def open_tree_filter(self):
        filter_input = self.query_one("#attachment-filter", Input)
        filter_input.display = True
        filter_input.focus()

    def close_tree_filter(self):
        filter_input = self.query_one("#attachment-filter", Input)
        filter_input.display = False
        self.query_one(AttachmentDirectoryTree).focus()

    async def on_input_changed(self, event):
        if event.input.id != "attachment-filter":
            return
        tree = self.query_one(AttachmentDirectoryTree)
        tree.filter_text = event.value
        await tree.reload()

    def on_input_submitted(self, event):
        if event.input.id == "attachment-filter":
            self.close_tree_filter()
            return
        if event.input.id != "attachment-root":
            return
        path = Path(event.value).expanduser()
        try:
            path = path.resolve(strict=True)
        except (OSError, RuntimeError):
            self.notify(f"Path does not exist: {event.value}", severity="error")
            return
        if path.is_file():
            self.dismiss(str(path))
        elif path.is_dir():
            tree = self.query_one(AttachmentDirectoryTree)
            tree.path = path
            event.input.value = str(path)
            tree.focus()
        else:
            self.notify(f"Not a regular file or directory: {path}", severity="error")

    def on_tree_node_highlighted(self, event):
        if event.control.id != "attachment-file-tree" or event.node.data is None:
            return
        self._preview_path(event.node.data.path)

    def _preview_path(self, path):
        self._preview_token += 1
        token = self._preview_token
        path = Path(path)
        text = self.query_one("#attachment-file-text", Markdown)
        text.display = False
        self.query_one("#attachment-file-media", Vertical).remove_children()
        try:
            details = path.stat()
            kind = "directory" if path.is_dir() else preview_kind(path.name)
            metadata = f"{path}\nType: {kind}\nSize: {details.st_size:,} bytes"
        except OSError as exc:
            metadata = f"{path}\nUnavailable: {exc}"
            kind = "metadata"
        self.query_one("#attachment-file-meta", Static).update(metadata)
        if kind == "text":
            self._load_local_text(path, token)
        elif kind == "image":
            self._load_local_image(path, token)

    @work(thread=True, exclusive=True, group="local-file-preview")
    def _load_local_text(self, path, token):
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.app.call_from_thread(self._preview_local_failed, token, str(exc))
            return
        self.app.call_from_thread(self._show_local_text, token, content)

    async def _show_local_text(self, token, content):
        if token != self._preview_token:
            return
        widget = self.query_one("#attachment-file-text", Markdown)
        widget.display = True
        await widget.update(content)

    @work(thread=True, exclusive=True, group="local-file-preview")
    def _load_local_image(self, path, token):
        widget_cls = getattr(self.app, "image_widget", None)
        if widget_cls is None:
            return
        try:
            from .browse import decode_image_bytes
            image = decode_image_bytes(path.read_bytes())
        except Exception as exc:
            self.app.call_from_thread(self._preview_local_failed, token, str(exc))
            return
        self.app.call_from_thread(self._show_local_image, token, widget_cls, image)

    async def _show_local_image(self, token, widget_cls, image):
        if token != self._preview_token:
            return
        await self.query_one("#attachment-file-media", Vertical).mount(
            widget_cls(image, id="attachment-file-image"))

    def _preview_local_failed(self, token, message):
        if token == self._preview_token:
            self.notify(f"Preview unavailable: {message}", severity="warning")

    def on_directory_tree_directory_selected(self, event):
        self.query_one("#attachment-root", Input).value = str(event.path)

    def on_directory_tree_file_selected(self, event):
        self.dismiss(str(event.path))


class AttachmentScreen(ModalScreen):
    """List, preview, upload, and copy references for an entry's attachments."""

    DEFAULT_CSS = """
    AttachmentScreen { align: center middle; }
    #attachment-dialog {
        width: 90%;
        height: 85%;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    #attachment-body { height: 1fr; }
    #attachment-table { width: 45%; border: round $primary; }
    #attachment-preview { width: 1fr; border: round $primary-darken-1; padding: 0 1; }
    #attachment-image { width: auto; height: auto; max-width: 100%; max-height: 30; }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("u", "upload", "Upload"),
        Binding("y", "copy_reference", "Copy ref"),
        Binding("x", "delete", "Delete"),
    ]

    def __init__(self, session, doc, entry, *, on_changed=None):
        super().__init__()
        self.session = session
        self.data = session.data
        self.doc = doc
        self.entry = entry
        self.on_changed = on_changed
        self.attachments = []
        self._preview_token = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="attachment-dialog"):
            yield Static(
                f'Attachments for entry #{self.entry.log_id} in "{self.doc.name}"',
                id="attachment-title",
            )
            with Horizontal(id="attachment-body"):
                yield DataTable(id="attachment-table", cursor_type="row", zebra_stripes=True)
                with VerticalScroll(id="attachment-preview"):
                    yield Static("Select an attachment.", id="attachment-meta")
                    yield Markdown(id="attachment-text")
                    yield Vertical(id="attachment-media")
            yield Footer()

    def on_mount(self):
        table = self.query_one("#attachment-table", DataTable)
        table.add_columns("ID", "Filename")
        table.set_loading(True)
        self.query_one("#attachment-text", Markdown).display = False
        self._load()

    @work(thread=True, exclusive=True, group="attachment-list")
    def _load(self, focus_id=None, focus_row=None):
        try:
            attachments = self.data.attachments(self.doc.id, self.entry.log_id)
        except Exception as exc:
            self.app.call_from_thread(
                self._load_failed, format_error_message(exc, self.session.factory))
            return
        self.app.call_from_thread(self._populate, attachments, focus_id, focus_row)

    def _populate(self, attachments, focus_id=None, focus_row=None):
        self.attachments = list(attachments)
        table = self.query_one("#attachment-table", DataTable)
        table.clear()
        table.set_loading(False)
        for attachment in self.attachments:
            table.add_row(
                str(getattr(attachment, "id", "")),
                getattr(attachment, "original_filename", None) or "(unnamed)",
            )
        if not self.attachments:
            self.query_one("#attachment-meta", Static).update("No attachments.")
            return
        row = min(focus_row or 0, len(self.attachments) - 1)
        if focus_id is not None:
            row = next((i for i, att in enumerate(self.attachments) if att.id == focus_id), 0)
        table.move_cursor(row=row)
        table.focus()
        self._preview(self.attachments[row])

    def _load_failed(self, message):
        self.query_one("#attachment-table", DataTable).set_loading(False)
        self.query_one("#attachment-meta", Static).update(f"Could not load attachments: {message}")

    def on_data_table_row_highlighted(self, event):
        if event.data_table.id == "attachment-table" and event.cursor_row < len(self.attachments):
            self._preview(self.attachments[event.cursor_row])

    def _current(self):
        row = self.query_one("#attachment-table", DataTable).cursor_row
        if row is None or row >= len(self.attachments):
            return None
        return self.attachments[row]

    def _preview(self, attachment):
        self._preview_token += 1
        token = self._preview_token
        name = getattr(attachment, "original_filename", None) or "(unnamed)"
        stored = getattr(attachment, "stored_filename", None) or ""
        path = getattr(attachment, "download_path", None) or ""
        metadata = f"ID: {getattr(attachment, 'id', '')}\nFilename: {name}\nStored: {stored}\nDownload: {path}"
        self.query_one("#attachment-meta", Static).update(metadata)
        self.query_one("#attachment-text", Markdown).display = False
        self.query_one("#attachment-media", Vertical).remove_children()
        kind = preview_kind(name)
        if kind == "image":
            self._load_image(attachment, token)
        elif kind == "text":
            self._load_text(attachment, token)

    @work(thread=True, exclusive=True, group="attachment-preview")
    def _load_text(self, attachment, token):
        try:
            raw = self.data.attachment_bytes(attachment.stored_filename, scaling=None)
            content = raw.decode("utf-8")
        except Exception as exc:
            self.app.call_from_thread(self._preview_failed, token, str(exc))
            return
        self.app.call_from_thread(self._show_text, token, content)

    async def _show_text(self, token, content):
        if token != self._preview_token:
            return
        widget = self.query_one("#attachment-text", Markdown)
        widget.display = True
        await widget.update(content)

    @work(thread=True, exclusive=True, group="attachment-preview")
    def _load_image(self, attachment, token):
        widget_cls = getattr(self.app, "image_widget", None)
        if widget_cls is None:
            self.app.call_from_thread(self._preview_failed, token, "Image preview is unavailable.")
            return
        try:
            from .browse import decode_image_bytes

            raw = self.data.attachment_bytes(attachment.stored_filename)
            image = decode_image_bytes(raw)
        except Exception as exc:
            self.app.call_from_thread(self._preview_failed, token, str(exc))
            return
        self.app.call_from_thread(self._show_image, token, widget_cls, image)

    async def _show_image(self, token, widget_cls, image):
        if token != self._preview_token:
            return
        await self.query_one("#attachment-media", Vertical).mount(
            widget_cls(image, id="attachment-image"))

    def _preview_failed(self, token, message):
        if token == self._preview_token:
            self.notify(f"Preview unavailable: {message}", severity="warning")

    def action_copy_reference(self):
        attachment = self._current()
        if attachment is None:
            self.notify("Select an attachment first.", severity="warning")
            return
        reference = getattr(attachment, "markdown_reference", None) or ""
        self.app.copy_to_clipboard(reference)
        self.notify("Attachment Markdown reference copied.")

    def action_delete(self):
        attachment = self._current()
        if attachment is None:
            self.notify("Select an attachment first.", severity="warning")
            return
        self._delete(attachment)

    @work
    async def _delete(self, attachment):
        confirmed = await self.app.push_screen_wait(ConfirmScreen(
            f'Delete attachment "{attachment.original_filename}" (id={attachment.id})?',
            confirm_label="Delete", cancel_label="Cancel", confirm_variant="error"))
        if not confirmed:
            return
        api = await self.app.ensure_auth()
        if api is None:
            return
        try:
            await asyncio.to_thread(
                core.delete_attachment, api, self.doc.id, self.entry.log_id, attachment.id)
        except Exception as exc:
            self.notify(
                f"Delete failed: {format_error_message(exc, self.session.factory)}",
                severity="error")
            return
        row = self.query_one("#attachment-table", DataTable).cursor_row or 0
        self.data.invalidate_attachments(self.doc.id, self.entry.log_id)
        if self.on_changed is not None:
            self.on_changed()
        self._load(focus_row=row)
        self.notify(f'Attachment "{attachment.original_filename}" deleted.')

    def action_upload(self):
        self._upload()

    @work
    async def _upload(self):
        path = await self.app.push_screen_wait(AttachmentFileScreen())
        if not path:
            return
        try:
            path = core.validate_attachment_path(path)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        api = await self.app.ensure_auth()
        if api is None:
            return
        await self.app.push_screen(LoadingScreen("Uploading attachment…"))
        try:
            info = await asyncio.to_thread(
                core.upload_attachment, api, self.doc.id, self.entry.log_id, path)
        except Exception as exc:
            self.notify(
                f"Upload failed: {format_error_message(exc, self.session.factory)}",
                severity="error",
            )
            return
        finally:
            self.app.pop_screen()
        self.data.invalidate_attachments(self.doc.id, self.entry.log_id)
        if self.on_changed is not None:
            self.on_changed()
        self._load(focus_id=info["id"])
        self.notify(f'Attachment "{info["original_filename"]}" uploaded.')

    def action_close(self):
        self.dismiss(None)
