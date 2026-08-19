import unittest
from types import SimpleNamespace

from bely_cli.tui.data import LogbookData


class FakeApi:
    def __init__(self):
        self.calls = []
        self.fail_next = False

    def get_logbook_types(self):
        self.calls.append(("types",))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("boom")
        return [SimpleNamespace(id=1, name="ops")]

    def get_log_documents(self, logbook_type_id, limit):
        self.calls.append(("docs", logbook_type_id, limit))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("boom")
        return [SimpleNamespace(id=10, name="Doc")]

    def get_log_entries(self, log_document_id, load_replies, load_reactions):
        self.calls.append(("entries", log_document_id, load_replies, load_reactions))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("boom")
        return [SimpleNamespace(log_id=100)]

    def get_log_entry_attachments(self, log_document_id, log_id):
        self.calls.append(("attachments", log_document_id, log_id))
        return [SimpleNamespace(original_filename="a.png")]


class LogbookDataCachingTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeApi()
        self.data = LogbookData(self.api)

    def test_types_fetched_once_then_cached(self):
        self.data.logbook_types()
        self.data.logbook_types()
        self.assertEqual(self.api.calls.count(("types",)), 1)

    def test_docs_cached_per_type_id(self):
        self.data.documents(1, 100)
        self.data.documents(1, 100)
        self.data.documents(2, 100)
        self.assertEqual(self.api.calls.count(("docs", 1, 100)), 1)
        self.assertEqual(self.api.calls.count(("docs", 2, 100)), 1)

    def test_entries_pass_load_replies_and_reactions(self):
        self.data.entries(10)
        self.assertIn(("entries", 10, True, True), self.api.calls)

    def test_entries_cached_per_doc_id(self):
        self.data.entries(10)
        self.data.entries(10)
        self.assertEqual(self.api.calls.count(("entries", 10, True, True)), 1)

    def test_attachments_keyed_by_doc_and_log_id(self):
        self.data.attachments(10, 100)
        self.data.attachments(10, 100)
        self.data.attachments(10, 200)
        self.assertEqual(self.api.calls.count(("attachments", 10, 100)), 1)
        self.assertEqual(self.api.calls.count(("attachments", 10, 200)), 1)

    def test_failures_are_not_cached(self):
        self.api.fail_next = True
        with self.assertRaises(RuntimeError):
            self.data.logbook_types()
        # second call retries the network instead of returning a cached failure
        result = self.data.logbook_types()
        self.assertEqual(result[0].name, "ops")
        self.assertEqual(self.api.calls.count(("types",)), 2)

    def test_invalidate_types(self):
        self.data.logbook_types()
        self.data.invalidate("types")
        self.data.logbook_types()
        self.assertEqual(self.api.calls.count(("types",)), 2)

    def test_invalidate_docs_by_type_id(self):
        self.data.documents(1, 100)
        self.data.documents(2, 100)
        self.data.invalidate("docs", type_id=1)
        self.data.documents(1, 100)
        self.data.documents(2, 100)
        self.assertEqual(self.api.calls.count(("docs", 1, 100)), 2)
        self.assertEqual(self.api.calls.count(("docs", 2, 100)), 1)

    def test_invalidate_entries_by_doc_id_also_drops_its_attachments(self):
        self.data.entries(10)
        self.data.attachments(10, 100)
        self.data.invalidate("entries", doc_id=10)
        self.data.entries(10)
        self.data.attachments(10, 100)
        self.assertEqual(self.api.calls.count(("entries", 10, True, True)), 2)
        self.assertEqual(self.api.calls.count(("attachments", 10, 100)), 2)

    def test_invalidate_unknown_level_raises(self):
        with self.assertRaises(ValueError):
            self.data.invalidate("bogus")


if __name__ == "__main__":
    unittest.main()
