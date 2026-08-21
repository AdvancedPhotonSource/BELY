import os
import tempfile
import unittest
from unittest.mock import patch

from bely_cli import auth


class _Unauthorized(Exception):
    """Stand-in for belyApi.exceptions.UnauthorizedException."""


class FakeApiClient:
    def __init__(self):
        self.default_headers = {}

    def set_default_header(self, key, value):
        self.default_headers[key] = value


def _fake_factory_class(valid_token=None, login_ok=True, login_token="new-token"):
    """Build a stand-in for BelyApiFactory.BelyApiFactory.

    `valid_token` is the only token `test_authenticated()` accepts;
    `login_ok`/`login_token` control what `authenticate_user()` does.
    """

    class FakeFactory:
        HEADER_TOKEN_KEY = "token"

        def __init__(self, bely_url):
            self.bely_url = bely_url
            self.api_client = FakeApiClient()

        def test_authenticated(self):
            if self.api_client.default_headers.get(self.HEADER_TOKEN_KEY) != valid_token:
                raise _Unauthorized()

        def authenticate_user(self, username, password):
            if not login_ok:
                raise _Unauthorized()
            self.api_client.set_default_header(self.HEADER_TOKEN_KEY, login_token)

        def get_authenticate_token(self):
            return self.api_client.default_headers[self.HEADER_TOKEN_KEY]

    return FakeFactory


class AuthTestCase(unittest.TestCase):
    """Points auth.py's token file at a scratch path and stubs get_host()."""

    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        os.remove(tmp.name)  # start with no cached token
        self.token_file = tmp.name
        self.addCleanup(lambda: os.path.exists(self.token_file) and os.remove(self.token_file))

        p_token = patch.object(auth, "get_token_file", return_value=self.token_file)
        p_token.start()
        self.addCleanup(p_token.stop)

        p_host = patch.object(auth, "get_host", return_value="https://example.test/bely")
        p_host.start()
        self.addCleanup(p_host.stop)

    def _install_factory(self, **kwargs):
        fake_cls = _fake_factory_class(**kwargs)
        self._install_factory_class(fake_cls)
        return fake_cls

    def _install_factory_class(self, fake_cls):
        p1 = patch("BelyApiFactory.BelyApiFactory", fake_cls)
        p1.start()
        self.addCleanup(p1.stop)
        p2 = patch("belyApi.exceptions.UnauthorizedException", _Unauthorized)
        p2.start()
        self.addCleanup(p2.stop)


class AuthenticatedFactoryFromTokenTests(AuthTestCase):
    def test_no_cached_token_returns_none(self):
        self._install_factory(valid_token="good-token")
        self.assertIsNone(auth.authenticated_factory_from_token())

    def test_valid_cached_token_returns_factory(self):
        self._install_factory(valid_token="good-token")
        auth.save_token("good-token")

        factory = auth.authenticated_factory_from_token()

        self.assertIsNotNone(factory)
        self.assertEqual(factory.api_client.default_headers["token"], "good-token")

    def test_rejected_token_is_deleted_and_returns_none(self):
        self._install_factory(valid_token="good-token")
        auth.save_token("stale-token")

        factory = auth.authenticated_factory_from_token()

        self.assertIsNone(factory)
        self.assertIsNone(auth.load_token())


class LoginTests(AuthTestCase):
    def test_success_caches_token_and_returns_factory(self):
        self._install_factory(login_ok=True, login_token="fresh-token")

        factory = auth.login("alice", "correct")

        self.assertEqual(factory.get_authenticate_token(), "fresh-token")
        self.assertEqual(auth.load_token(), "fresh-token")

    def test_bad_credentials_raise_value_error_and_leave_no_token(self):
        self._install_factory(login_ok=False)

        with self.assertRaises(ValueError) as ctx:
            auth.login("alice", "wrong")

        self.assertIn("alice", str(ctx.exception))
        self.assertIsNone(auth.load_token())

    def test_other_failure_raises_runtime_error(self):
        fake_cls = _fake_factory_class()

        class BoomFactory(fake_cls):
            def authenticate_user(self, username, password):
                raise RuntimeError("network down")

        self._install_factory_class(BoomFactory)

        with self.assertRaises(RuntimeError):
            auth.login("alice", "whatever")


class GetAuthenticatedFactoryTests(AuthTestCase):
    def test_prefers_valid_cached_token_without_prompting(self):
        self._install_factory(valid_token="good-token")
        auth.save_token("good-token")

        with patch.object(auth, "get_username", side_effect=AssertionError("should not prompt")), \
             patch.object(auth, "get_password", side_effect=AssertionError("should not prompt")):
            with auth.get_authenticated_factory() as factory:
                self.assertEqual(factory.api_client.default_headers["token"], "good-token")

    def test_falls_back_to_login_when_no_cached_token(self):
        self._install_factory(login_ok=True, login_token="fresh-token")

        with patch.object(auth, "get_username", return_value="alice"), \
             patch.object(auth, "get_password", return_value="correct"):
            with auth.get_authenticated_factory() as factory:
                self.assertEqual(factory.get_authenticate_token(), "fresh-token")

        self.assertEqual(auth.load_token(), "fresh-token")


if __name__ == "__main__":
    unittest.main()
