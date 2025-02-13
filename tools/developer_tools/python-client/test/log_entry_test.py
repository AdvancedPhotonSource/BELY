from tkinter.messagebox import NO
import unittest
from belyApi import OpenApiException
from test.bely_test_base import BelyTestBase


class LogEntryTests(BelyTestBase):
    def test_add_log_entry_to_sample_log_document(self):
        self.login_as_user()
        with self.assertRaises(OpenApiException):
            self.logbook_api.get_log_entry_template(self.DOC_SAMPLE_ID)

        self.login_as_admin()
        entry_template = self.logbook_api.get_log_entry_template(self.DOC_SAMPLE_ID)

        entries = self.logbook_api.get_log_entries(self.DOC_SAMPLE_ID)

        log_entry_text = "sample entry text %s" % self._gen_unique_name()
        entry_template.log_entry = log_entry_text

        new_entry = self.logbook_api.add_update_log_entry(entry_template)

        new_entries = self.logbook_api.get_log_entries(self.DOC_SAMPLE_ID)

        self.assertEqual(len(entries) + 1, len(new_entries))

        last_entry = new_entries[-1]
        self.assertEqual(new_entry.log_id, last_entry.log_id)
        self.assertEqual(new_entry.log_entry, log_entry_text)


if __name__ == "__main__":
    unittest.main()
