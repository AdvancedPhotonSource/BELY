"""DialogScreen: shared modal base -- a bordered panel, Esc to cancel, arrows between fields/buttons."""

from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button

SAVE_HINT = "^S"
CANCEL_HINT = "Esc"


def hinted_label(label, hint=None):
    """Button label with its shortcut dimmed on a second line, blank if none, so row buttons stay level."""
    return f"{label}\n[dim]{hint or ' '}[/dim]"


class DialogButtons(Horizontal):
    DEFAULT_CLASSES = "dialog-buttons"


class DialogScreen(ModalScreen):
    DEFAULT_CSS = """
    DialogScreen {
        align: center middle;
    }

    .dialog {
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    .dialog-buttons {
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    .dialog-buttons Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("up", "focus_up", show=False),
        Binding("down", "focus_down", show=False),
        Binding("left", "focus_left", show=False),
        Binding("right", "focus_right", show=False),
    ]

    # Subclasses override: list of button-id rows, top row first.
    BUTTON_ROWS = []

    def action_cancel(self):
        self.dismiss(None)

    # -- arrow-key nav across BUTTON_ROWS --

    def _focused_button_row(self):
        focused = self.focused
        if not isinstance(focused, Button):
            return None
        for row in self.BUTTON_ROWS:
            if focused.id in row:
                return row
        return None

    def action_focus_left(self):
        self._cycle_button(-1)

    def action_focus_right(self):
        self._cycle_button(1)

    def _cycle_button(self, delta):
        row = self._focused_button_row()
        if row is None:
            return
        pos = row.index(self.focused.id)
        self.query_one(f"#{row[(pos + delta) % len(row)]}", Button).focus()

    def action_focus_down(self):
        row = self._focused_button_row()
        if row is None:
            self.focus_next()
            return
        idx = self.BUTTON_ROWS.index(row)
        if idx + 1 < len(self.BUTTON_ROWS):
            self.query_one(f"#{self.BUTTON_ROWS[idx + 1][0]}", Button).focus()

    def action_focus_up(self):
        row = self._focused_button_row()
        if row is None:
            self.focus_previous()
            return
        idx = self.BUTTON_ROWS.index(row)
        if idx > 0:
            self.query_one(f"#{self.BUTTON_ROWS[idx - 1][0]}", Button).focus()
            return
        chain = self.focus_chain
        first_button = self.query_one(f"#{self.BUTTON_ROWS[0][0]}", Button)
        pos = chain.index(first_button)
        if pos > 0:
            chain[pos - 1].focus()
