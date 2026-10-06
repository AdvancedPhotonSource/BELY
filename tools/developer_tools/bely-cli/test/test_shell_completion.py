import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from bely_cli.cli import cli
from bely_cli import shell_completion as completion


class CacheTests(unittest.TestCase):
    def test_cache_is_atomic_host_scoped_and_expires(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(completion.config, "CONFIG_DIR", directory):
            first = completion.write_cache("https://one", {"types": []}, now=100)
            completion.write_cache("https://two", {"types": []}, now=200)
            self.assertNotEqual(completion.cache_path("https://one"), completion.cache_path("https://two"))
            self.assertEqual(completion.load_cache("https://one"), first)
            self.assertTrue(completion.cache_is_fresh(first, now=100 + completion.CACHE_TTL_SECONDS - 1))
            self.assertFalse(completion.cache_is_fresh(first, now=100 + completion.CACHE_TTL_SECONDS))
            self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(completion.cache_dir())))

    def test_created_and_deleted_documents_update_existing_host_cache(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(completion.config, "CONFIG_DIR", directory), \
             patch.object(completion.auth, "get_host", return_value="https://one"):
            completion.write_cache("https://one", {
                "types": [], "systems": [], "templates": [],
                "documents": [{"id": 1, "name": "Old", "type": "Ops"}],
            }, now=100)
            created = SimpleNamespace(id=2, name="New", logbook_type=None)

            self.assertTrue(completion.add_cached_document(created, "ops"))
            data = completion.load_cache("https://one")
            self.assertEqual([item["id"] for item in data["documents"]], [2, 1])
            self.assertEqual(data["documents"][0]["type"], "ops")
            self.assertEqual(data["refreshed_at"], 100)

            self.assertTrue(completion.remove_cached_document(1))
            self.assertEqual(
                [item["id"] for item in completion.load_cache("https://one")["documents"]],
                [2],
            )

    def test_mutations_do_not_create_a_cache_or_affect_another_host(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(completion.config, "CONFIG_DIR", directory):
            completion.write_cache("https://one", {"documents": [{"id": 1}]})
            with patch.object(completion.auth, "get_host", return_value="https://two"):
                self.assertFalse(completion.add_cached_document(SimpleNamespace(id=2, name="New")))
                self.assertFalse(completion.remove_cached_document(1))
            self.assertEqual(completion.load_cache("https://one")["documents"], [{"id": 1}])

    def test_invalid_cache_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(completion.config, "CONFIG_DIR", directory):
            os.makedirs(completion.cache_dir())
            with open(completion.cache_path("host"), "w") as cache_file:
                cache_file.write("not json")
            self.assertIsNone(completion.load_cache("host"))

    def test_stale_cache_starts_refresh_and_returns_values(self):
        stale = {"refreshed_at": 0, "types": [{"name": "ops"}]}
        with patch.object(completion.auth, "get_host", return_value="host"), \
             patch.object(completion, "load_cache", return_value=stale), \
             patch.object(completion, "start_background_refresh") as refresh:
            self.assertEqual(completion.cached_values_for_completion(), stale)
        refresh.assert_called_once_with("host")

    def test_completion_never_fetches_or_prompts(self):
        with patch.object(completion.auth, "get_host", side_effect=ValueError("missing")), \
             patch.object(completion, "refresh_cache") as refresh:
            self.assertEqual(completion.cached_values_for_completion(), {})
        refresh.assert_not_called()

    def test_refresh_lock_allows_only_one_process(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(completion.config, "CONFIG_DIR", directory):
            fd = completion.acquire_refresh_lock("host")
            self.assertIsNotNone(fd)
            self.assertIsNone(completion.acquire_refresh_lock("host"))
            completion.release_refresh_lock("host", fd)


class FetchTests(unittest.TestCase):
    def test_fetches_100_per_type_and_deduplicates_documents(self):
        api = MagicMock()
        api.get_logbook_types.return_value = [
            SimpleNamespace(id=1, name="ops", display_name="Ops", description="Operations"),
            SimpleNamespace(id=2, name="all", display_name="All", description=""),
        ]
        api.get_logbook_systems.return_value = [SimpleNamespace(name="SR", description="Ring")]
        api.get_logbook_templates.return_value = [SimpleNamespace(name="Shift", description="")]
        doc = SimpleNamespace(id=7, name="Shift Log", logbook_type="Ops")
        api.get_log_documents.side_effect = [[doc], [doc]]
        factory = MagicMock()
        factory.get_logbook_api.return_value = api

        values = completion.fetch_completion_values(factory)

        self.assertEqual(len(values["documents"]), 1)
        self.assertEqual(api.get_log_documents.call_count, 2)
        for call in api.get_log_documents.call_args_list:
            self.assertEqual(call.kwargs["limit"], 100)


class CompletionTests(unittest.TestCase):
    VALUES = {
        "types": [{"name": "ops", "description": "Operations"}],
        "systems": [{"name": "SR", "description": "Ring"}, {"name": "software", "description": ""}],
        "templates": [{"name": "Shift", "description": "Report"}],
        "documents": [{"id": 42, "name": "Shift Log", "type": "Ops"}],
    }

    def test_dynamic_completers(self):
        with patch.object(completion, "cached_values_for_completion", return_value=self.VALUES):
            self.assertEqual(completion.complete_types(None, None, "o")[0].value, "ops")
            self.assertEqual(completion.complete_templates(None, None, "S")[0].help, "Report")
            self.assertEqual(completion.complete_systems(None, None, "SR,so")[0].value, "SR,software")
            self.assertEqual(completion.complete_document_names(None, None, "Sh")[0].help, "Ops")
            self.assertEqual(completion.complete_document_ids(None, None, "4")[0].help, "Shift Log")

    def test_click_completion_lists_commands_aliases_and_options(self):
        runner = CliRunner()
        env = {"COMP_WORDS": "bely-cli d", "COMP_CWORD": "1"}
        result = runner.invoke(cli, [], prog_name="bely-cli",
                               env={**env, "_BELY_CLI_COMPLETE": "bash_complete"})
        self.assertEqual(result.exit_code, 0)
        self.assertIn("doc", result.output)

        env = {"COMP_WORDS": "bely-cli doc l", "COMP_CWORD": "2"}
        result = runner.invoke(cli, [], prog_name="bely-cli",
                               env={**env, "_BELY_CLI_COMPLETE": "bash_complete"})
        self.assertIn("list", result.output)
        self.assertIn("ls", result.output)

    def test_entry_ids_are_fetched_for_selected_document_without_cache(self):
        api = MagicMock()
        api.get_log_entries.return_value = [
            SimpleNamespace(
                log_id=42,
                log_entry="Main entry\nMore",
                log_replies=[SimpleNamespace(log_id=43, log_entry="Reply", log_replies=[])],
            )
        ]
        factory = MagicMock()
        factory.get_logbook_api.return_value = api
        ctx = SimpleNamespace(params={"doc_id": 206})

        with patch.object(completion.auth, "get_factory", return_value=factory), \
             patch.object(completion, "cached_values_for_completion") as cached:
            items = completion.complete_entry_ids(ctx, None, "4")

        self.assertEqual([item.value for item in items], ["42", "43"])
        self.assertEqual(items[0].help, "Main entry")
        api.get_log_entries.assert_called_once_with(log_document_id=206, load_replies=True)
        cached.assert_not_called()

    def test_entry_ids_resolve_selected_document_name(self):
        api = MagicMock()
        api.get_log_document_by_name.return_value = SimpleNamespace(id=206)
        api.get_log_entries.return_value = [
            SimpleNamespace(log_id=42, log_entry="Entry", log_replies=[]),
        ]
        factory = MagicMock()
        factory.get_logbook_api.return_value = api

        with patch.object(completion.auth, "get_factory", return_value=factory):
            items = completion.complete_entry_ids(
                SimpleNamespace(params={"doc_name": "New doc"}), None, "4")

        self.assertEqual([item.value for item in items], ["42"])
        api.get_log_document_by_name.assert_called_once_with(name="New doc")
        api.get_log_entries.assert_called_once_with(log_document_id=206, load_replies=True)

    def test_entry_ids_require_document(self):
        with patch.object(completion.auth, "get_factory") as factory:
            self.assertEqual(
                completion.complete_entry_ids(SimpleNamespace(params={}), None, ""), [])
        factory.assert_not_called()

    def test_entry_id_completion_failure_is_silent(self):
        ctx = SimpleNamespace(params={"doc_id": 206})
        with patch.object(completion.auth, "get_factory", side_effect=RuntimeError("offline")):
            self.assertEqual(completion.complete_entry_ids(ctx, None, ""), [])

    def test_entry_routes_use_dynamic_entry_id_completion(self):
        entry_commands = cli.commands["entry"].commands
        commands = [
            entry_commands["get"],
            entry_commands["update"],
            entry_commands["delete"],
            entry_commands["attachment"].commands["add"],
            entry_commands["attachment"].commands["list"],
            entry_commands["attachment"].commands["delete"],
        ]
        for command in commands:
            with self.subTest(command=command.name):
                options = {parameter.name: parameter for parameter in command.params}
                self.assertIs(
                    options["entry_id"]._custom_shell_complete,
                    completion.complete_entry_ids,
                )

    def test_path_options_expose_file_completion(self):
        command = cli.commands["entry"].commands["add"]
        options = {parameter.name: parameter for parameter in command.params}
        items = options["file"].shell_complete(None, "")
        self.assertTrue(items)
        self.assertEqual(items[0].type, "file")


class InitTests(unittest.TestCase):
    def test_detects_shell(self):
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            self.assertEqual(completion.detect_shell(), "zsh")

    def test_install_is_idempotent_and_preserves_other_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, ".bashrc")
            with open(path, "w") as rc_file:
                rc_file.write("export KEEP=yes\n")
            completion.install_completion("bash", path)
            completion.install_completion("bash", path)
            with open(path) as rc_file:
                content = rc_file.read()
        self.assertIn("export KEEP=yes", content)
        self.assertEqual(content.count(completion.BLOCK_START), 1)
        self.assertIn("bash_source", content)

    def test_init_print_does_not_write(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, ".bashrc")
            with patch.object(completion, "rc_path", return_value=path):
                result = runner.invoke(cli, ["shell", "init", "--shell", "bash", "--print"])
            self.assertEqual(result.exit_code, 0)
            self.assertFalse(os.path.exists(path))
            self.assertIn(completion.BLOCK_START, result.output)


if __name__ == "__main__":
    unittest.main()
