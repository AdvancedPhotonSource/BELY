import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bely_cli import core


class FakeLogbookApi:
    def __init__(self):
        self.types = [SimpleNamespace(id=1, name="ops", display_name="Ops")]
        self.systems = [SimpleNamespace(id=2, name="SR", description="Storage Ring")]
        self.templates = [SimpleNamespace(id=3, name="shift", description="Shift template")]
        self.created = None
        self.saved = None
        self.uploaded = None

    def get_logbook_types(self):
        return self.types

    def get_logbook_systems(self):
        return self.systems

    def get_logbook_templates(self):
        return self.templates

    def create_logbook_document(self, log_document_options):
        self.created = log_document_options
        return SimpleNamespace(id=42, name=log_document_options.name)

    def get_log_entry_template(self, log_document_id):
        return SimpleNamespace(log_id=None, log_entry="")

    def add_update_log_entry(self, log_entry):
        self.saved = log_entry
        if log_entry.log_id is None:
            log_entry.log_id = 99
        return log_entry

    def upload_attachment(self, log_document_id, log_id, body, append_reference, file_name):
        self.uploaded = (log_document_id, log_id, body, append_reference, file_name)
        return SimpleNamespace(
            original_filename=file_name,
            stored_filename=f"stored_{file_name}",
            download_path=f"/download/{file_name}",
            markdown_reference=f"![{file_name}](/download/{file_name})",
        )


class FindLookupTests(unittest.TestCase):
    def test_find_logbook_type_case_insensitive(self):
        api = FakeLogbookApi()
        t = core.find_logbook_type(api, "OPS")
        self.assertEqual(t.id, 1)

    def test_find_logbook_type_unknown_lists_available(self):
        api = FakeLogbookApi()
        with self.assertRaises(ValueError) as ctx:
            core.find_logbook_type(api, "nope")
        self.assertIn("ops", str(ctx.exception))

    def test_find_systems_resolves_csv_to_ids(self):
        api = FakeLogbookApi()
        api.systems.append(SimpleNamespace(id=4, name="Software", description=""))
        self.assertEqual(core.find_systems(api, "SR, software"), [2, 4])

    def test_find_systems_unknown_name_raises(self):
        api = FakeLogbookApi()
        with self.assertRaises(ValueError):
            core.find_systems(api, "nope")

    def test_find_template_case_insensitive(self):
        api = FakeLogbookApi()
        self.assertEqual(core.find_template(api, "SHIFT").id, 3)


class ResolveDocTests(unittest.TestCase):
    def test_both_name_and_id_raises(self):
        with self.assertRaises(ValueError):
            core.resolve_doc(None, "name", 1)

    def test_neither_raises(self):
        with self.assertRaises(ValueError):
            core.resolve_doc(None, None, None)

    def test_by_id_does_not_touch_the_api(self):
        doc = core.resolve_doc(None, None, 7)
        self.assertEqual(doc.id, 7)
        self.assertEqual(doc.name, "id=7")

    def test_by_name_not_found_raises(self):
        api = MagicMock()
        with patch("bely_cli.common.find_logdoc", return_value=None):
            with self.assertRaises(ValueError):
                core.resolve_doc(api, "missing", None)


class FakeOptions:
    """Stand-in for belyApi.LogDocumentOptions: a plain object so hasattr()
    reflects only what create_document actually set (unlike a MagicMock,
    which auto-vivifies any attribute access)."""

    def __init__(self, name, logbook_type_id):
        self.name = name
        self.logbook_type_id = logbook_type_id


class CreateDocumentTests(unittest.TestCase):
    def test_builds_options_and_creates(self):
        api = FakeLogbookApi()
        with patch("belyApi.LogDocumentOptions", FakeOptions):
            doc = core.create_document(
                api, "My Doc", 1, system_id_list=[2], template_id=3,
                skip_default_template=True,
            )
        opts = api.created
        self.assertEqual(opts.name, "My Doc")
        self.assertEqual(opts.logbook_type_id, 1)
        self.assertEqual(opts.system_id_list, [2])
        self.assertEqual(opts.template_id, 3)
        self.assertTrue(opts.skip_default_logbook_type_template)
        self.assertEqual(doc.id, 42)

    def test_optional_fields_omitted_when_not_given(self):
        api = FakeLogbookApi()
        with patch("belyApi.LogDocumentOptions", FakeOptions):
            core.create_document(api, "My Doc", 1)
        opts = api.created
        self.assertFalse(hasattr(opts, "system_id_list"))
        self.assertFalse(hasattr(opts, "template_id"))
        self.assertFalse(hasattr(opts, "skip_default_logbook_type_template"))


class EntryTests(unittest.TestCase):
    def test_new_entry_template(self):
        api = FakeLogbookApi()
        entry = core.new_entry_template(api, 42)
        self.assertEqual(entry.log_entry, "")

    def test_save_entry_sets_content_and_saves(self):
        api = FakeLogbookApi()
        entry = SimpleNamespace(log_id=None, log_entry="")
        saved = core.save_entry(api, entry, "hello")
        self.assertEqual(saved.log_entry, "hello")
        self.assertEqual(saved.log_id, 99)
        self.assertIs(api.saved, entry)

    def test_find_entry_found_and_missing(self):
        entries = [SimpleNamespace(log_id=1), SimpleNamespace(log_id=2)]
        self.assertIs(core.find_entry(entries, 2), entries[1])
        self.assertIsNone(core.find_entry(entries, 99))

    def test_last_entry_by_user_case_insensitive_and_last_match(self):
        entries = [
            SimpleNamespace(log_id=1, entered_by_username="alice"),
            SimpleNamespace(log_id=2, entered_by_username="Bob"),
            SimpleNamespace(log_id=3, entered_by_username="BOB"),
        ]
        entry = core.last_entry_by_user(entries, "bob")
        self.assertEqual(entry.log_id, 3)

    def test_last_entry_by_user_no_match(self):
        entries = [SimpleNamespace(log_id=1, entered_by_username="alice")]
        self.assertIsNone(core.last_entry_by_user(entries, "bob"))

    def test_entry_list_items_builds_rows(self):
        import datetime
        entries = [
            SimpleNamespace(
                log_id=1,
                entered_on_date_time=datetime.datetime(2026, 1, 2, 3, 4),
                entered_by_username="alice",
                log_entry="first line\nsecond line",
            ),
            SimpleNamespace(
                log_id=2, entered_on_date_time=None, entered_by_username=None, log_entry=None,
            ),
        ]
        items = core.entry_list_items(entries)
        self.assertEqual(items[0]["date"], "2026-01-02 03:04")
        self.assertEqual(items[0]["author"], "alice")
        self.assertEqual(items[0]["snippet"], "first line")
        self.assertEqual(items[1], {"log_id": 2, "date": "", "author": "", "snippet": ""})

    def test_entry_list_items_truncates_long_snippet(self):
        entries = [SimpleNamespace(
            log_id=1, entered_on_date_time=None, entered_by_username="a",
            log_entry="x" * 100,
        )]
        snippet = core.entry_list_items(entries)[0]["snippet"]
        self.assertEqual(len(snippet), 60)
        self.assertTrue(snippet.endswith("..."))


class AttachmentTests(unittest.TestCase):
    def test_validate_attachment_path_missing_raises(self):
        with self.assertRaises(ValueError):
            core.validate_attachment_path("/no/such/file.txt")

    def test_validate_attachment_path_expands_user(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertEqual(core.validate_attachment_path(f.name), f.name)

    def test_upload_attachment_returns_dict(self):
        api = FakeLogbookApi()
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            info = core.upload_attachment(api, 42, 99, f.name)
        basename = os.path.basename(f.name)
        self.assertEqual(info["original_filename"], basename)
        self.assertEqual(api.uploaded[0], 42)
        self.assertEqual(api.uploaded[1], 99)


class RecentDocumentsTests(unittest.TestCase):
    def test_sorts_by_last_modified_desc_and_truncates(self):
        import datetime as dt

        docs = [
            SimpleNamespace(object_id=1, object_name="Old", logbook_type="ops",
                             last_modified_on=dt.datetime(2026, 1, 1)),
            SimpleNamespace(object_id=2, object_name="New", logbook_type="ops",
                             last_modified_on=dt.datetime(2026, 6, 1)),
            SimpleNamespace(object_id=3, object_name="Mid", logbook_type="ops",
                             last_modified_on=dt.datetime(2026, 3, 1)),
        ]
        factory = MagicMock()
        factory.get_users_api.return_value.get_user_by_username.return_value = SimpleNamespace(id=7)
        factory.get_search_api.return_value.search_logbook.return_value = SimpleNamespace(document_results=docs)

        result = core.recent_documents(factory, "alice", limit=2)

        self.assertEqual([d.name for d in result], ["New", "Mid"])
        self.assertEqual(result[0].id, 2)
        self.assertEqual(result[0].more_info.last_modified_on_date_time, dt.datetime(2026, 6, 1))

    def test_user_lookup_failure_wrapped_as_runtime_error(self):
        factory = MagicMock()
        factory.get_users_api.return_value.get_user_by_username.side_effect = Exception("boom")
        with self.assertRaises(RuntimeError):
            core.recent_documents(factory, "alice", limit=10)


class ConfigTests(unittest.TestCase):
    def test_collect_config_masks_password(self):
        with patch.object(core.config, "load_settings", return_value={"host": "h"}), \
             patch.dict(os.environ, {"BELY_HOST": "h", "BELY_PASSWORD": "secret"}, clear=False):
            data = core.collect_config()
        self.assertEqual(data["environment"]["BELY_HOST"], "h")
        self.assertEqual(data["environment"]["BELY_PASSWORD"], "****")
        self.assertEqual(data["settings"], {"host": "h"})

    def test_ensure_settings_file_creates_when_missing(self):
        with tempfile.TemporaryDirectory() as d:
            settings_file = os.path.join(d, "sub", "settings.yaml")
            with patch.object(core.config, "SETTINGS_FILE", settings_file), \
                 patch.object(core.config, "CONFIG_DIR", os.path.dirname(settings_file)):
                path = core.ensure_settings_file()
                self.assertTrue(os.path.exists(settings_file))
                self.assertEqual(path, settings_file)


if __name__ == "__main__":
    unittest.main()
