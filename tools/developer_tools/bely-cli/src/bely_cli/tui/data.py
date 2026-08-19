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

from .. import core


class LogbookData:
    """Wraps logbook_api with the caching the TUI needs."""

    def __init__(self, logbook_api):
        self._logbook_api = logbook_api

        self._types = None
        self._systems = None
        self._templates = None
        self._docs = {}          # type_id -> list of ItemDomainLogbook
        self._entries = {}       # doc_id -> list of LogEntry
        self._attachments = {}   # (doc_id, log_id) -> list of LogEntryAttachment
        self._recent = {}        # username -> list of recent documents

    def logbook_types(self):
        if self._types is None:
            self._types = self._logbook_api.get_logbook_types()
        return self._types

    def logbook_systems(self):
        if self._systems is None:
            self._systems = self._logbook_api.get_logbook_systems()
        return self._systems

    def logbook_templates(self):
        if self._templates is None:
            self._templates = self._logbook_api.get_logbook_templates()
        return self._templates

    def recent_documents(self, factory, username, limit):
        """The user's recently modified documents (see core.recent_documents).

        Cached per username; `factory` is only needed to actually fetch (it
        isn't part of the cache key -- a session has exactly one factory).
        """
        docs = self._recent.get(username)
        if docs is None:
            docs = core.recent_documents(factory, username, limit)
            self._recent[username] = docs
        return docs

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

    def invalidate(self, level, type_id=None, doc_id=None, username=None):
        """Drop the cache for one level so the next fetch hits the network.

        level: "types", "systems", "templates", "docs", "entries", or
        "recent". type_id/doc_id/username narrow the invalidation to a
        single key; omitted, the whole level is cleared.
        """
        if level == "types":
            self._types = None
        elif level == "systems":
            self._systems = None
        elif level == "templates":
            self._templates = None
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
        elif level == "recent":
            if username is None:
                self._recent.clear()
            else:
                self._recent.pop(username, None)
        else:
            raise ValueError(f"unknown cache level: {level}")

    def clear(self):
        """Discard every cache, forcing the next fetch at any level to hit the network."""
        self._types = None
        self._systems = None
        self._templates = None
        self._docs.clear()
        self._entries.clear()
        self._attachments.clear()
        self._recent.clear()
