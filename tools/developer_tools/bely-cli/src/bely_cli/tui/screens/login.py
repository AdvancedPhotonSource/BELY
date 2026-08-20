"""LoginScreen: credentials modal used by BelyTuiApp.ensure_auth().

Deliberately dumb: it only collects a (username, password) pair and dismisses
with it (or None on cancel). The caller does the actual network call, so this
screen needs no auth import and is trivial to test headless.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Input, Static

from .dialog import CANCEL_HINT, SAVE_HINT, DialogButtons, DialogScreen, hinted_label


class LoginScreen(DialogScreen):
    DEFAULT_CSS = """
    #login-dialog {
        width: 60;
    }
    """

    BINDINGS = [Binding("ctrl+s", "submit", "Log in", show=False)]

    BUTTON_ROWS = [["login-submit", "login-cancel"]]

    def __init__(self, prefill=""):
        super().__init__()
        self._prefill = prefill

    def compose(self) -> ComposeResult:
        with Vertical(id="login-dialog", classes="dialog"):
            yield Static("Log in to BELY", id="login-title")
            yield Input(value=self._prefill, placeholder="username", id="login-username")
            yield Input(password=True, placeholder="password", id="login-password")
            with DialogButtons():
                yield Button(hinted_label("Log in", SAVE_HINT), variant="primary", id="login-submit")
                yield Button(hinted_label("Cancel", CANCEL_HINT), id="login-cancel")

    def on_mount(self):
        field = self.query_one("#login-username", Input)
        field.focus()
        field.cursor_position = len(field.value)

    def on_input_submitted(self, event):
        if event.input.id == "login-username":
            self.query_one("#login-password", Input).focus()
        elif event.input.id == "login-password":
            self._submit()

    def on_button_pressed(self, event):
        if event.button.id == "login-submit":
            self._submit()
        elif event.button.id == "login-cancel":
            self.dismiss(None)

    def action_submit(self):
        self._submit()

    def _submit(self):
        username = self.query_one("#login-username", Input).value.strip()
        password = self.query_one("#login-password", Input).value
        if not username:
            self.notify("Username is required.", severity="warning")
            return
        self.dismiss((username, password))
