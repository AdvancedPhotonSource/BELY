"""CLI alias registration and help behavior."""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from bely_cli.cli import cli


class CliAliasTests(unittest.TestCase):
    ALIASES = {
        "doc": {"ls": "list", "add": "new"},
        "entry": {"ls": "list", "show": "get", "edit": "update"},
        "config": {"ls": "show"},
    }

    def test_aliases_reuse_canonical_commands(self):
        for group_name, aliases in self.ALIASES.items():
            commands = cli.commands[group_name].commands
            for alias, canonical in aliases.items():
                with self.subTest(group=group_name, alias=alias):
                    self.assertIs(commands[alias], commands[canonical])

    def test_alias_help_matches_canonical_help(self):
        runner = CliRunner()
        for group_name, aliases in self.ALIASES.items():
            for alias, canonical in aliases.items():
                with self.subTest(group=group_name, alias=alias):
                    alias_result = runner.invoke(cli, [group_name, alias, "--help"])
                    canonical_result = runner.invoke(cli, [group_name, canonical, "--help"])
                    self.assertEqual(alias_result.exit_code, 0)
                    self.assertEqual(canonical_result.exit_code, 0)
                    self.assertEqual(
                        alias_result.output.replace(f" {alias} ", f" {canonical} ", 1),
                        canonical_result.output,
                    )

    def test_group_help_combines_aliases(self):
        runner = CliRunner()
        expected = {
            "doc": ("add, new", "list, ls"),
            "entry": ("edit, update", "get, show", "list, ls"),
            "config": ("ls, show",),
        }
        for group_name, labels in expected.items():
            with self.subTest(group=group_name):
                result = runner.invoke(cli, [group_name, "--help"])
                self.assertEqual(result.exit_code, 0)
                for label in labels:
                    self.assertIn(label, result.output)

    def test_alias_invokes_same_handler(self):
        runner = CliRunner()
        with patch("bely_cli.cli.cmd_list_docs") as command:
            result = runner.invoke(cli, ["doc", "ls", "--limit", "3", "--format", "json"])
        self.assertEqual(result.exit_code, 0)
        command.assert_called_once_with(fmt="json", limit=3)

    def test_reply_invokes_handler(self):
        runner = CliRunner()
        with patch("bely_cli.cli.cmd_reply_entry") as command:
            result = runner.invoke(cli, [
                "entry", "reply", "--doc-id", "99", "--id", "42",
                "--text", "Reply text", "--format", "json",
            ])
        self.assertEqual(result.exit_code, 0)
        command.assert_called_once_with(
            fmt="json", doc_id=99, doc_name=None, entry_id=42,
            file=None, text="Reply text", add_attachment=None,
        )
