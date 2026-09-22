import os
import unittest

from belyApi import LogDocumentOptions, OpenApiException
from test.bely_test_base import BelyTestBase

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TEST_IMAGE = os.path.join(TEST_DATA_DIR, "AnlLogo.png")


class AttachmentUploadTests(BelyTestBase):

    def _create_log_entry(self):
        """Log in as admin, create a log entry on DOC_SAMPLE_ID, return (doc_id, log_id)."""
        self.login_as_admin()
        entry_template = self.logbook_api.get_log_entry_template(self.DOC_SAMPLE_ID)
        entry_template.log_entry = "attachment test %s" % self._gen_unique_name()
        new_entry = self.logbook_api.add_update_log_entry(entry_template)
        return self.DOC_SAMPLE_ID, new_entry.log_id

    def test_upload_attachment_with_file_path(self):
        doc_id, log_id = self._create_log_entry()

        result = self.logbook_api.upload_attachment(
            log_document_id=doc_id,
            log_id=log_id,
            body=TEST_IMAGE,
            file_name="AnlLogo.png",
        )

        self.assertIsNotNone(result.id)
        self.assertIsNotNone(result.markdown_reference)
        self.assertIsNotNone(result.download_path)
        self.assertIsNotNone(result.original_filename)
        self.assertIsNotNone(result.stored_filename)
        self.assertEqual("AnlLogo.png", result.original_filename)

    def test_upload_attachment_with_bytes(self):
        doc_id, log_id = self._create_log_entry()

        with open(TEST_IMAGE, "rb") as f:
            file_bytes = f.read()

        result = self.logbook_api.upload_attachment(
            log_document_id=doc_id,
            log_id=log_id,
            body=file_bytes,
            file_name="AnlLogo.png",
        )

        self.assertIsNotNone(result.id)
        self.assertIsNotNone(result.markdown_reference)
        self.assertIsNotNone(result.download_path)
        self.assertIsNotNone(result.original_filename)
        self.assertIsNotNone(result.stored_filename)
        self.assertEqual("AnlLogo.png", result.original_filename)

    def test_upload_attachment_requires_auth(self):
        with self.assertRaises(OpenApiException):
            self.logbook_api.upload_attachment(
                log_document_id=self.DOC_SAMPLE_ID,
                log_id=1,
                body=b"dummy",
                file_name="test.txt",
            )

    def test_upload_attachment_requires_filename(self):
        doc_id, log_id = self._create_log_entry()

        with self.assertRaises(OpenApiException):
            self.logbook_api.upload_attachment(
                log_document_id=doc_id,
                log_id=log_id,
                body=b"dummy",
            )

    def test_get_log_entry_attachments(self):
        doc_id, log_id = self._create_log_entry()

        self.logbook_api.upload_attachment(
            log_document_id=doc_id,
            log_id=log_id,
            body=TEST_IMAGE,
            file_name="AnlLogo.png",
        )

        attachments = self.logbook_api.get_log_entry_attachments(
            log_document_id=doc_id,
            log_id=log_id,
        )

        filenames = [a.original_filename for a in attachments]
        self.assertIn("AnlLogo.png", filenames)
        self.assertTrue(all(attachment.id is not None for attachment in attachments))

    def test_download_attachment(self):
        doc_id, log_id = self._create_log_entry()

        with open(TEST_IMAGE, "rb") as f:
            original_bytes = f.read()

        result = self.logbook_api.upload_attachment(
            log_document_id=doc_id,
            log_id=log_id,
            body=original_bytes,
            file_name="AnlLogo.png",
        )

        download_api = self.factory.get_download_api()
        response = download_api.get_attachment_without_preload_content(
            result.stored_filename
        )
        downloaded_bytes = response.data

        self.assertEqual(original_bytes, downloaded_bytes)

    def test_upload_attachment_append_reference(self):
        doc_id, log_id = self._create_log_entry()

        result = self.logbook_api.upload_attachment(
            log_document_id=doc_id,
            log_id=log_id,
            body=TEST_IMAGE,
            file_name="AnlLogo.png",
            append_reference=True,
        )

        log_entries = self.logbook_api.get_log_entries(doc_id)
        entry = next(e for e in log_entries if e.log_id == log_id)

        self.assertIn(result.markdown_reference, entry.log_entry)


class AttachmentDeleteTests(BelyTestBase):

    def _create_document_entry_and_attachment(self, as_admin=False, append_reference=False):
        if as_admin:
            self.login_as_admin()
        else:
            self.login_as_user()
        options = LogDocumentOptions(
            name=f"Delete attachment {self._gen_unique_name()}",
            logbook_type_id=self.CTL_LOGBOOK_ID,
        )
        document = self.logbook_api.create_logbook_document(options)
        entry = self.logbook_api.get_log_entry_template(document.id)
        entry.log_entry = "attachment delete test"
        entry = self.logbook_api.add_update_log_entry(entry)
        attachment = self.logbook_api.upload_attachment(
            log_document_id=document.id,
            log_id=entry.log_id,
            body=TEST_IMAGE,
            file_name="AnlLogo.png",
            append_reference=append_reference,
        )
        return document, entry, attachment

    def test_delete_attachment(self):
        document, entry, attachment = self._create_document_entry_and_attachment(
            append_reference=True
        )

        result = self.logbook_api.delete_attachment(
            document.id, entry.log_id, attachment.id
        )

        self.assertIsNone(result)
        self.assertEqual(
            [], self.logbook_api.get_log_entry_attachments(document.id, entry.log_id)
        )
        updated_entry = self.logbook_api.get_log_entries(document.id)[0]
        self.assertIn(attachment.markdown_reference, updated_entry.log_entry)
        download_api = self.factory.get_download_api()
        with self.assertRaises(OpenApiException):
            download_api.get_attachment(attachment.stored_filename)
        for scaling in ("original", "scaled", "thumbnail"):
            with self.assertRaises(OpenApiException):
                download_api.get_attachment1(attachment.stored_filename, scaling)
        self.logbook_api.delete_log_document(document.id)

    def test_delete_attachment_requires_authentication(self):
        document, entry, attachment = self._create_document_entry_and_attachment()
        self.factory.logout_user()
        self.loggedIn = False

        with self.assertRaises(OpenApiException):
            self.logbook_api.delete_attachment(
                document.id, entry.log_id, attachment.id
            )

        self.login_as_user()
        self.logbook_api.delete_attachment(document.id, entry.log_id, attachment.id)
        self.logbook_api.delete_log_document(document.id)

    def test_delete_attachment_requires_permission(self):
        document, entry, attachment = self._create_document_entry_and_attachment(
            as_admin=True
        )

        self.login_as_user()
        with self.assertRaises(OpenApiException):
            self.logbook_api.delete_attachment(
                document.id, entry.log_id, attachment.id
            )

        self.login_as_admin()
        attachments = self.logbook_api.get_log_entry_attachments(
            document.id, entry.log_id
        )
        self.assertIn(attachment.id, [item.id for item in attachments])
        self.logbook_api.delete_attachment(document.id, entry.log_id, attachment.id)
        self.logbook_api.delete_log_document(document.id)

    def test_delete_attachment_rejects_mismatched_entry(self):
        document, entry, attachment = self._create_document_entry_and_attachment()
        other_entry = self.logbook_api.get_log_entry_template(document.id)
        other_entry.log_entry = "other entry"
        other_entry = self.logbook_api.add_update_log_entry(other_entry)

        with self.assertRaises(OpenApiException):
            self.logbook_api.delete_attachment(
                document.id, other_entry.log_id, attachment.id
            )

        attachments = self.logbook_api.get_log_entry_attachments(
            document.id, entry.log_id
        )
        self.assertIn(attachment.id, [item.id for item in attachments])
        self.logbook_api.delete_attachment(document.id, entry.log_id, attachment.id)
        self.logbook_api.delete_log_document(document.id)


if __name__ == "__main__":
    unittest.main()
