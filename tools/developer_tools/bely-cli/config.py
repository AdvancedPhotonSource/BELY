import os
import yaml

CONFIG_DIR = os.path.expanduser("~/.config/bely")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.yaml")

VALID_FIELDS = ("host", "user")


def _ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, mode=0o700)


def load_settings():
    """Read settings.yaml and return as a dict (empty dict if missing)."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


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
    """Update a single setting and save."""
    data = load_settings()
    data[key] = value
    save_settings(data)
