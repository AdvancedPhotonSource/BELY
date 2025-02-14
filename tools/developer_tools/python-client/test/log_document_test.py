from tkinter.messagebox import NO
import unittest

from BelyApiFactory import BelyApiFactory
from belyApi import LogDocumentOptions, OpenApiException
from test.bely_test_base import BelyTestBase


class LogDocumentFetchTests(BelyTestBase):

    def test_fetch_logbooks(self):
        logbooks = self.logbook_api.get_logbook_types()

        self.assertEqual(len(logbooks), 13)

    def test_fetch_lobook_systems(self):
        systems = self.logbook_api.get_logbook_systems()

        self.assertEqual(len(systems), 12)

    def test_fetch_logbook_templates(self):
        templates = self.logbook_api.get_logbook_templates()

        self.assertEqual(len(templates), 3)

    def test_fetch_logbook_documents(self):
        documents = self.logbook_api.get_log_documents(self.OPS_LOGBOOK_ID, limit=100)

        self.assertEqual(len(documents), 75)

    def test_fetch_logbook_document_with_more_info(self):
        documents = self.logbook_api.get_log_documents(self.OPS_LOGBOOK_ID, limit=1)

        document = documents[0]
        more_info = document.more_info

        self.assertIsNotNone(more_info)
        self.assertIsNotNone(more_info.created_by_username)
        self.assertIsNotNone(more_info.created_on_date_time)
        self.assertIsNotNone(more_info.last_modified_by_username)
        self.assertIsNotNone(more_info.last_modified_on_date_time)


class LogDocumentEditTests(BelyTestBase):

    def test_create_logbook_document(self):
        doc_name = self._gen_unique_name() + "Basic"
        options = LogDocumentOptions(name=doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)

        # Create log document without logging in.
        with self.assertRaises(OpenApiException):
            self.logbook_api.create_logbook_document(log_document_options=options)

        self.login_as_user()

        existing_logbooks = self.logbook_api.get_log_documents(
            self.CTL_LOGBOOK_ID, limit=1000
        )

        new_log_document = self.logbook_api.create_logbook_document(
            log_document_options=options
        )
        self.assertIsNotNone(new_log_document.id)

        with self.assertRaises(
            OpenApiException, msg="Not failed creating a same document twice."
        ):
            self.logbook_api.create_logbook_document(log_document_options=options)

        new_logbooks = self.logbook_api.get_log_documents(
            self.CTL_LOGBOOK_ID, limit=1000
        )

        self.assertEqual(len(existing_logbooks) + 1, len(new_logbooks))

        # TODO Add get log document by id and test

    def test_create_logbook_document_per_entry_template(self):
        doc_name = self._gen_unique_name() + " Entry Per Template"
        options = LogDocumentOptions(name=doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)
        options.template_id = self.DOC_TEMPLATE_PER_ENTRY_ID

        template_entries = self.logbook_api.get_log_entries(
            self.DOC_TEMPLATE_PER_ENTRY_ID
        )

        self.assertEqual(len(template_entries), 1)

        expected_text = template_entries[0].log_entry

        self.login_as_user()
        new_log_document = self.logbook_api.create_logbook_document(
            log_document_options=options
        )
        entry_template = self.logbook_api.get_log_entry_template(new_log_document.id)

        self.assertEqual(
            entry_template.log_entry, expected_text, msg="Entry not fetched as expected"
        )

        entry_template.log_entry += "\n\n" + doc_name
        new_entry = self.logbook_api.add_update_log_entry(entry_template)

        self.assertEqual(
            entry_template.log_entry,
            new_entry.log_entry,
            msg="new entry not matching added entry",
        )

    def test_create_logbook_document_from_non_template_id(self):
        doc_name = self._gen_unique_name() + " From non-template"
        options = LogDocumentOptions(name=doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)
        options.template_id = self.TEST_DOCUMENT_ID

        self.login_as_user()

        with self.assertRaises(
            OpenApiException, msg="Was able to create log document from non-template"
        ):
            self.logbook_api.create_logbook_document(log_document_options=options)

    def __verify_log_entry_copy(self, template_id, new_doc_id):
        template_log_entries = self.logbook_api.get_log_entries(template_id)
        entries_in_new_document = self.logbook_api.get_log_entries(new_doc_id)

        # Verify same amount of test log entries.
        self.assertEqual(len(template_log_entries), len(entries_in_new_document))

        # Verify content of log entries.
        for i, template_entry in enumerate(template_log_entries):
            document_entry = entries_in_new_document[i]

            self.assertEqual(template_entry.log_entry, document_entry.log_entry)

    def test_create_from_template_with_copy(self):
        doc_name = self._gen_unique_name() + " Copy Template"

        options = LogDocumentOptions(name=doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)
        options.template_id = self.DOC_TEMPLATE_COPY_ID

        self.login_as_user()
        new_log_document = self.logbook_api.create_logbook_document(
            log_document_options=options
        )

        self.__verify_log_entry_copy(self.DOC_TEMPLATE_COPY_ID, new_log_document.id)

    # Verify creation of sections.
    def test_create_from_template_with_sections_copy(self):
        doc_name = self._gen_unique_name() + " Section Copy Template"

        options = LogDocumentOptions(name=doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)
        options.template_id = self.DOC_TEMPLATE_SECTIONS_COPY_ID

        self.login_as_user()
        new_log_document = self.logbook_api.create_logbook_document(
            log_document_options=options
        )

        template_sections = self.logbook_api.get_logbook_sections(
            self.DOC_TEMPLATE_SECTIONS_COPY_ID
        )
        new_log_document_sections = self.logbook_api.get_logbook_sections(
            new_log_document.id
        )

        self.assertEqual(len(template_sections), len(new_log_document_sections))

        for i, template_section in enumerate(template_sections):
            new_doc_section = new_log_document_sections[i]
            self.__verify_log_entry_copy(template_section.id, new_doc_section.id)

    def test_no_template_per_entry(self):
        doc_name = self._gen_unique_name() + " No template per entry test"

        options = LogDocumentOptions(name=doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)
        options.template_id = self.DOC_TEMPLATE_COPY_ID

        self.login_as_user()
        new_log_document = self.logbook_api.create_logbook_document(
            log_document_options=options
        )

        entry_template = self.logbook_api.get_log_entry_template(new_log_document.id)

        self.assertEqual(0, len(entry_template.log_entry))

        new_entry_text = "TEST Text"
        entry_template.log_entry += new_entry_text
        new_entry = self.logbook_api.add_update_log_entry(entry_template)
        self.assertEqual(new_entry.log_entry, new_entry_text)

    def test_create_log_document_with_sections(self):
        doc_name = self._gen_unique_name() + " New doc with sections."

        self.login_as_user()

        options = LogDocumentOptions(doc_name, logbook_type_id=self.CTL_LOGBOOK_ID)

        new_doc = self.logbook_api.create_logbook_document(options)

        sample_sections = ["section 1", "section 2", "section 3", "section 4"]

        for section in sample_sections:
            self.logbook_api.create_log_document_section(new_doc.id, section)

        # Should not allow duplicate name
        with self.assertRaises(OpenApiException):
            self.logbook_api.create_log_document_section(new_doc.id, sample_sections[0])

        added_sections = self.logbook_api.get_logbook_sections(
            log_document_id=new_doc.id
        )

        for i, section in enumerate(added_sections):
            self.assertEqual(sample_sections[i], section.name)


if __name__ == "__main__":
    unittest.main()
