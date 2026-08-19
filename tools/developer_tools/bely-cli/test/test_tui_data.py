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

    def get_logbook_systems(self):
        self.calls.append(("systems",))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("boom")
        return [SimpleNamespace(id=1, name="sys-a")]

    def get_logbook_templates(self):
        self.calls.append(("templates",))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("boom")
        return [SimpleNamespace(id=1, name="tmpl-a")]


class FakeSearchResults:
    def __init__(self, docs):
        self.document_results = docs


class FakeUsersApi:
    def __init__(self, calls):
        self._calls = calls

    def get_user_by_username(self, username):
        self._calls.append(("user", username))
        return SimpleNamespace(id=99)


class FakeSearchApi:
    def __init__(self, calls, docs):
        self._calls = calls
        self._docs = docs

    def search_logbook(self, search_text, user_id):
        self._calls.append(("search", search_text, tuple(user_id)))
        return FakeSearchResults(self._docs)


class FakeFactory:
    """Minimal factory for recent_documents(): only users/search apis are used."""

    def __init__(self, docs):
        self.calls = []
        self._docs = docs

    def get_users_api(self):
        return FakeUsersApi(self.calls)

    def get_search_api(self):
        return FakeSearchApi(self.calls, self._docs)


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

    def test_systems_fetched_once_then_cached(self):
        self.data.logbook_systems()
        self.data.logbook_systems()
        self.assertEqual(self.api.calls.count(("systems",)), 1)

    def test_templates_fetched_once_then_cached(self):
        self.data.logbook_templates()
        self.data.logbook_templates()
        self.assertEqual(self.api.calls.count(("templates",)), 1)

    def test_invalidate_systems(self):
        self.data.logbook_systems()
        self.data.invalidate("systems")
        self.data.logbook_systems()
        self.assertEqual(self.api.calls.count(("systems",)), 2)

    def test_invalidate_templates(self):
        self.data.logbook_templates()
        self.data.invalidate("templates")
        self.data.logbook_templates()
        self.assertEqual(self.api.calls.count(("templates",)), 2)

    def test_clear_drops_every_cache(self):
        self.data.logbook_types()
        self.data.logbook_systems()
        self.data.logbook_templates()
        self.data.documents(1, 100)
        self.data.entries(10)
        self.data.attachments(10, 100)

        self.data.clear()

        self.data.logbook_types()
        self.data.logbook_systems()
        self.data.logbook_templates()
        self.data.documents(1, 100)
        self.data.entries(10)
        self.data.attachments(10, 100)
        self.assertEqual(self.api.calls.count(("types",)), 2)
        self.assertEqual(self.api.calls.count(("systems",)), 2)
        self.assertEqual(self.api.calls.count(("templates",)), 2)
        self.assertEqual(self.api.calls.count(("docs", 1, 100)), 2)
        self.assertEqual(self.api.calls.count(("entries", 10, True, True)), 2)
        self.assertEqual(self.api.calls.count(("attachments", 10, 100)), 2)


class RecentDocumentsCachingTests(unittest.TestCase):
    def setUp(self):
        self.data = LogbookData(FakeApi())
        self.docs = [SimpleNamespace(
            object_id=1, object_name="Doc A", logbook_type="ops", last_modified_on="t1",
        )]
        self.factory = FakeFactory(self.docs)

    def test_fetched_once_then_cached_per_username(self):
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.recent_documents(self.factory, "alice", 10)
        self.assertEqual(self.factory.calls.count(("user", "alice")), 1)

    def test_cached_per_username(self):
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.recent_documents(self.factory, "bob", 10)
        self.assertEqual(self.factory.calls.count(("user", "alice")), 1)
        self.assertEqual(self.factory.calls.count(("user", "bob")), 1)

    def test_invalidate_recent_by_username(self):
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.recent_documents(self.factory, "bob", 10)
        self.data.invalidate("recent", username="alice")
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.recent_documents(self.factory, "bob", 10)
        self.assertEqual(self.factory.calls.count(("user", "alice")), 2)
        self.assertEqual(self.factory.calls.count(("user", "bob")), 1)

    def test_invalidate_recent_without_username_clears_all(self):
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.recent_documents(self.factory, "bob", 10)
        self.data.invalidate("recent")
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.recent_documents(self.factory, "bob", 10)
        self.assertEqual(self.factory.calls.count(("user", "alice")), 2)
        self.assertEqual(self.factory.calls.count(("user", "bob")), 2)

    def test_clear_drops_recent_too(self):
        self.data.recent_documents(self.factory, "alice", 10)
        self.data.clear()
        self.data.recent_documents(self.factory, "alice", 10)
        self.assertEqual(self.factory.calls.count(("user", "alice")), 2)


if __name__ == "__main__":
    unittest.main()
