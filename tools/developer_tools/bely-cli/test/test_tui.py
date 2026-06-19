import datetime
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bely-cli"))

import tui


class FilterItemsTests(unittest.TestCase):
    def test_empty_query_returns_all(self):
        items = ["alpha", "beta", "gamma"]
        self.assertEqual(tui.filter_items(items, "", lambda s: s), items)

    def test_case_insensitive_substring(self):
        items = ["Shift Report", "Beam Study", "RF trip"]
        result = tui.filter_items(items, "beam", lambda s: s)
        self.assertEqual(result, ["Beam Study"])

    def test_substring_anywhere(self):
        items = ["abc", "xbcx", "zzz"]
        result = tui.filter_items(items, "bc", lambda s: s)
        self.assertEqual(result, ["abc", "xbcx"])


class FormatEntryTests(unittest.TestCase):
    def test_date_author_snippet(self):
        e = SimpleNamespace(
            entered_on_date_time=datetime.datetime(2026, 6, 19, 14, 30),
            entered_by_username="alice",
            log_entry="First line\nSecond line",
        )
        out = tui.format_entry(e)
        self.assertIn("2026-06-19 14:30", out)
        self.assertIn("alice", out)
        self.assertIn("First line", out)
        self.assertNotIn("Second line", out)

    def test_truncates_long_first_line(self):
        e = SimpleNamespace(
            entered_on_date_time=None,
            entered_by_username="bob",
            log_entry="x" * 100,
        )
        out = tui.format_entry(e)
        self.assertIn("...", out)

    def test_skips_blank_leading_lines(self):
        e = SimpleNamespace(
            entered_on_date_time=None,
            entered_by_username="bob",
            log_entry="\n\n  \nReal content",
        )
        self.assertIn("Real content", tui.format_entry(e))


class StepIndexTests(unittest.TestCase):
    def test_middle_moves(self):
        self.assertEqual(tui.step_index(3, +1, 10), 4)
        self.assertEqual(tui.step_index(3, -1, 10), 2)

    def test_clamp_low(self):
        self.assertEqual(tui.step_index(0, -1, 10), 0)

    def test_clamp_high(self):
        self.assertEqual(tui.step_index(9, +1, 10), 9)

    def test_empty_list(self):
        self.assertEqual(tui.step_index(0, +1, 0), 0)


class EntryReferenceTests(unittest.TestCase):
    def test_reference_fields(self):
        doc = SimpleNamespace(id=42, name="My Doc")
        entry = SimpleNamespace(log_id=99)
        self.assertEqual(
            tui.entry_reference(doc, entry),
            {"doc_id": 42, "doc_name": "My Doc", "log_id": 99},
        )


if __name__ == "__main__":
    unittest.main()
