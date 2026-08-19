"""ConfirmScreen: a reusable yes/no modal with real buttons.

Dismisses with True (confirm), or False on cancel/escape. Used wherever the
TUI needs a "are you sure?" gate -- ComposeScreen's discard-changes check,
BrowseScreen's save-after-external-edit prompt -- instead of repurposing
PickerScreen (a filterable list) for a plain confirmation.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen):
    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }

    #confirm-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #confirm-buttons {
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, message, *, confirm_label="Yes", cancel_label="No",
                 confirm_variant="primary"):
        super().__init__()
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_variant = confirm_variant

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static(self.message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button(self.cancel_label, id="confirm-cancel")
                yield Button(self.confirm_label, variant=self.confirm_variant, id="confirm-confirm")

    def on_mount(self):
        self.query_one("#confirm-confirm", Button).focus()

    def on_button_pressed(self, event):
        if event.button.id == "confirm-confirm":
            self.dismiss(True)
        elif event.button.id == "confirm-cancel":
            self.dismiss(False)

    def action_cancel(self):
        self.dismiss(False)
