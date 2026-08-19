"""TuiSession: the TUI's handle on auth + cached API access.

No Textual import here (matches data.py) -- this is plumbing the screens use,
kept testable without a terminal. Constructed once by cmd_tui and shared by
every screen through `self.app.session`.

Browsing (types/docs/entries/recent-docs) only ever needs the unauthenticated
`factory` that also backs `LogbookData`. Mutations (new doc, add/update
entry, attachments, config) need an authenticated `logbook_api`, obtained
lazily and cached here for the rest of the session -- this is what lets a
user who already has a cached CLI token (`bely-cli entry add ...` run
earlier, for instance) skip the login screen entirely.
"""

from .. import auth
from .data import LogbookData


class TuiSession:
    def __init__(self, factory):
        self.factory = factory
        self.data = LogbookData(factory.get_logbook_api())
        self._auth_factory = None

    def username(self):
        """Configured username, or None. Does not prompt."""
        return auth.get_configured_username()

    def is_authenticated(self):
        return self._auth_factory is not None

    def try_token(self):
        """Try the cached CLI token. Returns True if now authenticated.

        Safe to call repeatedly/off the UI thread; does not prompt.
        """
        if self._auth_factory is not None:
            return True
        factory = auth.authenticated_factory_from_token()
        if factory is None:
            return False
        self._auth_factory = factory
        return True

    def login(self, username, password):
        """Authenticate with explicit credentials.

        Raises ValueError on bad credentials, RuntimeError otherwise -- same
        as auth.login, which this delegates to.
        """
        self._auth_factory = auth.login(username, password)

    def authenticated_factory(self):
        """The authenticated BelyApiFactory. Raises RuntimeError if not authenticated yet."""
        if self._auth_factory is None:
            raise RuntimeError("not authenticated yet")
        return self._auth_factory

    def authenticated_api(self):
        """The authenticated logbook_api. Raises RuntimeError if not authenticated yet."""
        return self.authenticated_factory().get_logbook_api()
