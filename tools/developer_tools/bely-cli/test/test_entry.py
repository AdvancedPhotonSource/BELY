import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from belyApi.api.logbook_api import LogbookApi

from bely_cli import entry
from test.api_helpers import api_fake, factory_mock, method_mock


@api_fake(LogbookApi)
class FakeApi:
    """Minimal fake exposing only the methods entry.py touches."""

    def __init__(self, existing_entries=None):
        self.doc = SimpleNamespace(id=42, name="My Doc")
        self.existing_entries = existing_entries or []
        self.entry_saved = None
        self.uploaded = None
        self.attachments = []

    def get_log_document_by_name(self, name):
        return self.doc

    def get_log_entry_template(self, log_document_id):
        return SimpleNamespace(log_id=None, log_entry="")

    def get_log_entries(self, log_document_id, load_replies=None):
        return self.existing_entries

    def add_update_log_entry(self, log_entry):
        self.entry_saved = log_entry
        if log_entry.log_id is None:
            log_entry.log_id = 99
        return log_entry

    def upload_attachment(self, log_document_id, log_id, body, append_reference, file_name):
        self.uploaded = (log_document_id, log_id, body, append_reference, file_name)
        return SimpleNamespace(
            id=7, original_filename=file_name, stored_filename=f"stored_{file_name}",
            download_path=f"/download/{file_name}", markdown_reference=f"![{file_name}](/download/{file_name})",
        )

    def get_log_entry_attachments(self, log_document_id, log_id):
        return self.attachments


def _patch_auth(api):
    """Patch entry.auth.get_factory and get_authenticated_factory to yield `api`."""
    factory = factory_mock()
    factory.get_logbook_api.return_value = api

    auth_factory = factory_mock()
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
                        fmt="text",
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

    def test_add_entry_json_format(self):
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
                        fmt="json",
                    )
            finally:
                for p in patches:
                    p.stop()
        finally:
            os.unlink(tmp_path)

        # In JSON mode the only stdout is the structured result.
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["log_id"], 99)
        self.assertEqual(payload["status"], "added")
        self.assertEqual(payload["doc"], "My Doc")


class CmdReplyEntryTests(unittest.TestCase):
    def test_add_reply_with_text(self):
        parent = SimpleNamespace(log_id=10, log_entry="parent", log_replies=[])
        api = FakeApi(existing_entries=[parent])
        api.get_log_entries = method_mock(
            LogbookApi, "get_log_entries", wraps=api.get_log_entries)
        patches = _patch_auth(api)
        for patcher in patches:
            patcher.start()
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                entry.cmd_reply_entry(
                    "My Doc", None, 10, None, "reply text", None, fmt="json")
        finally:
            for patcher in patches:
                patcher.stop()

        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["parent_log_id"], 10)
        self.assertEqual(payload["log_id"], 99)
        self.assertEqual(payload["status"], "added")
        self.assertEqual(api.entry_saved.parent_log_id, 10)
        self.assertEqual(api.entry_saved.log_entry, "reply text")
        api.get_log_entries.assert_called_once_with(
            log_document_id=42, load_replies=True)

    def test_reply_requires_top_level_parent(self):
        reply = SimpleNamespace(log_id=11, log_entry="reply", log_replies=[])
        parent = SimpleNamespace(log_id=10, log_entry="parent", log_replies=[reply])
        api = FakeApi(existing_entries=[parent])
        with patch.object(entry.auth, "get_factory") as get_factory, \
             patch.object(entry.auth, "get_authenticated_factory") as authenticated:
            get_factory.return_value.get_logbook_api.return_value = api
            with self.assertRaisesRegex(ValueError, "top-level entry"):
                entry.cmd_reply_entry(
                    "My Doc", None, 11, None, "nested reply", None)
        authenticated.assert_not_called()

    def test_add_reply_with_attachment(self):
        parent = SimpleNamespace(log_id=10, log_entry="parent", log_replies=[])
        api = FakeApi(existing_entries=[parent])
        tmp_path = _write_tmp("attachment")
        try:
            patches = _patch_auth(api)
            for patcher in patches:
                patcher.start()
            try:
                entry.cmd_reply_entry(
                    "My Doc", None, 10, None, "reply", tmp_path)
            finally:
                for patcher in patches:
                    patcher.stop()
        finally:
            os.unlink(tmp_path)
        self.assertEqual(api.uploaded[:2], (42, 99))


class CmdAttachmentTests(unittest.TestCase):
    def test_add_attachment_to_existing_entry(self):
        existing = SimpleNamespace(log_id=10, log_entry="entry", entered_by_username="alice")
        api = FakeApi(existing_entries=[existing])
        tmp_path = _write_tmp("attachment")
        try:
            patches = _patch_auth(api)
            for p in patches:
                p.start()
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    entry.cmd_add_attachment("My Doc", None, 10, tmp_path, fmt="json")
            finally:
                for p in patches:
                    p.stop()
        finally:
            os.unlink(tmp_path)

        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["attachment"]["id"], 7)
        self.assertEqual(api.uploaded[:2], (42, 10))
        self.assertTrue(api.uploaded[3])

    def test_list_attachments_json(self):
        existing = SimpleNamespace(log_id=10, log_entry="entry", entered_by_username="alice")
        api = FakeApi(existing_entries=[existing])
        api.attachments = [SimpleNamespace(
            id=7, original_filename="plot.png", stored_filename="stored.png",
            download_path="/download/stored.png", markdown_reference="![plot.png](/download/stored.png)",
        )]
        with patch.object(entry.auth, "get_factory") as get_factory:
            get_factory.return_value.get_logbook_api.return_value = api
            buf = io.StringIO()
            with redirect_stdout(buf):
                entry.cmd_list_attachments("My Doc", None, 10, fmt="json")

        payload = json.loads(buf.getvalue())
        self.assertEqual(payload[0]["id"], 7)
        self.assertEqual(payload[0]["original_filename"], "plot.png")

    def test_list_attachments_delegates_entry_validation_to_endpoint(self):
        api = FakeApi()
        api.get_log_entry_attachments = method_mock(
            LogbookApi, "get_log_entry_attachments", side_effect=RuntimeError("entry not found"))
        with patch.object(entry.auth, "get_factory") as get_factory:
            get_factory.return_value.get_logbook_api.return_value = api
            with self.assertRaisesRegex(RuntimeError, "entry not found"):
                entry.cmd_list_attachments("My Doc", None, 10)
        api.get_log_entry_attachments.assert_called_once_with(log_document_id=42, log_id=10)


class CmdListEntryTests(unittest.TestCase):
    def test_list_with_replies(self):
        reply = SimpleNamespace(
            log_id=11, log_entry="reply", log_replies=None,
            entered_on_date_time=None, entered_by_username="bob")
        parent = SimpleNamespace(
            log_id=10, log_entry="parent", log_replies=[reply],
            entered_on_date_time=None, entered_by_username="alice")
        api = FakeApi(existing_entries=[parent])
        api.get_log_entries = method_mock(
            LogbookApi, "get_log_entries", wraps=api.get_log_entries)
        with patch.object(entry.auth, "get_factory") as get_factory:
            get_factory.return_value.get_logbook_api.return_value = api
            buf = io.StringIO()
            with redirect_stdout(buf):
                entry.cmd_list_entries("My Doc", None, replies=True, fmt="json")
        payload = json.loads(buf.getvalue())
        self.assertEqual([item["log_id"] for item in payload], [10, 11])
        self.assertEqual(payload[0]["parent_log_id"], "")
        self.assertEqual(payload[1]["parent_log_id"], 10)
        api.get_log_entries.assert_called_once_with(
            log_document_id=42, load_replies=True)


class CmdGetEntryTests(unittest.TestCase):
    def test_get_finds_nested_reply(self):
        reply = SimpleNamespace(log_id=11, log_entry="reply text", log_replies=None)
        parent = SimpleNamespace(log_id=10, log_entry="parent", log_replies=[reply])
        api = FakeApi(existing_entries=[parent])
        with patch.object(entry.auth, "get_factory") as get_factory, \
             tempfile.TemporaryDirectory() as output_dir:
            get_factory.return_value.get_logbook_api.return_value = api
            api.get_log_entries = method_mock(
                LogbookApi, "get_log_entries", wraps=api.get_log_entries)
            buf = io.StringIO()
            with redirect_stdout(buf):
                entry.cmd_get_entry(
                    "My Doc", None, 11, output_dir=output_dir, fmt="json")
            payload = json.loads(buf.getvalue())
            with open(payload["path"]) as output:
                self.assertEqual(output.read(), "reply text")
        api.get_log_entries.assert_called_once_with(
            log_document_id=42, load_replies=True)


class CmdDeleteTests(unittest.TestCase):
    def test_delete_reply(self):
        reply = SimpleNamespace(log_id=11, log_replies=None)
        parent = SimpleNamespace(log_id=10, log_replies=[reply])
        api = FakeApi(existing_entries=[parent])
        api.delete_log_entry = method_mock(LogbookApi, "delete_log_entry")
        api.get_log_entries = method_mock(
            LogbookApi, "get_log_entries", wraps=api.get_log_entries)
        patches = _patch_auth(api)
        for patcher in patches:
            patcher.start()
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                entry.cmd_delete_entry("My Doc", None, 11, yes=True, fmt="json")
        finally:
            for patcher in patches:
                patcher.stop()
        self.assertEqual(json.loads(buf.getvalue())["status"], "deleted")
        api.delete_log_entry.assert_called_once_with(log_document_id=42, log_id=11)
        api.get_log_entries.assert_called_once_with(
            log_document_id=42, load_replies=True)

    def test_delete_attachment_by_numeric_id(self):
        api = FakeApi()
        api.attachments = [SimpleNamespace(id=7)]
        api.delete_attachment = method_mock(LogbookApi, "delete_attachment")
        patches = _patch_auth(api)
        for patcher in patches:
            patcher.start()
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                entry.cmd_delete_attachment("My Doc", None, 10, 7, yes=True, fmt="json")
        finally:
            for patcher in patches:
                patcher.stop()
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["attachment_id"], 7)
        self.assertEqual(payload["status"], "deleted")
        api.delete_attachment.assert_called_once_with(
            log_document_id=42, log_id=10, attachment_id=7)

    def test_missing_entry_and_attachment_fail(self):
        api = FakeApi()
        patches = _patch_auth(api)
        for patcher in patches:
            patcher.start()
        try:
            with self.assertRaisesRegex(ValueError, "entry with log_id=99 not found"):
                entry.cmd_delete_entry("My Doc", None, 99, yes=True)
            with self.assertRaisesRegex(ValueError, "attachment id=99 not found"):
                entry.cmd_delete_attachment("My Doc", None, 10, 99, yes=True)
        finally:
            for patcher in patches:
                patcher.stop()


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
                        fmt="text",
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
