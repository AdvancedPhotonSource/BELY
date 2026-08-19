"""ComposeScreen: TextArea editor for adding or updating a log entry.

Auth is resolved by the caller (via `open_composer`, below) before this
screen is ever pushed -- fetching a fresh entry template already needs an
authenticated api (see core.new_entry_template), so there is no
"unauthenticated" state for this screen to handle. It only knows how to
render/edit/save, given an already-authenticated `api`.

Dismisses with the saved entry, or None if the user cancelled / nothing
changed.
"""

import asyncio

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, TextArea

from ... import core
from ...common import editor_changed


class ComposeScreen(ModalScreen):
    """Buttons-only entry composer; BINDINGS below are arrow-key focus navigation, not action shortcuts."""

    DEFAULT_CSS = """
    ComposeScreen {
        align: center middle;
    }

    #compose-dialog {
        width: 90%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #compose-area {
        height: 1fr;
    }

    #compose-buttons {
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    #compose-buttons Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("up", "focus_up", show=False),
        Binding("down", "focus_down", show=False),
        Binding("left", "focus_left", show=False),
        Binding("right", "focus_right", show=False),
    ]

    # Save first: right after the attachment field in tab order, since it's used most.
    BUTTON_IDS = ["compose-save", "compose-editor", "compose-cancel"]

    def __init__(self, doc, entry, api, *, is_new):
        super().__init__()
        self.doc = doc
        self.entry = entry
        self.api = api
        self.is_new = is_new
        self._initial_text = entry.log_entry or ""

    def compose(self) -> ComposeResult:
        title = (f'New entry in "{self.doc.name}"' if self.is_new
                 else f'Update entry #{self.entry.log_id} in "{self.doc.name}"')
        with Vertical(id="compose-dialog"):
            yield Static(title, id="compose-title")
            yield TextArea(self._initial_text, language="markdown", id="compose-area")
            with Horizontal(id="compose-attach-row"):
                yield Static("Attachment:", id="compose-attach-label")
                yield Input(placeholder="optional file path", id="compose-attach")
            with Horizontal(id="compose-buttons"):
                yield Button("Save", variant="primary", id="compose-save")
                yield Button("Edit in $EDITOR", id="compose-editor")
                yield Button("Cancel", id="compose-cancel")

    def on_mount(self):
        self.query_one("#compose-area", TextArea).focus()

    def on_button_pressed(self, event):
        if event.button.id == "compose-save":
            self._save()
        elif event.button.id == "compose-editor":
            self._open_editor()
        elif event.button.id == "compose-cancel":
            self._cancel()

    # -- arrow-key nav: TextArea/Input consume arrows themselves, so this only fires past both --

    def action_focus_down(self):
        if self.focused is self.query_one("#compose-attach", Input):
            self.query_one(f"#{self.BUTTON_IDS[0]}", Button).focus()

    def action_focus_up(self):
        if isinstance(self.focused, Button):
            self.query_one("#compose-attach", Input).focus()

    def action_focus_left(self):
        self._cycle_button(-1)

    def action_focus_right(self):
        self._cycle_button(1)

    def _cycle_button(self, delta):
        focused = self.focused
        if not isinstance(focused, Button):
            return
        idx = self.BUTTON_IDS.index(focused.id)
        target_id = self.BUTTON_IDS[(idx + delta) % len(self.BUTTON_IDS)]
        self.query_one(f"#{target_id}", Button).focus()

    # -- dirty check shared by cancel and save --

    def _is_dirty(self):
        area = self.query_one("#compose-area", TextArea)
        attach_path = self.query_one("#compose-attach", Input).value.strip()
        return editor_changed(self._initial_text, area.text) or bool(attach_path)

    # -- cancel, with a dirty-buffer confirmation --

    def _cancel(self):
        if self._is_dirty():
            self._confirm_discard()
        else:
            self.dismiss(None)

    @work
    async def _confirm_discard(self):
        from .confirm import ConfirmScreen

        discard = await self.app.push_screen_wait(
            ConfirmScreen(
                "Discard unsaved changes?", confirm_label="Discard", cancel_label="Keep editing",
                confirm_variant="error",
            )
        )
        if discard:
            self.dismiss(None)

    # -- hand off to $EDITOR and back --

    def _open_editor(self):
        from ...common import open_in_editor

        area = self.query_one("#compose-area", TextArea)
        with self.app.suspend():
            edited = open_in_editor(area.text)
        area.text = edited

    # -- save --

    @work
    async def _save(self):
        area = self.query_one("#compose-area", TextArea)
        text = area.text

        if self.is_new and not text.strip():
            self.notify("Empty entry, skipped.", severity="warning")
            self.dismiss(None)
            return

        attach_path = self.query_one("#compose-attach", Input).value.strip()
        if attach_path:
            try:
                attach_path = core.validate_attachment_path(attach_path)
            except ValueError as e:
                self.notify(str(e), severity="error")
                return

        if not self.is_new and not editor_changed(self._initial_text, text) and not attach_path:
            self.notify("No changes made.")
            self.dismiss(None)
            return

        try:
            saved_entry = await asyncio.to_thread(core.save_entry, self.api, self.entry, text)
            if attach_path:
                await asyncio.to_thread(
                    core.upload_attachment, self.api, self.doc.id, saved_entry.log_id, attach_path)
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")
            return

        self.dismiss(saved_entry)


async def open_composer(app, doc, api, *, entry=None):
    """Push ComposeScreen for a new or existing entry.

    When `entry` is None, fetches a fresh template first (needs an
    authenticated api, same as cmd_add_entry) -- shared by BrowseScreen's
    'n'/'u' keys and NewDocScreen's post-create prompt so neither duplicates
    the template-fetch/push/await dance.

    Returns the saved entry, or None if the template fetch failed or the
    user cancelled / made no changes.
    """
    if entry is None:
        try:
            entry = await asyncio.to_thread(core.new_entry_template, api, doc.id)
        except Exception as e:
            app.notify(f"Could not load entry template: {e}", severity="error")
            return None
        is_new = True
    else:
        is_new = False
    return await app.push_screen_wait(ComposeScreen(doc, entry, api, is_new=is_new))
