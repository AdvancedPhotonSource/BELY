"""ConfirmScreen: a reusable yes/no modal with real buttons.

Dismisses with True (confirm), or False on cancel/escape. Used wherever the
TUI needs a "are you sure?" gate -- ComposeScreen's discard-changes check,
BrowseScreen's save-after-external-edit prompt -- instead of repurposing
PickerScreen (a filterable list) for a plain confirmation.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, Static

from .dialog import CANCEL_HINT, DialogButtons, DialogScreen, hinted_label


class ConfirmScreen(DialogScreen):
    DEFAULT_CSS = """
    #confirm-dialog {
        width: 60;
    }
    """

    BUTTON_ROWS = [["confirm-confirm", "confirm-cancel"]]

    def __init__(self, message, *, confirm_label="Yes", cancel_label="No",
                 confirm_variant="primary"):
        super().__init__()
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_variant = confirm_variant

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog", classes="dialog"):
            yield Static(self.message, id="confirm-message")
            with DialogButtons():
                yield Button(hinted_label(self.confirm_label), variant=self.confirm_variant, id="confirm-confirm")
                yield Button(hinted_label(self.cancel_label, CANCEL_HINT), id="confirm-cancel")

    def on_mount(self):
        # Destructive confirmations default focus to "cancel" rather than the risky action.
        default_id = "confirm-cancel" if self.confirm_variant == "error" else "confirm-confirm"
        self.query_one(f"#{default_id}", Button).focus()

    def on_button_pressed(self, event):
        if event.button.id == "confirm-confirm":
            self.dismiss(True)
        elif event.button.id == "confirm-cancel":
            self.dismiss(False)

    def action_cancel(self):
        self.dismiss(False)


class TypeToConfirmScreen(DialogScreen):
    """Require an exact phrase before enabling a destructive action."""

    DEFAULT_CSS = """
    #type-confirm-dialog { width: 64; }
    #type-confirm-input { margin-top: 1; }
    """

    BUTTON_ROWS = [["type-confirm-confirm", "type-confirm-cancel"]]

    def __init__(self, message, *, phrase="delete", confirm_label="Delete",
                 cancel_label="Cancel"):
        super().__init__()
        self.message = message
        self.phrase = phrase
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(id="type-confirm-dialog", classes="dialog"):
            yield Static(self.message, id="type-confirm-message")
            yield Input(
                placeholder=f'Type "{self.phrase}" to continue',
                id="type-confirm-input",
            )
            with DialogButtons():
                yield Button(
                    hinted_label(self.confirm_label), variant="error",
                    id="type-confirm-confirm", disabled=True,
                )
                yield Button(
                    hinted_label(self.cancel_label, CANCEL_HINT),
                    id="type-confirm-cancel",
                )

    def on_mount(self):
        self.query_one("#type-confirm-input", Input).focus()

    def on_input_changed(self, event):
        if event.input.id == "type-confirm-input":
            self.query_one("#type-confirm-confirm", Button).disabled = (
                event.value != self.phrase)

    def on_input_submitted(self, event):
        if event.input.id == "type-confirm-input" and event.value == self.phrase:
            self.dismiss(True)

    def on_button_pressed(self, event):
        if event.button.id == "type-confirm-confirm":
            self.dismiss(True)
        elif event.button.id == "type-confirm-cancel":
            self.dismiss(False)

    def action_cancel(self):
        self.dismiss(False)
