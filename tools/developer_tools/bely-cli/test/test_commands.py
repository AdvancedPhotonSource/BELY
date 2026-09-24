import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bely_cli import commands


class _NF(Exception):
    """Stand-in for belyApi.exceptions.NotFoundException."""


class FakeApi:
    def __init__(self):
        self.created = None
        self.entry_saved = None

    def get_logbook_types(self):
        return [SimpleNamespace(id=1, name="ops", display_name="Ops")]

    def get_log_document_by_name(self, name):
        raise _NF()

    def create_logbook_document(self, log_document_options):
        self.created = log_document_options
        return SimpleNamespace(id=42, name="My Doc")

    def get_log_entries(self, log_document_id):
        return []

    def get_log_entry_template(self, log_document_id):
        return SimpleNamespace(log_id=None, log_entry="")

    def add_update_log_entry(self, log_entry):
        self.entry_saved = log_entry
        log_entry.log_id = 99
        return log_entry


class CmdAuthTests(unittest.TestCase):
    def test_login_uses_resolved_credentials(self):
        with patch.object(commands.auth, "get_username", return_value="alice"), \
             patch.object(commands.auth, "get_password", return_value="secret") as get_password, \
             patch.object(commands.auth, "login") as login:
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_login()

        get_password.assert_called_once_with("alice")
        login.assert_called_once_with("alice", "secret")
        self.assertEqual(buf.getvalue(), "Logged in as alice.\n")

    def test_logout_reports_current_session(self):
        with patch.object(commands.auth, "logout", return_value=True):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_logout()

        self.assertEqual(buf.getvalue(), "Logged out.\n")

    def test_logout_reports_when_not_logged_in(self):
        with patch.object(commands.auth, "logout", return_value=False):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_logout()

        self.assertEqual(buf.getvalue(), "Not logged in.\n")

    def test_verify_reports_valid_token(self):
        with patch.object(commands.auth, "load_token", return_value="token"), \
             patch.object(commands.auth, "verify", return_value=True):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_verify(fmt="json")

        self.assertEqual(buf.getvalue(), '{"authenticated": true}\n')

    def test_verify_explains_when_token_is_not_found(self):
        with patch.object(commands.auth, "load_token", return_value=None), \
             patch.object(commands.auth, "verify") as verify:
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_verify()

        verify.assert_not_called()
        self.assertEqual(
            buf.getvalue(),
            "No cached authentication token found. Run 'bely-cli auth login' first.\n",
        )

    def test_verify_structured_output_identifies_missing_token(self):
        with patch.object(commands.auth, "load_token", return_value=None):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_verify(fmt="json")

        self.assertEqual(
            buf.getvalue(),
            '{"authenticated": false, "reason": "token_not_found"}\n',
        )

    def test_verify_reports_invalid_or_expired_token(self):
        with patch.object(commands.auth, "load_token", return_value="token"), \
             patch.object(commands.auth, "verify", return_value=False):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_auth_verify()

        self.assertEqual(
            buf.getvalue(),
            "Authentication token is invalid or expired. "
            "Run 'bely-cli auth login' to authenticate again.\n",
        )


class CmdNewDocTests(unittest.TestCase):
    def test_creates_doc_and_first_entry_from_file(self):
        api = FakeApi()

        factory = MagicMock()
        factory.get_logbook_api.return_value = api

        auth_factory = MagicMock()
        auth_factory.get_logbook_api.return_value = api
        auth_ctx = MagicMock()
        auth_ctx.__enter__.return_value = auth_factory
        auth_ctx.__exit__.return_value = False

        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("hello\n")
            tmp_path = f.name

        try:
            with patch.object(commands.auth, "get_factory", return_value=factory), \
                 patch.object(commands.auth, "get_authenticated_factory", return_value=auth_ctx), \
                 patch("belyApi.LogDocumentOptions") as opts_cls, \
                 patch("belyApi.exceptions.NotFoundException", _NF):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    commands.cmd_new_doc(
                        type_="ops",
                        name="My Doc",
                        file=tmp_path,
                        template=None,
                        systems=None,
                        no_template=False,
                        output_dir=None,
                        list_options=None,
                        fmt="text",
                    )
        finally:
            os.unlink(tmp_path)

        opts_cls.assert_called_once_with(name="My Doc", logbook_type_id=1)
        self.assertIs(api.created, opts_cls.return_value)
        self.assertEqual(api.entry_saved.log_entry, "hello\n")
        self.assertEqual(api.entry_saved.log_id, 99)

        out = buf.getvalue()
        self.assertIn('New document "My Doc" created, id=42', out)
        self.assertIn("Log entry added, log_id=99", out)


if __name__ == "__main__":
    unittest.main()
