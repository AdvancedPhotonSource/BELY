"""LogbookData: API access + per-session caching for the TUI.

No textual import here either — this is the data layer, independently
testable with a hand-rolled FakeApi (see test/test_tui_data.py), the same
style used by test/test_commands.py and test/test_entry.py.

Caching rules (carried over from the original curses implementation):
  - Results are cached per parent id/key, including empty lists.
  - Failures are NOT cached, so a later visit retries the network call.
  - `is None` (not falsiness) distinguishes "not fetched yet" from a
    legitimately empty result.
"""


class LogbookData:
    """Wraps logbook_api with the caching the TUI needs."""

    def __init__(self, logbook_api):
        self._logbook_api = logbook_api

        self._types = None
        self._docs = {}          # type_id -> list of ItemDomainLogbook
        self._entries = {}       # doc_id -> list of LogEntry
        self._attachments = {}   # (doc_id, log_id) -> list of LogEntryAttachment

    def logbook_types(self):
        if self._types is None:
            self._types = self._logbook_api.get_logbook_types()
        return self._types

    def documents(self, type_id, limit):
        docs = self._docs.get(type_id)
        if docs is None:
            docs = self._logbook_api.get_log_documents(logbook_type_id=type_id, limit=limit)
            self._docs[type_id] = docs
        return docs

    def entries(self, doc_id):
        entries = self._entries.get(doc_id)
        if entries is None:
            entries = self._logbook_api.get_log_entries(
                log_document_id=doc_id, load_replies=True, load_reactions=True)
            self._entries[doc_id] = entries
        return entries

    def attachments(self, doc_id, log_id):
        key = (doc_id, log_id)
        attachments = self._attachments.get(key)
        if attachments is None:
            attachments = self._logbook_api.get_log_entry_attachments(
                log_document_id=doc_id, log_id=log_id)
            self._attachments[key] = attachments
        return attachments

    def invalidate(self, level, type_id=None, doc_id=None):
        """Drop the cache for one level so the next fetch hits the network.

        level: "types", "docs", or "entries". type_id/doc_id narrow the
        invalidation to a single key; omitted, the whole level is cleared.
        """
        if level == "types":
            self._types = None
        elif level == "docs":
            if type_id is None:
                self._docs.clear()
            else:
                self._docs.pop(type_id, None)
        elif level == "entries":
            if doc_id is None:
                self._entries.clear()
                self._attachments.clear()
            else:
                self._entries.pop(doc_id, None)
                for key in [k for k in self._attachments if k[0] == doc_id]:
                    del self._attachments[key]
        else:
            raise ValueError(f"unknown cache level: {level}")
