import importlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bely-cli"))

import config
import auth


class GetEditorTests(unittest.TestCase):
    def test_env_var_wins(self):
        with patch.dict(os.environ, {"EDITOR": "emacs"}), \
             patch.object(config, "get_setting", return_value="nano"):
            self.assertEqual(config.get_editor(), "emacs")

    def test_settings_used_when_no_env(self):
        with patch.dict(os.environ, {}, clear=False), \
             patch.object(config, "get_setting", return_value="nano"):
            os.environ.pop("EDITOR", None)
            self.assertEqual(config.get_editor(), "nano")

    def test_default_vi(self):
        with patch.dict(os.environ, {}, clear=False), \
             patch.object(config, "get_setting", return_value=None):
            os.environ.pop("EDITOR", None)
            self.assertEqual(config.get_editor(), "vi")


class GetTokenFileTests(unittest.TestCase):
    def test_default_is_sibling_of_settings(self):
        with patch.object(auth, "get_setting", return_value=None):
            self.assertEqual(
                auth.get_token_file(),
                os.path.join(config.CONFIG_DIR, "token"),
            )

    def test_settings_override_with_expansion(self):
        with patch.dict(os.environ, {"MYDIR": "/tmp/belytok"}), \
             patch.object(auth, "get_setting", return_value="$MYDIR/tok"):
            self.assertEqual(auth.get_token_file(), "/tmp/belytok/tok")

    def test_settings_override_with_tilde(self):
        with patch.object(auth, "get_setting", return_value="~/mytoken"):
            self.assertEqual(
                auth.get_token_file(),
                os.path.join(os.path.expanduser("~"), "mytoken"),
            )


class SettingOverridePathTests(unittest.TestCase):
    """Keys from setting_override_path are merged on top of base settings."""

    def _write(self, dir_, name, text):
        path = os.path.join(dir_, name)
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_override_merges_on_top_of_base(self):
        with tempfile.TemporaryDirectory() as d:
            override = self._write(d, "overrides.yaml", "user: alice\n")
            base = self._write(
                d, "settings.yaml",
                f"host: shared-host\nuser: bob\nsetting_override_path: {override}\n",
            )
            with patch.object(config, "SETTINGS_FILE", base):
                settings = config.load_settings()
        self.assertEqual(settings["host"], "shared-host")  # base kept
        self.assertEqual(settings["user"], "alice")        # overridden

    def test_missing_override_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            base = self._write(
                d, "settings.yaml",
                f"user: bob\nsetting_override_path: {d}/nope.yaml\n",
            )
            with patch.object(config, "SETTINGS_FILE", base):
                self.assertEqual(config.load_settings()["user"], "bob")

    def test_override_cannot_rechain(self):
        with tempfile.TemporaryDirectory() as d:
            override = self._write(
                d, "overrides.yaml",
                "user: alice\nsetting_override_path: /etc/evil.yaml\n",
            )
            base = self._write(
                d, "settings.yaml", f"setting_override_path: {override}\n",
            )
            with patch.object(config, "SETTINGS_FILE", base):
                settings = config.load_settings()
        self.assertEqual(settings["user"], "alice")
        # base's override path is preserved; the override file's is dropped.
        self.assertEqual(settings["setting_override_path"], override)

    def test_set_setting_does_not_bake_in_overrides(self):
        with tempfile.TemporaryDirectory() as d:
            override = self._write(d, "overrides.yaml", "user: alice\n")
            base = self._write(
                d, "settings.yaml",
                f"user: bob\nsetting_override_path: {override}\n",
            )
            with patch.object(config, "SETTINGS_FILE", base):
                config.set_setting("host", "new-host")
                raw_base = config._read_yaml(base)
        self.assertEqual(raw_base["host"], "new-host")
        self.assertEqual(raw_base["user"], "bob")  # not overwritten by override


class SettingsFileEnvTests(unittest.TestCase):
    def tearDown(self):
        # Reload back to defaults so other test modules see a clean config.
        os.environ.pop("BELY_SETTINGS_FILE", None)
        importlib.reload(config)
        importlib.reload(auth)

    def test_env_var_sets_settings_file_and_config_dir(self):
        with patch.dict(os.environ, {"BELY_SETTINGS_FILE": "/tmp/bely/custom.yaml"}):
            importlib.reload(config)
            importlib.reload(auth)
            self.assertEqual(config.SETTINGS_FILE, "/tmp/bely/custom.yaml")
            self.assertEqual(config.CONFIG_DIR, "/tmp/bely")
            with patch.object(auth, "get_setting", return_value=None):
                self.assertEqual(auth.get_token_file(), "/tmp/bely/token")


if __name__ == "__main__":
    unittest.main()
