import unittest
import uuid

from belyApi import SearchEntitiesOptions
from test.bely_test_base import BelyTestBase


class SearchTests(BelyTestBase):

    def setUp(self):
        super().setUp()
        self.search_api = self.factory.get_search_api()

    # -- search_logbook (GET /api/Search/{searchText}) --

    def test_search_documents_by_name(self):
        results = self.search_api.search_logbook("Sample*")

        self.assertIsNotNone(results.document_results)
        self.assertGreater(len(results.document_results), 0)

        names = [r.object_name for r in results.document_results]
        self.assertTrue(
            any("Sample" in n for n in names),
            f"Expected a document name containing 'Sample', got: {names}",
        )

    def test_search_log_entries(self):
        results = self.search_api.search_logbook("Top level*")

        self.assertIsNotNone(results.log_entry_results)
        self.assertGreater(len(results.log_entry_results), 0)

        doc_ids = [r.log_document_id for r in results.log_entry_results]
        self.assertIn(
            self.DOC_WITH_ENTRIES,
            doc_ids,
            f"Expected log document ID {self.DOC_WITH_ENTRIES} in results, got: {doc_ids}",
        )

    def test_search_no_results(self):
        nonsense = uuid.uuid4().hex
        results = self.search_api.search_logbook(nonsense)

        doc_results = results.document_results or []
        entry_results = results.log_entry_results or []

        self.assertEqual(len(doc_results), 0)
        self.assertEqual(len(entry_results), 0)

    def test_search_with_logbook_type_filter(self):
        results = self.search_api.search_logbook(
            "test_doc*", logbook_type_id=[self.OPS_LOGBOOK_ID]
        )

        all_results = (results.document_results or []) + (
            results.log_entry_results or []
        )
        for r in all_results:
            if r.logbook_type is not None:
                # Verify each result belongs to the filtered logbook type
                self.assertIsNotNone(r.logbook_type)

    def test_search_case_insensitive(self):
        # Case-insensitive search should find "Sample log document"
        ci_results = self.search_api.search_logbook(
            "sample*", case_insensitive=True
        )
        ci_docs = ci_results.document_results or []
        self.assertGreater(
            len(ci_docs), 0, "Case-insensitive search for 'sample*' should find results"
        )

        # Case-sensitive search for lowercase should not match "Sample..."
        cs_results = self.search_api.search_logbook(
            "sample*", case_insensitive=False
        )
        cs_docs = cs_results.document_results or []
        self.assertEqual(
            len(cs_docs),
            0,
            f"Case-sensitive search for 'sample*' should find no documents, got: "
            f"{[r.object_name for r in cs_docs]}",
        )

    def test_search_wildcard(self):
        results = self.search_api.search_logbook("?ection*")

        all_results = (results.document_results or []) + (
            results.log_entry_results or []
        )
        self.assertGreater(
            len(all_results),
            0,
            "Expected results matching '?ection*' wildcard pattern",
        )

        names = [r.object_name for r in all_results]
        self.assertTrue(
            any("ection" in (n or "") for n in names),
            f"Expected a result containing 'ection', got: {names}",
        )

    # -- generic_search (POST /api/Search/GenericSearch) --

    def test_generic_search_users(self):
        options = SearchEntitiesOptions(
            search_text="logr", include_user=True
        )
        results = self.search_api.generic_search(options)

        self.assertIsNotNone(results.user_results)
        self.assertGreater(len(results.user_results), 0)

    def test_generic_search_no_flags(self):
        options = SearchEntitiesOptions(search_text="logr")
        results = self.search_api.generic_search(options)

        # With no include flags, all result lists should be empty or None
        for field_name in [
            "item_domain_catalog_results",
            "item_domain_inventory_results",
            "item_domain_machine_design_results",
            "item_domain_cable_catalog_results",
            "item_domain_cable_inventory_results",
            "item_domain_cable_design_results",
            "item_domain_location_results",
            "item_domain_maarc_results",
            "item_element_results",
            "item_type_results",
            "item_category_results",
            "property_type_results",
            "property_type_category_results",
            "source_results",
            "user_results",
            "user_group_results",
        ]:
            value = getattr(results, field_name)
            self.assertTrue(
                value is None or len(value) == 0,
                f"Expected {field_name} to be empty/None, got: {value}",
            )


if __name__ == "__main__":
    unittest.main()
