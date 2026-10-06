"""Attachment browser for a selected log entry."""

import asyncio
import os

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Markdown, Static

from ... import core
from ...common import format_error_message
from .confirm import ConfirmScreen
from .dialog import DialogScreen


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


class AttachmentPathScreen(DialogScreen):
    """Prompt for a local attachment path."""

    DEFAULT_CSS = """
    #attachment-path-dialog { width: 70; }
    #attachment-path { margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="attachment-path-dialog", classes="dialog"):
            yield Static("Local file to upload")
            yield Input(placeholder="file path", id="attachment-path")

    def on_mount(self):
        self.query_one(Input).focus()

    def on_input_submitted(self, event):
        path = event.value.strip()
        if path:
            self.dismiss(path)


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

    def __init__(self, session, doc, entry, *, on_uploaded=None):
        super().__init__()
        self.session = session
        self.data = session.data
        self.doc = doc
        self.entry = entry
        self.on_uploaded = on_uploaded
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
        self._load(focus_row=row)
        self.notify(f'Attachment "{attachment.original_filename}" deleted.')

    def action_upload(self):
        self._upload()

    @work
    async def _upload(self):
        path = await self.app.push_screen_wait(AttachmentPathScreen())
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
        try:
            info = await asyncio.to_thread(
                core.upload_attachment, api, self.doc.id, self.entry.log_id, path)
        except Exception as exc:
            self.notify(
                f"Upload failed: {format_error_message(exc, self.session.factory)}",
                severity="error",
            )
            return
        self.data.invalidate_attachments(self.doc.id, self.entry.log_id)
        if self.on_uploaded is not None:
            self.on_uploaded()
        self._load(focus_id=info["id"])
        self.notify(f'Attachment "{info["original_filename"]}" uploaded.')

    def action_close(self):
        self.dismiss(None)
