import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bely-cli"))

import commands
import common


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
                 patch.object(commands.belyApi, "LogDocumentOptions") as opts_cls, \
                 patch.object(common.belyApi.exceptions, "NotFoundException", _NF):
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
