import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch

from belyApi.api.logbook_api import LogbookApi

from bely_cli import commands
from test.api_helpers import api_fake, api_mock, factory_mock


class _NF(Exception):
    """Stand-in for belyApi.exceptions.NotFoundException."""


@api_fake(LogbookApi)
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


class CmdShowDocTests(unittest.TestCase):
    def test_show_doc_json(self):
        doc = SimpleNamespace(
            id=42, name="My Doc", description="Shift log", domain=None,
            entity_type_list=[SimpleNamespace(name="ops")], item_type_list=[],
            more_info=None, log_lockout_hours=None)
        with patch.object(commands.auth, "get_factory") as get_factory, \
             patch.object(commands.core, "get_document", return_value=doc):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_show_doc("My Doc", None, fmt="json")
        payload = __import__("json").loads(buf.getvalue())
        self.assertEqual(payload["id"], 42)
        self.assertEqual(payload["logbook_types"], ["ops"])
        get_factory.assert_called_once_with()


class CmdDeleteDocTests(unittest.TestCase):
    def setUp(self):
        self.api = api_mock()
        self.api.get_log_document_by_name.return_value = SimpleNamespace(id=42, name="My Doc")
        self.factory = factory_mock()
        self.factory.get_logbook_api.return_value = self.api
        self.auth_factory = factory_mock()
        self.auth_factory.get_logbook_api.return_value = self.api
        self.auth_ctx = MagicMock()
        self.auth_ctx.__enter__.return_value = self.auth_factory
        self.auth_ctx.__exit__.return_value = False

    def test_delete_yes_returns_structured_result(self):
        self.api.get_log_entries.return_value = []
        with patch.object(commands.auth, "get_factory", return_value=self.factory), \
             patch.object(commands.auth, "get_authenticated_factory", return_value=self.auth_ctx), \
             patch("bely_cli.shell_completion.remove_cached_document") as remove_cached:
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_delete_doc("My Doc", None, yes=True, fmt="json")
        self.assertEqual(__import__("json").loads(buf.getvalue())["status"], "deleted")
        self.api.delete_log_document.assert_called_once_with(log_document_id=42)
        remove_cached.assert_called_once_with(42)

    def test_decline_is_cancelled_without_authentication(self):
        self.api.get_log_entries.return_value = []
        with patch.object(commands.auth, "get_factory", return_value=self.factory), \
             patch.object(commands.auth, "get_authenticated_factory") as authenticated, \
             patch("builtins.input", return_value="n"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                commands.cmd_delete_doc("My Doc", None, fmt="json")
        self.assertEqual(__import__("json").loads(buf.getvalue())["status"], "cancelled")
        authenticated.assert_not_called()

    def test_nonempty_requires_force(self):
        self.api.get_log_entries.return_value = [SimpleNamespace(log_id=1)]
        with patch.object(commands.auth, "get_factory", return_value=self.factory):
            with self.assertRaisesRegex(ValueError, "--force"):
                commands.cmd_delete_doc("My Doc", None, yes=True)

    def test_force_does_not_imply_yes(self):
        self.api.get_log_entries.return_value = [SimpleNamespace(log_id=1)]
        with patch.object(commands.auth, "get_factory", return_value=self.factory), \
             patch.object(commands.auth, "get_authenticated_factory") as authenticated, \
             patch("builtins.input", return_value="n"):
            commands.cmd_delete_doc("My Doc", None, force=True)
        authenticated.assert_not_called()

    def test_no_prompt_requires_yes(self):
        self.api.get_log_entries.return_value = []
        with patch.object(commands.auth, "get_factory", return_value=self.factory), \
             patch.object(commands, "is_no_prompt", return_value=True), \
             patch("bely_cli.common.is_no_prompt", return_value=True):
            with self.assertRaisesRegex(ValueError, "--yes"):
                commands.cmd_delete_doc("My Doc", None)


class CmdNewDocTests(unittest.TestCase):
    def test_creates_doc_and_first_entry_from_file(self):
        api = FakeApi()

        factory = factory_mock()
        factory.get_logbook_api.return_value = api

        auth_factory = factory_mock()
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
                 patch("belyApi.exceptions.NotFoundException", _NF), \
                 patch("bely_cli.shell_completion.add_cached_document") as cache_document:
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
        cache_document.assert_called_once_with(ANY, "ops")
        cached_doc = cache_document.call_args.args[0]
        self.assertEqual((cached_doc.id, cached_doc.name), (42, "My Doc"))
        self.assertIs(api.created, opts_cls.return_value)
        self.assertEqual(api.entry_saved.log_entry, "hello\n")
        self.assertEqual(api.entry_saved.log_id, 99)

        out = buf.getvalue()
        self.assertIn('New document "My Doc" created, id=42', out)
        self.assertIn("Log entry added, log_id=99", out)


if __name__ == "__main__":
    unittest.main()
