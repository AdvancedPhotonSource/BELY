import unittest
from belyApi import OpenApiException
from test.bely_test_base import BelyTestBase


class LogEntryFetchTests(BelyTestBase):

    def test_fetch_log_entry_with_dates(self):
        log_entries = self.logbook_api.get_log_entries(self.DOC_WITH_ENTRIES)
        log_entry = log_entries[0]

        self.assertIsNotNone(log_entry.entered_by_username)
        self.assertIsNotNone(log_entry.entered_on_date_time)
        self.assertIsNotNone(log_entry.last_modified_by_username)
        self.assertIsNotNone(log_entry.last_modified_on_date_time)

    def test_fetch_log_entry_without_replies_reactions(self):
        log_entries = self.logbook_api.get_log_entries(self.DOC_WITH_ENTRIES)
        log_entry = log_entries[0]

        self.assertIsNone(log_entry.log_replies)
        self.assertIsNone(log_entry.log_reactions)

    def test_fetch_log_entry_with_replies_reactions(self):
        log_entries = self.logbook_api.get_log_entries(
            self.DOC_WITH_ENTRIES, load_replies=True, load_reactions=True
        )

        self.__test_doc_with_entries_replies(log_entries=log_entries)
        self.__test_doc_with_entries_reactions(log_entries=log_entries)

    def test_fetch_log_entry_with_replies_no_reactions(self):
        log_entries = self.logbook_api.get_log_entries(
            self.DOC_WITH_ENTRIES, load_replies=True, load_reactions=False
        )

        log_entry = log_entries[0]
        log_reply = log_entry.log_replies[0]

        self.assertIsNone(log_entry.log_reactions)
        self.assertIsNone(log_reply.log_reactions)
        self.__test_doc_with_entries_replies(log_entries=log_entries)

    def test_fetch_log_entry_with_reactions_no_replies(self):
        log_entries = self.logbook_api.get_log_entries(
            self.DOC_WITH_ENTRIES, load_replies=False, load_reactions=True
        )

        self.__test_doc_with_entries_reactions(
            log_entries=log_entries, has_replies=False
        )

    def __test_doc_with_entries_replies(self, log_entries):
        # Ensure that everything is loaded as requested.
        log_entry = log_entries[0]
        self.assertIsNotNone(log_entry.log_replies)

        # Fetch replies defined in test db.
        log_reply_without_reaction = log_entry.log_replies[0]

        # Reply should not have another level of replies
        self.assertIsNone(log_reply_without_reaction.log_replies)

    def __test_doc_with_entries_reactions(self, log_entries, has_replies=True):
        # Ensure that everything is loaded as requested.
        log_entry = log_entries[0]
        self.assertIsNotNone(log_entry.log_reactions)

        # 5 reactions with first entry
        self.assertEqual(5, len(log_entry.log_reactions))

        if has_replies:
            # Fetch replies defined in test db.
            log_reply_without_reaction = log_entry.log_replies[0]
            log_reply_with_reaction = log_entry.log_replies[1]

            # Reactions should be loaded for all replies.
            self.assertIsNotNone(log_reply_without_reaction.log_reactions)
            self.assertIsNotNone(log_reply_with_reaction.log_reactions)

            # 1 Reaction with second log reply of first entry.
            self.assertEqual(1, len(log_reply_with_reaction.log_reactions))
        else:
            self.assertIsNone(log_entry.log_replies)


class LogEntryEditTests(BelyTestBase):
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

    def test_update_log_reply(self):
        self.login_as_user()

        log_entries = self.logbook_api.get_log_entries(
            self.DOC_WITH_ENTRIES, load_replies=True, load_reactions=False
        )

        # Given log entry text and test db reply
        log_entry_text = f"Reply-{self._gen_unique_name()}"
        log_entry = log_entries[0]
        log_reply = log_entry.log_replies[0]

        # Verify not yet equal to what it will be set to.
        self.assertNotEqual(log_entry_text, log_reply.log_entry)

        # Perform update
        log_reply.log_entry = log_entry_text
        result = self.logbook_api.add_update_log_entry(log_entry=log_reply)

        # Return should be equal.
        self.assertEqual(log_entry_text, result.log_entry)

        # Attempt to fetch fresh copy.
        log_entries = self.logbook_api.get_log_entries(
            self.DOC_WITH_ENTRIES, load_replies=True, load_reactions=False
        )
        log_entry = log_entries[0]
        log_reply = log_entry.log_replies[0]
        self.assertEqual(log_entry_text, log_reply.log_entry)


if __name__ == "__main__":
    unittest.main()
