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


class FakeDownloadApi:
    def __init__(self):
        self.calls = []
        self.fail_scaled = set()  # stored_filenames whose scaled fetch should fail

    def get_attachment1_without_preload_content(self, attachment_name, scaling):
        self.calls.append(("scaled", attachment_name, scaling))
        if attachment_name in self.fail_scaled:
            raise RuntimeError("no scaled variant")
        return SimpleNamespace(data=f"scaled:{attachment_name}".encode())

    def get_attachment_without_preload_content(self, attachment_name):
        self.calls.append(("plain", attachment_name))
        return SimpleNamespace(data=f"plain:{attachment_name}".encode())


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
        self.download_api = FakeDownloadApi()
        self.data = LogbookData(self.api, self.download_api)

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

    def test_invalidate_entries_without_doc_id_also_drops_image_cache(self):
        self.data.attachment_bytes("a.png")
        self.data.invalidate("entries")
        self.data.attachment_bytes("a.png")
        self.assertEqual(self.download_api.calls.count(("scaled", "a.png", "scaled")), 2)

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
        self.data.attachment_bytes("a.png")

        self.data.clear()

        self.data.logbook_types()
        self.data.logbook_systems()
        self.data.logbook_templates()
        self.data.documents(1, 100)
        self.data.entries(10)
        self.data.attachments(10, 100)
        self.data.attachment_bytes("a.png")
        self.assertEqual(self.api.calls.count(("types",)), 2)
        self.assertEqual(self.api.calls.count(("systems",)), 2)
        self.assertEqual(self.api.calls.count(("templates",)), 2)
        self.assertEqual(self.api.calls.count(("docs", 1, 100)), 2)
        self.assertEqual(self.api.calls.count(("entries", 10, True, True)), 2)
        self.assertEqual(self.api.calls.count(("attachments", 10, 100)), 2)
        self.assertEqual(self.download_api.calls.count(("scaled", "a.png", "scaled")), 2)


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


class AttachmentBytesCachingTests(unittest.TestCase):
    def setUp(self):
        self.download_api = FakeDownloadApi()
        self.data = LogbookData(FakeApi(), self.download_api)

    def test_fetches_scaled_by_default(self):
        data = self.data.attachment_bytes("a.png")
        self.assertEqual(data, b"scaled:a.png")
        self.assertEqual(self.download_api.calls, [("scaled", "a.png", "scaled")])

    def test_cached_per_filename_and_scaling(self):
        self.data.attachment_bytes("a.png")
        self.data.attachment_bytes("a.png")
        self.data.attachment_bytes("a.png", scaling=None)
        self.assertEqual(self.download_api.calls.count(("scaled", "a.png", "scaled")), 1)
        self.assertEqual(self.download_api.calls.count(("plain", "a.png")), 1)

    def test_falls_back_to_unscaled_when_scaled_fetch_fails(self):
        self.download_api.fail_scaled.add("a.png")
        data = self.data.attachment_bytes("a.png")
        self.assertEqual(data, b"plain:a.png")
        self.assertEqual(self.download_api.calls, [
            ("scaled", "a.png", "scaled"), ("plain", "a.png"),
        ])

    def test_fallback_result_is_cached(self):
        self.download_api.fail_scaled.add("a.png")
        self.data.attachment_bytes("a.png")
        self.data.attachment_bytes("a.png")
        self.assertEqual(self.download_api.calls.count(("plain", "a.png")), 1)

    def test_failures_are_not_cached(self):
        # No scaling requested, so a failure propagates and must not be cached.
        self.download_api.get_attachment_without_preload_content = lambda name: (_ for _ in ()).throw(
            RuntimeError("boom"))
        with self.assertRaises(RuntimeError):
            self.data.attachment_bytes("a.png", scaling=None)
        self.assertEqual(len(self.data._image_bytes), 0)

    def test_evicts_oldest_past_bound(self):
        self.data.MAX_CACHED_IMAGES = 2
        self.data.attachment_bytes("a.png")
        self.data.attachment_bytes("b.png")
        self.data.attachment_bytes("c.png")
        self.assertEqual(len(self.data._image_bytes), 2)
        # "a.png" was evicted, so fetching it again hits the network.
        self.data.attachment_bytes("a.png")
        self.assertEqual(self.download_api.calls.count(("scaled", "a.png", "scaled")), 2)


if __name__ == "__main__":
    unittest.main()
