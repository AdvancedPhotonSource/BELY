import getpass
import os
import sys
from contextlib import contextmanager

import belyApi

from BelyApiFactory import BelyApiFactory
from settings import get_setting


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



def get_factory():
    """Create and return an unauthenticated BelyApiFactory."""
    return BelyApiFactory(bely_url=get_host())


@contextmanager
def get_authenticated_factory():
    """Create and yield an authenticated BelyApiFactory, logging out on exit.

    Usage::

        with auth.get_authenticated_factory() as factory:
            logbook_api = factory.get_logbook_api()
            ...

    Credentials come from:
      1. BELY_USER + BELY_PASSWORD env vars
      2. Interactive prompt
    """
    factory = BelyApiFactory(bely_url=get_host())

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

    try:
        yield factory
    finally:
        factory.logout_user()
