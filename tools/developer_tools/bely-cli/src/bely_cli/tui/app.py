"""Textual application for `bely-cli tui` / `bely-cli tui lookup`.

`BelyTuiApp` owns the session (auth + cached data) and the shared CSS. It
pushes `BrowseScreen` directly on mount for both modes -- there is no
separate landing/menu screen. The only difference between modes is
`select_mode`: "lookup" exits with `(doc, entry)` on the original
select-and-exit contract `tui lookup` scripts depend on; "app" just browses
in place.

Everything else the old Home menu offered (configuration, "my documents",
logging in ahead of time, discarding the cache) lives in the command palette
(`ctrl+p`), wired up via `get_system_commands()`.

`ensure_auth()` is the shared auth gate every mutating screen goes through:
it tries the cached CLI token first (so a user who already ran an
authenticated CLI command never sees a login prompt), then falls back to
pushing LoginScreen and calling session.login(). Screens call it from an
async `@work` method (not `@work(thread=True)`) because it needs to await a
modal; the network calls inside it are pushed to a thread via
`asyncio.to_thread` so the event loop is never blocked.
"""

import asyncio

from textual.app import App, SystemCommand

from .screens.browse import BrowseScreen


class BelyTuiApp(App):
    """Top-level app: pushes Browse and returns its exit result."""

    TITLE = "BELY"

    CSS = """
    #body {
        height: 1fr;
    }

    #nav-table {
        border: round $primary;
    }

    #preview {
        width: 1fr;
        border: round $primary-darken-1;
        padding: 0 1;
    }

    #meta {
        height: auto;
        border-bottom: solid $primary-darken-1;
        margin-bottom: 1;
    }

    #status-bar {
        height: 1;
        padding: 0 1;
    }

    #status-left {
        width: 1fr;
    }

    #filter {
        width: 1fr;
        margin: 0 1;
    }

    #status-right {
        width: auto;
    }
    """

    def __init__(self, session, limit=100, mode="app"):
        super().__init__()
        self.session = session
        self.limit = limit
        self.mode = mode

    def on_mount(self):
        self.theme = "textual-dark"
        self.push_screen(BrowseScreen(self.session, self.limit, select_mode=(self.mode == "lookup")))

    def get_system_commands(self, screen):
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            "Configuration", "View and edit bely-cli settings", self._cmd_config)
        if isinstance(screen, BrowseScreen):
            yield SystemCommand(
                "My documents", "Browse your recently modified documents", self._cmd_recent)
            yield SystemCommand(
                "Refresh cache", "Discard all cached logbook data", self._cmd_refresh)
        yield SystemCommand(
            "Log in", "Authenticate now instead of at the first mutation", self._cmd_login)

    def _cmd_config(self):
        from .screens.configscreen import ConfigScreen

        self.push_screen(ConfigScreen())

    def _cmd_recent(self):
        self.push_screen(BrowseScreen(self.session, self.limit, select_mode=False, source="recent"))

    def _cmd_refresh(self):
        self.session.data.clear()
        screen = self.screen
        if isinstance(screen, BrowseScreen):
            screen.show_level(screen.level, preserve_filter=True)
        self.notify("Cache cleared.")

    def _cmd_login(self):
        self.run_worker(self._do_login(), exclusive=True, group="login")

    async def _do_login(self):
        api = await self.ensure_auth()
        screen = self.screen
        if isinstance(screen, BrowseScreen):
            screen._update_auth_status()
        if api is not None:
            self.notify("Logged in.")

    async def ensure_auth(self):
        """Return an authenticated logbook_api, or None if the user cancelled login.

        Safe to call repeatedly -- once authenticated for this session, later
        calls just return the cached api without touching the network or UI.
        """
        if self.session.is_authenticated():
            return self.session.authenticated_api()

        ok = await asyncio.to_thread(self.session.try_token)
        if ok:
            return self.session.authenticated_api()

        from .screens.login import LoginScreen

        prefill = self.session.username() or ""
        while True:
            credentials = await self.push_screen_wait(LoginScreen(prefill))
            if credentials is None:
                return None
            username, password = credentials
            try:
                await asyncio.to_thread(self.session.login, username, password)
            except ValueError as e:
                self.notify(str(e), severity="error")
                prefill = username
                continue
            except RuntimeError as e:
                self.notify(f"Login failed: {e}", severity="error")
                return None
            return self.session.authenticated_api()
