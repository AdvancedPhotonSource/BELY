import getpass
import os
import sys
from contextlib import contextmanager

from .common import is_no_prompt
from .config import CONFIG_DIR, expand_path, get_setting

# belyApi and BelyApiFactory are imported lazily inside the functions that need
# them: the generated client is ~1.8s to import, and paths like --help that
# never make a network call should not pay that cost.



def get_token_file():
    """Return the token file path: 'token_path' setting, else <config dir>/token."""
    configured = get_setting("token_path")
    if configured:
        return expand_path(configured)
    return os.path.join(CONFIG_DIR, "token")


def get_host():
    """Return the BELY server URL from env var or settings."""
    host = os.environ.get("BELY_HOST") or get_setting("host")
    if not host:
        raise ValueError("no host configured. Set BELY_HOST or add 'host' to settings.yaml.")
    return host


def get_configured_username():
    """Return the BELY username from env var or settings, without prompting."""
    return os.environ.get("BELY_USER") or get_setting("user")


def get_username():
    """Return the BELY username from env var, settings, or interactive prompt."""
    username = get_configured_username()
    if not username:
        if is_no_prompt():
            raise ValueError("username required: set BELY_USER or 'user' in settings")
        username = input("Username: ").strip()
    return username


def get_password(username):
    """Return the BELY password from env var or interactive prompt."""
    password = os.environ.get("BELY_PASSWORD")
    if not password:
        if is_no_prompt():
            raise ValueError("password required: set BELY_PASSWORD")
        print(f"Logging in as '{username}'")
        try:
            password = getpass.getpass("Password: ")
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)
    return password


def load_token():
    """Return the cached auth token from disk, or None if not present."""
    try:
        with open(get_token_file(), "r") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None


def save_token(token):
    """Persist the auth token to disk with restrictive permissions."""
    token_file = get_token_file()
    parent = os.path.dirname(token_file)
    if parent:
        os.makedirs(parent, mode=0o700, exist_ok=True)
    with open(token_file, "w") as f:
        f.write(token)
    os.chmod(token_file, 0o600)


def delete_token():
    """Remove the cached token file."""
    try:
        os.remove(get_token_file())
    except FileNotFoundError:
        pass


def get_factory():
    """Create and return an unauthenticated BelyApiFactory."""
    from BelyApiFactory import BelyApiFactory
    return BelyApiFactory(bely_url=get_host())


def authenticated_factory_from_token():
    """Return a factory authenticated with the cached token, or None.

    A cached token that the server rejects is deleted before returning None,
    so the caller can fall back to an interactive/explicit login. Does not
    prompt for anything.
    """
    import belyApi
    from BelyApiFactory import BelyApiFactory

    token = load_token()
    if not token:
        return None

    factory = BelyApiFactory(bely_url=get_host())
    factory.api_client.set_default_header(BelyApiFactory.HEADER_TOKEN_KEY, token)
    try:
        factory.test_authenticated()
    except belyApi.exceptions.UnauthorizedException:
        delete_token()
        return None
    return factory


def login(username, password):
    """Authenticate with credentials, cache the resulting token, and return the factory.

    Raises ValueError on bad credentials, RuntimeError on any other failure.
    """
    import belyApi
    from BelyApiFactory import BelyApiFactory

    factory = BelyApiFactory(bely_url=get_host())
    try:
        factory.authenticate_user(username, password)
    except belyApi.exceptions.UnauthorizedException:
        raise ValueError(f"Authentication failed: invalid credentials for user '{username}'")
    except Exception as e:
        raise RuntimeError(f"Authentication failed: {e}") from e
    save_token(factory.get_authenticate_token())
    return factory


@contextmanager
def get_authenticated_factory():
    """Create and yield an authenticated BelyApiFactory.

    Uses a cached token from disk if it is still valid; otherwise prompts
    for credentials and saves the new token. The token persists across
    runs, so we deliberately do not log out on exit.

    Credentials, when needed, come from:
      1. BELY_USER + BELY_PASSWORD env vars
      2. Interactive prompt
    """
    factory = authenticated_factory_from_token()
    if factory is None:
        username = get_username()
        factory = login(username, get_password(username))

    yield factory
