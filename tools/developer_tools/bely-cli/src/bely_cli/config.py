import os
import yaml

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/bely")

VALID_FIELDS = ("host", "user", "editor", "token_path", "theme")


def expand_path(path):
    """Expand ~ and $VARS in a path string."""
    return os.path.expanduser(os.path.expandvars(path))


# The settings file location can be overridden with BELY_SETTINGS_FILE; the
# config dir (where the default token lives) follows the settings file.
_settings_env = os.environ.get("BELY_SETTINGS_FILE")
if _settings_env:
    SETTINGS_FILE = expand_path(_settings_env)
else:
    SETTINGS_FILE = os.path.join(DEFAULT_CONFIG_DIR, "settings.yaml")
CONFIG_DIR = os.path.dirname(SETTINGS_FILE)


def _ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, mode=0o700)


def _read_yaml(path):
    """Read a YAML file into a dict (empty dict if missing)."""
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def load_settings():
    """Read the settings file and return it as a dict (empty if missing).

    If the settings file defines ``setting_override_path``, keys from that
    file are merged on top of the base settings. This lets a user override
    individual values (e.g. ``user``) in a file they own, even when the main
    settings file lives in a shared, read-only location.
    """
    settings = _read_yaml(SETTINGS_FILE)
    override_path = settings.get("setting_override_path")
    if override_path:
        overrides = _read_yaml(expand_path(override_path))
        # The override file overrides values only; it cannot re-chain.
        overrides.pop("setting_override_path", None)
        settings.update(overrides)
    return settings


def save_settings(data):
    """Write a dict to settings.yaml, creating the config dir if needed."""
    _ensure_config_dir()
    with open(SETTINGS_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    os.chmod(SETTINGS_FILE, 0o600)


def get_setting(key):
    """Get a single setting value, or None if not set."""
    return load_settings().get(key)


def set_setting(key, value):
    """Update a single setting and save.

    Operates on the base settings file only (not merged override values), so
    overridden keys are never baked back into the base file.
    """
    data = _read_yaml(SETTINGS_FILE)
    data[key] = value
    save_settings(data)


def get_editor():
    """Return the editor: EDITOR env var, then 'editor' setting, then 'vi'."""
    return os.environ.get("EDITOR") or get_setting("editor") or "vi"
