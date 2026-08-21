import unittest
from unittest.mock import patch

from bely_cli import common


class OpenInEditorTests(unittest.TestCase):
    def test_shell_style_editor_command_is_split(self):
        with patch.object(common.config, "get_editor", return_value="code -w"), \
             patch.object(common.subprocess, "call") as call:
            common.open_in_editor("hello")
        argv = call.call_args.args[0]
        self.assertEqual(argv[:2], ["code", "-w"])

    def test_missing_editor_raises_runtime_error(self):
        with patch.object(common.config, "get_editor", return_value="not-a-real-editor"), \
             patch.object(common.subprocess, "call", side_effect=OSError("not found")):
            with self.assertRaises(RuntimeError):
                common.open_in_editor("hello")

    def test_returns_edited_file_contents(self):
        def fake_call(argv):
            path = argv[-1]
            with open(path, "w") as f:
                f.write("edited text")

        with patch.object(common.config, "get_editor", return_value="vi"), \
             patch.object(common.subprocess, "call", side_effect=fake_call):
            result = common.open_in_editor("original text")
        self.assertEqual(result, "edited text")


class EditorChangedTests(unittest.TestCase):
    def test_identical_text_is_unchanged(self):
        self.assertFalse(common.editor_changed("hello", "hello"))

    def test_trailing_newline_only_is_unchanged(self):
        self.assertFalse(common.editor_changed("hello", "hello\n"))
        self.assertFalse(common.editor_changed("hello\n", "hello"))

    def test_real_change_is_detected(self):
        self.assertTrue(common.editor_changed("hello", "hello world"))


if __name__ == "__main__":
    unittest.main()
