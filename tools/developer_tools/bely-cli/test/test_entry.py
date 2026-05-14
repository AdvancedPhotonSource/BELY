import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bely-cli"))

import entry


class FakeApi:
    """Minimal fake exposing only the methods entry.py touches."""

    def __init__(self, existing_entries=None):
        self.doc = SimpleNamespace(id=42, name="My Doc")
        self.existing_entries = existing_entries or []
        self.entry_saved = None

    def get_log_document_by_name(self, name):
        return self.doc

    def get_log_entry_template(self, log_document_id):
        return SimpleNamespace(log_id=None, log_entry="")

    def get_log_entries(self, log_document_id):
        return self.existing_entries

    def add_update_log_entry(self, log_entry):
        self.entry_saved = log_entry
        if log_entry.log_id is None:
            log_entry.log_id = 99
        return log_entry


def _patch_auth(api):
    """Patch entry.auth.get_factory and get_authenticated_factory to yield `api`."""
    factory = MagicMock()
    factory.get_logbook_api.return_value = api

    auth_factory = MagicMock()
    auth_factory.get_logbook_api.return_value = api
    auth_ctx = MagicMock()
    auth_ctx.__enter__.return_value = auth_factory
    auth_ctx.__exit__.return_value = False

    return [
        patch.object(entry.auth, "get_factory", return_value=factory),
        patch.object(entry.auth, "get_authenticated_factory", return_value=auth_ctx),
    ]


def _write_tmp(content):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(content)
        return f.name


class CmdAddEntryTests(unittest.TestCase):
    def test_add_entry_with_file_and_name(self):
        api = FakeApi()
        tmp_path = _write_tmp("added content\n")

        try:
            patches = _patch_auth(api)
            for p in patches:
                p.start()
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    entry.cmd_add_entry(
                        doc_name="My Doc",
                        doc_id=None,
                        file=tmp_path,
                        text=None,
                        add_attachment=None,
                    )
            finally:
                for p in patches:
                    p.stop()
        finally:
            os.unlink(tmp_path)

        self.assertIsNotNone(api.entry_saved)
        self.assertEqual(api.entry_saved.log_entry, "added content\n")
        self.assertEqual(api.entry_saved.log_id, 99)
        self.assertIn('Log entry added to "My Doc", log_id=99', buf.getvalue())


class CmdUpdateEntryTests(unittest.TestCase):
    def test_update_entry_with_file_and_name(self):
        existing = SimpleNamespace(
            log_id=10,
            log_entry="old content",
            entered_by_username="alice",
        )
        api = FakeApi(existing_entries=[existing])
        tmp_path = _write_tmp("updated content\n")

        try:
            patches = _patch_auth(api)
            patches.append(patch.object(entry.auth, "get_username", return_value="alice"))
            for p in patches:
                p.start()
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    entry.cmd_update_entry(
                        doc_name="My Doc",
                        doc_id=None,
                        entry_id=None,
                        file=tmp_path,
                        text=None,
                        add_attachment=None,
                    )
            finally:
                for p in patches:
                    p.stop()
        finally:
            os.unlink(tmp_path)

        self.assertIs(api.entry_saved, existing)
        self.assertEqual(api.entry_saved.log_entry, "updated content\n")
        self.assertEqual(api.entry_saved.log_id, 10)
        self.assertIn('Log entry updated in "My Doc", log_id=10', buf.getvalue())


if __name__ == "__main__":
    unittest.main()
