import getpass
import os
import sys
from contextlib import contextmanager

from config import CONFIG_DIR, expand_path, get_setting

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
        print("Error: no host configured. Set BELY_HOST or add 'host' to settings.yaml.",
              file=sys.stderr)
        sys.exit(1)
    return host


def get_username():
    """Return the BELY username from env var, settings, or interactive prompt."""
    username = os.environ.get("BELY_USER") or get_setting("user")
    if not username:
        username = input("Username: ").strip()
    return username


def get_password(username):
    """Return the BELY password from env var or interactive prompt."""
    password = os.environ.get("BELY_PASSWORD")
    if not password:
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


def _login_and_cache(factory):
    """Prompt for credentials, authenticate the factory, and persist the new token."""
    import belyApi
    username = get_username()
    password = get_password(username)
    try:
        factory.authenticate_user(username, password)
    except belyApi.exceptions.UnauthorizedException:
        print(f"Authentication failed: invalid credentials for user '{username}'",
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)
    save_token(factory.get_authenticate_token())


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
    import belyApi
    from BelyApiFactory import BelyApiFactory

    factory = BelyApiFactory(bely_url=get_host())

    token = load_token()
    if token:
        factory.api_client.set_default_header(BelyApiFactory.HEADER_TOKEN_KEY, token)
        try:
            factory.test_authenticated()
        except belyApi.exceptions.UnauthorizedException:
            delete_token()
            factory.api_client.default_headers.pop(BelyApiFactory.HEADER_TOKEN_KEY, None)
            _login_and_cache(factory)
    else:
        _login_and_cache(factory)

    yield factory
