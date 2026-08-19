"""ConfigScreen: view and edit settings, mirroring `config show`/`config
set`/`config edit`.

A modal dialog opened from the command palette. Reading is unauthenticated
(core.collect_config() just reads settings.yaml + os.environ); only saving
touches disk.
"""

import asyncio
import subprocess

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from ... import config, core


class ConfigScreen(ModalScreen):
    DEFAULT_CSS = """
    ConfigScreen {
        align: center middle;
    }

    #config-dialog {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+e", "open_editor", "Edit file"),
        Binding("r", "reload", "Reload"),
    ]

    # Fields whose effective value can be overridden by an env var the CLI
    # also honors (see auth.py's precedence) -- token_path has none.
    ENV_FOR_FIELD = {"host": "BELY_HOST", "user": "BELY_USER", "editor": "EDITOR"}

    def compose(self) -> ComposeResult:
        with Vertical(id="config-dialog"):
            yield Static(id="config-breadcrumb")
            yield Static(id="config-summary")
            for field in config.VALID_FIELDS:
                yield Input(placeholder=field, id=f"config-{field}")
            yield Static(
                "[ctrl+s] save   [ctrl+e] edit file   [r] reload   [escape] back",
                id="config-hint",
            )

    def on_mount(self):
        self._load()

    def action_back(self):
        self.dismiss(None)

    def action_reload(self):
        self._load()

    def _load(self):
        data = core.collect_config()
        settings = data["settings"]
        env = data["environment"]

        self.query_one("#config-breadcrumb", Static).update(
            f"Configuration  -  {data['settings_file']}")

        lines = ["Settings:"]
        if settings:
            lines += [f"  {k} = {v}" for k, v in settings.items()]
        else:
            lines.append("  (no settings)")
        lines.append("")
        lines.append("Environment overrides:")
        if env:
            lines += [f"  {var} = {val}" for var, val in env.items()]
        else:
            lines.append("  (none set)")
        self.query_one("#config-summary", Static).update("\n".join(lines))

        for field in config.VALID_FIELDS:
            box = self.query_one(f"#config-{field}", Input)
            box.value = str(settings.get(field, "") or "")
            env_var = self.ENV_FOR_FIELD.get(field)
            box.placeholder = (
                f"{field} (overridden by {env_var})" if env_var and env_var in env else field
            )

    def action_save(self):
        self._save()

    @work
    async def _save(self):
        changed = []
        for field in config.VALID_FIELDS:
            value = self.query_one(f"#config-{field}", Input).value.strip()
            current = config.get_setting(field)
            if value and value != (current or ""):
                await asyncio.to_thread(config.set_setting, field, value)
                changed.append(field)

        if not changed:
            self.notify("No changes to save.")
        else:
            self.notify(f"Saved: {', '.join(changed)}")
            env = core.collect_config()["environment"]
            for field in changed:
                env_var = self.ENV_FOR_FIELD.get(field)
                if env_var and env_var in env:
                    self.notify(
                        f"{env_var} is set in the environment and will keep "
                        f"overriding the '{field}' setting.", severity="warning")

        self._load()

    def action_open_editor(self):
        self._open_editor()

    @work
    async def _open_editor(self):
        settings_file = await asyncio.to_thread(core.ensure_settings_file)
        editor = config.get_editor()
        with self.app.suspend():
            subprocess.call([editor, settings_file])
        self._load()
