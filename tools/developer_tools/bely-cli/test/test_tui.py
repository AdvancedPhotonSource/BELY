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


class FlattenEntriesTests(unittest.TestCase):
    def _entry(self, log_id, replies=None):
        return SimpleNamespace(
            log_id=log_id, entered_on_date_time=None, entered_by_username=None,
            log_entry=f"entry {log_id}", log_replies=replies,
        )

    def test_flat_list_when_no_replies(self):
        entries = [self._entry(1), self._entry(2)]
        nodes = fmt.flatten_entries(entries)
        self.assertEqual([n.entry.log_id for n in nodes], [1, 2])
        self.assertTrue(all(n.depth == 0 for n in nodes))
        self.assertTrue(all(n.parent is None for n in nodes))
        self.assertTrue(all(n.reply_count == 0 for n in nodes))

    def test_none_and_empty_log_replies_are_no_replies(self):
        entries = [self._entry(1, replies=None), self._entry(2, replies=[])]
        nodes = fmt.flatten_entries(entries)
        self.assertEqual(len(nodes), 2)
        self.assertTrue(all(n.reply_count == 0 for n in nodes))

    def test_replies_are_depth_first_after_parent(self):
        r1, r2 = self._entry(11), self._entry(12)
        parent = self._entry(1, replies=[r1, r2])
        nodes = fmt.flatten_entries([parent, self._entry(2)])
        self.assertEqual([n.entry.log_id for n in nodes], [1, 11, 12, 2])
        self.assertEqual([n.depth for n in nodes], [0, 1, 1, 0])
        self.assertIs(nodes[1].parent, parent)
        self.assertIs(nodes[2].parent, parent)

    def test_collapsed_id_skips_its_replies(self):
        r1 = self._entry(11)
        parent = self._entry(1, replies=[r1])
        nodes = fmt.flatten_entries([parent], collapsed={1})
        self.assertEqual([n.entry.log_id for n in nodes], [1])
        self.assertFalse(nodes[0].expanded)

    def test_uncollapsed_parent_is_expanded(self):
        parent = self._entry(1, replies=[self._entry(11)])
        nodes = fmt.flatten_entries([parent], collapsed=set())
        self.assertTrue(nodes[0].expanded)

    def test_nested_replies_use_connectors_and_continuation_bars(self):
        grandchild_a, grandchild_b = self._entry(111), self._entry(112)
        child = self._entry(11, replies=[grandchild_a, grandchild_b])
        other_child = self._entry(12)
        parent = self._entry(1, replies=[child, other_child])
        nodes = fmt.flatten_entries([parent])
        by_id = {n.entry.log_id: n for n in nodes}
        self.assertEqual(by_id[11].branch, "  ├─ ")
        self.assertEqual(by_id[12].branch, "  └─ ")
        self.assertEqual(by_id[111].branch, "  │  ├─ ")
        self.assertEqual(by_id[112].branch, "  │  └─ ")


class EntryNodeRowTests(unittest.TestCase):
    def _node(self, log_id, depth=0, branch="", reply_count=0, expanded=True, parent=None):
        entry = SimpleNamespace(
            log_id=log_id, entered_on_date_time=None, entered_by_username="alice",
            log_entry="Reactor status nominal",
        )
        return fmt.EntryNode(
            entry=entry, depth=depth, parent=parent, branch=branch,
            reply_count=reply_count, expanded=expanded,
        )

    def test_top_level_no_replies_pads_to_align(self):
        _, _, cell = fmt.entry_node_row(self._node(1))
        self.assertEqual(cell, "  Reactor status nominal")

    def test_top_level_expanded_with_replies_shows_open_glyph(self):
        node = self._node(1, reply_count=2, expanded=True)
        _, _, cell = fmt.entry_node_row(node)
        self.assertEqual(cell, "▾ Reactor status nominal")

    def test_top_level_collapsed_shows_closed_glyph_and_count(self):
        node = self._node(1, reply_count=2, expanded=False)
        _, _, cell = fmt.entry_node_row(node)
        self.assertEqual(cell, "▸ Reactor status nominal  (2 replies)")

    def test_collapsed_singular_reply_count(self):
        node = self._node(1, reply_count=1, expanded=False)
        _, _, cell = fmt.entry_node_row(node)
        self.assertEqual(cell, "▸ Reactor status nominal  (1 reply)")

    def test_reply_row_uses_its_branch_prefix(self):
        node = self._node(11, depth=1, branch="  └─ ")
        _, _, cell = fmt.entry_node_row(node)
        self.assertEqual(cell, "  └─ Reactor status nominal")

    def test_row_arity_matches_entry_columns(self):
        self.assertEqual(len(fmt.entry_node_row(self._node(1))), len(fmt.ENTRY_COLUMNS))


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

    def test_parent_adds_reply_to_row_right_after_log_id(self):
        doc = SimpleNamespace(id=1, name="Ops")
        parent = SimpleNamespace(log_id=100)
        rows = fmt.entry_metadata_rows(self._entry(), doc, parent=parent)
        labels = [label for label, _ in rows]
        self.assertEqual(labels[0], "log_id")
        self.assertEqual(labels[1], "reply to")
        self.assertEqual(dict(rows)["reply to"], "100")

    def test_no_parent_omits_reply_to_row(self):
        doc = SimpleNamespace(id=1, name="Ops")
        rows = fmt.entry_metadata_rows(self._entry(), doc)
        self.assertNotIn("reply to", dict(rows))


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
