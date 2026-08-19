import datetime
import unittest
from types import SimpleNamespace

from bely_cli.tui import format as fmt


class FilterItemsTests(unittest.TestCase):
    def test_empty_query_returns_all(self):
        items = ["alpha", "beta", "gamma"]
        self.assertEqual(fmt.filter_items(items, "", lambda s: s), items)

    def test_case_insensitive_substring(self):
        items = ["Shift Report", "Beam Study", "RF trip"]
        result = fmt.filter_items(items, "beam", lambda s: s)
        self.assertEqual(result, ["Beam Study"])

    def test_substring_anywhere(self):
        items = ["abc", "xbcx", "zzz"]
        result = fmt.filter_items(items, "bc", lambda s: s)
        self.assertEqual(result, ["abc", "xbcx"])


class TypeRowTests(unittest.TestCase):
    def test_returns_name_display_description(self):
        t = SimpleNamespace(name="ops", display_name="Ops", description="Operations log")
        self.assertEqual(fmt.type_row(t), ("ops", "Ops", "Operations log"))

    def test_missing_fields_become_empty_strings(self):
        t = SimpleNamespace(name="ops", display_name=None, description=None)
        self.assertEqual(fmt.type_row(t), ("ops", "", ""))


class DocRowTests(unittest.TestCase):
    def test_returns_name_description_systems_owner_modified(self):
        more_info = SimpleNamespace(
            last_modified_on_date_time=datetime.datetime(2026, 6, 19, 14, 30),
            owner_username="alice",
        )
        d = SimpleNamespace(
            name="Shift Report", description="daily notes",
            item_type_list=[SimpleNamespace(name="SR"), SimpleNamespace(name="software")],
            more_info=more_info,
        )
        self.assertEqual(
            fmt.doc_row(d),
            ("Shift Report", "daily notes", "SR, software", "alice", "2026-06-19 14:30"),
        )

    def test_none_more_info_and_item_type_list_do_not_raise(self):
        d = SimpleNamespace(name=None, description=None, item_type_list=None, more_info=None)
        self.assertEqual(fmt.doc_row(d), ("(unnamed)", "", "", "", ""))


class RowColumnArityTests(unittest.TestCase):
    """Guards against a column being added to one side (row fn / COLUMNS) but not the other."""

    def test_type_row_matches_type_columns(self):
        t = SimpleNamespace(name="ops", display_name="Ops", description="Operations log")
        self.assertEqual(len(fmt.type_row(t)), len(fmt.TYPE_COLUMNS))

    def test_doc_row_matches_doc_columns(self):
        d = SimpleNamespace(name=None, description=None, item_type_list=None, more_info=None)
        self.assertEqual(len(fmt.doc_row(d)), len(fmt.DOC_COLUMNS))

    def test_entry_row_matches_entry_columns(self):
        e = SimpleNamespace(entered_on_date_time=None, entered_by_username=None, log_entry=None)
        self.assertEqual(len(fmt.entry_row(e)), len(fmt.ENTRY_COLUMNS))


class FilterItemsWithRowFnTests(unittest.TestCase):
    def test_matches_on_any_column(self):
        items = [
            SimpleNamespace(name="ops", display_name="Ops", description="Operations"),
            SimpleNamespace(name="controls", display_name="Controls", description="RF systems"),
        ]
        render = lambda it: " ".join(str(c) for c in fmt.type_row(it))
        result = fmt.filter_items(items, "rf", render)
        self.assertEqual([r.name for r in result], ["controls"])


class EntryRowTests(unittest.TestCase):
    def test_date_author_snippet(self):
        e = SimpleNamespace(
            entered_on_date_time=datetime.datetime(2026, 6, 19, 14, 30),
            entered_by_username="alice",
            log_entry="First line\nSecond line",
        )
        date, author, snippet = fmt.entry_row(e)
        self.assertEqual(date, "2026-06-19 14:30")
        self.assertEqual(author, "alice")
        self.assertEqual(snippet, "First line")

    def test_truncates_long_first_line(self):
        e = SimpleNamespace(
            entered_on_date_time=None,
            entered_by_username="bob",
            log_entry="x" * 100,
        )
        _, _, snippet = fmt.entry_row(e)
        self.assertIn("...", snippet)

    def test_skips_blank_leading_lines(self):
        e = SimpleNamespace(
            entered_on_date_time=None,
            entered_by_username="bob",
            log_entry="\n\n  \nReal content",
        )
        _, _, snippet = fmt.entry_row(e)
        self.assertEqual(snippet, "Real content")


class EntryReferenceTests(unittest.TestCase):
    def test_reference_fields(self):
        doc = SimpleNamespace(id=42, name="My Doc")
        entry = SimpleNamespace(log_id=99)
        self.assertEqual(
            fmt.entry_reference(doc, entry),
            {"doc_id": 42, "doc_name": "My Doc", "log_id": 99},
        )


class ReferenceCommandTests(unittest.TestCase):
    def test_uses_installed_command_name(self):
        cmd = fmt.reference_command(42, 99)
        self.assertEqual(cmd, "bely-cli entry get -d 42 --id 99")
        self.assertNotIn(".py", cmd)


class SummarizeReactionsTests(unittest.TestCase):
    def test_empty_or_none_returns_empty_string(self):
        self.assertEqual(fmt.summarize_reactions(None), "")
        self.assertEqual(fmt.summarize_reactions([]), "")

    def test_aggregates_by_emoji_preserving_first_seen_order(self):
        reactions = [
            SimpleNamespace(reaction=SimpleNamespace(emoji="👍", name="thumbsup")),
            SimpleNamespace(reaction=SimpleNamespace(emoji="🎉", name="tada")),
            SimpleNamespace(reaction=SimpleNamespace(emoji="👍", name="thumbsup")),
        ]
        self.assertEqual(fmt.summarize_reactions(reactions), "👍 2  🎉 1")

    def test_falls_back_to_name_when_no_emoji(self):
        reactions = [SimpleNamespace(reaction=SimpleNamespace(emoji=None, name="thumbsup"))]
        self.assertEqual(fmt.summarize_reactions(reactions), "thumbsup 1")


class EntryMetadataRowsTests(unittest.TestCase):
    def _entry(self, **overrides):
        base = dict(
            log_id=4821,
            entered_by_username="alice",
            entered_on_date_time=None,
            last_modified_by_username=None,
            last_modified_on_date_time=None,
            log_replies=None,
            log_reactions=None,
        )
        base.update(overrides)
        return SimpleNamespace(**base)

    def test_minimal_entry_has_log_id_and_doc(self):
        doc = SimpleNamespace(id=1, name="Ops")
        rows = fmt.entry_metadata_rows(self._entry(entered_by_username=None), doc)
        labels = [label for label, _ in rows]
        self.assertIn("log_id", labels)
        self.assertIn("doc", labels)
        self.assertNotIn("by", labels)
        self.assertNotIn("replies", labels)
        self.assertNotIn("reactions", labels)

    def test_replies_and_reactions_shown_when_present(self):
        doc = SimpleNamespace(id=1, name="Ops")
        entry = self._entry(
            log_replies=[SimpleNamespace(), SimpleNamespace()],
            log_reactions=[SimpleNamespace(reaction=SimpleNamespace(emoji="👍", name=None))],
        )
        rows = dict(fmt.entry_metadata_rows(entry, doc))
        self.assertEqual(rows["replies"], "2")
        self.assertEqual(rows["reactions"], "👍 1")


class DocMetadataRowsTests(unittest.TestCase):
    def test_more_info_none_does_not_raise(self):
        doc = SimpleNamespace(
            name="Ops Log", description=None, entity_type_list=None,
            item_type_list=None, more_info=None, log_lockout_hours=None,
        )
        rows = dict(fmt.doc_metadata_rows(doc))
        self.assertEqual(rows["name"], "Ops Log")
        self.assertNotIn("owner", rows)
        self.assertNotIn("created", rows)

    def test_empty_lists_are_omitted(self):
        doc = SimpleNamespace(
            name="Ops Log", description=None, entity_type_list=[],
            item_type_list=[], more_info=None, log_lockout_hours=None,
        )
        rows = dict(fmt.doc_metadata_rows(doc))
        self.assertNotIn("logbook types", rows)
        self.assertNotIn("systems", rows)

    def test_more_info_owner_and_lockout_surfaced(self):
        more_info = SimpleNamespace(
            owner_username="bob", created_by_username=None,
            created_on_date_time=None, last_modified_by_username=None,
            last_modified_on_date_time=None,
        )
        doc = SimpleNamespace(
            name="Ops Log", description="daily ops", entity_type_list=None,
            item_type_list=None, more_info=more_info, log_lockout_hours=24,
        )
        rows = dict(fmt.doc_metadata_rows(doc))
        self.assertEqual(rows["owner"], "bob")
        self.assertEqual(rows["lockout"], "24h")
        self.assertEqual(rows["description"], "daily ops")


class FormatAttachmentTests(unittest.TestCase):
    def test_includes_path_when_present(self):
        att = SimpleNamespace(original_filename="a.png", download_path="/x/a.png")
        self.assertEqual(fmt.format_attachment(att), "a.png  (/x/a.png)")

    def test_falls_back_to_unnamed(self):
        att = SimpleNamespace(original_filename=None, download_path=None)
        self.assertEqual(fmt.format_attachment(att), "(unnamed)")


if __name__ == "__main__":
    unittest.main()
