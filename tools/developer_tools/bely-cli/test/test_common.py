import unittest
from unittest.mock import patch

from bely_cli import common


class FormatErrorMessageTests(unittest.TestCase):
    def test_non_api_error_uses_exception_text(self):
        self.assertEqual(common.format_error_message(ValueError("concise")), "concise")

    def test_api_error_uses_factory_parser_message(self):
        import belyApi

        error = belyApi.exceptions.ApiException(status=400, body="long response")
        factory = unittest.mock.Mock()
        factory.parse_api_exception.return_value.message = "short message"
        self.assertEqual(common.format_error_message(error, factory), "short message")
        factory.parse_api_exception.assert_called_once_with(error)

    def test_parser_failure_falls_back_to_exception_text(self):
        import belyApi

        error = belyApi.exceptions.ApiException(status=400, body="response")
        factory = unittest.mock.Mock()
        factory.parse_api_exception.side_effect = ValueError("bad response")
        self.assertEqual(common.format_error_message(error, factory), str(error))


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
