"""LoginScreen: credentials modal used by BelyTuiApp.ensure_auth().

Deliberately dumb: it only collects a (username, password) pair and dismisses
with it (or None on cancel). The caller does the actual network call, so this
screen needs no auth import and is trivial to test headless.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class LoginScreen(ModalScreen):
    DEFAULT_CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, prefill=""):
        super().__init__()
        self._prefill = prefill

    def compose(self) -> ComposeResult:
        with Vertical(id="login-dialog"):
            yield Static("Log in to BELY", id="login-title")
            yield Input(value=self._prefill, placeholder="username", id="login-username")
            yield Input(password=True, placeholder="password", id="login-password")
            yield Static("[enter] submit   [escape] cancel", id="login-hint")

    def on_mount(self):
        field = self.query_one("#login-username", Input)
        field.focus()
        field.cursor_position = len(field.value)

    def on_input_submitted(self, event):
        if event.input.id == "login-username":
            self.query_one("#login-password", Input).focus()
        elif event.input.id == "login-password":
            self._submit()

    def _submit(self):
        username = self.query_one("#login-username", Input).value.strip()
        password = self.query_one("#login-password", Input).value
        if not username:
            self.notify("Username is required.", severity="warning")
            return
        self.dismiss((username, password))

    def action_cancel(self):
        self.dismiss(None)
