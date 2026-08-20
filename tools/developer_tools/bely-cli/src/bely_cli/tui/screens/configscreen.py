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
from textual.widgets import Button, Input, Select, Static

from ... import config, core
from ..images import IMAGE_MODE_HELP, IMAGE_MODES
from .dialog import CANCEL_HINT, SAVE_HINT, DialogButtons, DialogScreen, hinted_label


class ConfigScreen(DialogScreen):
    DEFAULT_CSS = """
    #config-dialog {
        width: 70;
    }
    """

    BINDINGS = [Binding("ctrl+s", "submit", "Save", show=False)]

    BUTTON_ROWS = [["config-save", "config-edit", "config-reload", "config-close"]]

    # Fields whose effective value can be overridden by an env var the CLI
    # also honors (see auth.py's precedence) -- token_path has none.
    ENV_FOR_FIELD = {"host": "BELY_HOST", "user": "BELY_USER", "editor": "EDITOR"}

    FIELD_CHOICES = {"images": IMAGE_MODES}  # enum fields get a Select instead of an Input
    FIELD_DEFAULTS = {"images": "auto"}

    def compose(self) -> ComposeResult:
        with Vertical(id="config-dialog", classes="dialog"):
            yield Static(id="config-breadcrumb")
            yield Static(id="config-summary")
            for field in config.VALID_FIELDS:
                choices = self.FIELD_CHOICES.get(field)
                if choices:
                    yield Select(
                        [(f"{choice} — {IMAGE_MODE_HELP[choice]}", choice)
                         for choice in choices],
                        allow_blank=False, id=f"config-{field}",
                    )
                else:
                    yield Input(placeholder=field, id=f"config-{field}")
            with DialogButtons():
                yield Button(hinted_label("Save", SAVE_HINT), variant="primary", id="config-save")
                yield Button(hinted_label("Edit file"), id="config-edit")
                yield Button(hinted_label("Reload"), id="config-reload")
                yield Button(hinted_label("Close", CANCEL_HINT), id="config-close")

    def on_mount(self):
        self._load()
        self.query_one(f"#config-{config.VALID_FIELDS[0]}").focus()

    def on_button_pressed(self, event):
        if event.button.id == "config-save":
            self._save()
        elif event.button.id == "config-edit":
            self._open_editor()
        elif event.button.id == "config-reload":
            self._load()
        elif event.button.id == "config-close":
            self.dismiss(None)

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
            if field in self.FIELD_CHOICES:
                select = self.query_one(f"#config-{field}", Select)
                select.value = settings.get(field) or self.FIELD_DEFAULTS[field]
                continue
            box = self.query_one(f"#config-{field}", Input)
            box.value = str(settings.get(field, "") or "")
            env_var = self.ENV_FOR_FIELD.get(field)
            box.placeholder = (
                f"{field} (overridden by {env_var})" if env_var and env_var in env else field
            )

    def action_submit(self):
        self._save()

    @work
    async def _save(self):
        changed = []
        for field in config.VALID_FIELDS:
            if field in self.FIELD_CHOICES:
                value = self.query_one(f"#config-{field}", Select).value
                default = self.FIELD_DEFAULTS[field]
                current = config.get_setting(field) or default
                if value != current:
                    await asyncio.to_thread(config.set_setting, field, value)
                    changed.append(field)
                    if field == "images" and value != "off" and not getattr(
                            self.app, "image_widgets", None):
                        self.notify(
                            "Restart the TUI to enable images (the terminal wasn't "
                            "probed for graphics support at launch).", severity="warning")
                continue
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

    @work
    async def _open_editor(self):
        settings_file = await asyncio.to_thread(core.ensure_settings_file)
        editor = config.get_editor()
        with self.app.suspend():
            subprocess.call([editor, settings_file])
        self._load()
