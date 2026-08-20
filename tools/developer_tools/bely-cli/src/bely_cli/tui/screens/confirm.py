"""ConfirmScreen: a reusable yes/no modal with real buttons.

Dismisses with True (confirm), or False on cancel/escape. Used wherever the
TUI needs a "are you sure?" gate -- ComposeScreen's discard-changes check,
BrowseScreen's save-after-external-edit prompt -- instead of repurposing
PickerScreen (a filterable list) for a plain confirmation.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static

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
