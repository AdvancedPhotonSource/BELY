"""NewDocScreen: the `doc new` equivalent -- create a document, then optionally
compose its first entry.

Mirrors cmd_new_doc's flow (commands.py) as closely as a form can: resolve
type/systems/template via PickerScreen (all unauthenticated lookups, same as
the CLI's `auth.get_factory()` for name resolution), ensure_auth() only when
actually creating, then reproduce the post-create entry branch -- a template
that already produced an entry offers to edit it, no entry offers to create
one.

Dismisses with the created document, or None if cancelled before creation.
"""

import asyncio
from types import SimpleNamespace

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Input, Static

from ... import core
from ...common import find_logdoc
from .dialog import CANCEL_HINT, SAVE_HINT, DialogButtons, DialogScreen, hinted_label

# Sentinel for "explicitly skip the default template" -- distinct from
# PickerScreen's own None-on-cancel so the two can't be confused.
_NO_TEMPLATE = SimpleNamespace(id=None, name="(no template)")


class NewDocScreen(DialogScreen):
    DEFAULT_CSS = """
    #newdoc-dialog {
        width: 70;
    }
    """

    BINDINGS = [Binding("ctrl+s", "submit", "Create", show=False)]

    BUTTON_ROWS = [
        ["newdoc-pick-type", "newdoc-pick-systems", "newdoc-pick-template"],
        ["newdoc-create", "newdoc-cancel"],
    ]

    def __init__(self, session, logbook_type=None):
        super().__init__()
        self.session = session
        self.logbook_type = logbook_type
        self.systems = []
        self.template = None
        self.skip_template = False

    def compose(self) -> ComposeResult:
        with Vertical(id="newdoc-dialog", classes="dialog"):
            yield Static("New document", id="newdoc-title")
            yield Input(placeholder="document name", id="newdoc-name")
            yield Static(id="newdoc-type")
            yield Static(id="newdoc-systems")
            yield Static(id="newdoc-template")
            with DialogButtons():
                yield Button("Type…", id="newdoc-pick-type")
                yield Button("Systems…", id="newdoc-pick-systems")
                yield Button("Template…", id="newdoc-pick-template")
            with DialogButtons():
                yield Button(hinted_label("Create", SAVE_HINT), variant="primary", id="newdoc-create")
                yield Button(hinted_label("Cancel", CANCEL_HINT), id="newdoc-cancel")

    def on_mount(self):
        self._refresh_labels()
        self.query_one("#newdoc-name", Input).focus()

    def on_button_pressed(self, event):
        if event.button.id == "newdoc-pick-type":
            self._pick_type()
        elif event.button.id == "newdoc-pick-systems":
            self._pick_systems()
        elif event.button.id == "newdoc-pick-template":
            self._pick_template()
        elif event.button.id == "newdoc-create":
            self._create()
        elif event.button.id == "newdoc-cancel":
            self.dismiss(None)

    def _refresh_labels(self):
        type_label = self.logbook_type.name if self.logbook_type else "(none)"
        self.query_one("#newdoc-type", Static).update(f"Type: {type_label}")

        names = ", ".join(s.name for s in self.systems) or "(none)"
        self.query_one("#newdoc-systems", Static).update(f"Systems: {names}")

        if self.template is not None:
            template_label = self.template.name
        elif self.skip_template:
            template_label = "(no template)"
        else:
            template_label = "(none)"
        self.query_one("#newdoc-template", Static).update(f"Template: {template_label}")

    # -- pickers --

    @work
    async def _pick_type(self):
        from .picker import PickerScreen

        try:
            types = await asyncio.to_thread(self.session.data.logbook_types)
        except Exception as e:
            self.notify(f"Could not load types: {e}", severity="error")
            return
        choice = await self.app.push_screen_wait(
            PickerScreen("Logbook type", types, lambda t: t.name or "")
        )
        if choice is not None:
            self.logbook_type = choice
            self._refresh_labels()

    @work
    async def _pick_systems(self):
        from .picker import PickerScreen

        try:
            systems = await asyncio.to_thread(self.session.data.logbook_systems)
        except Exception as e:
            self.notify(f"Could not load systems: {e}", severity="error")
            return
        choice = await self.app.push_screen_wait(
            PickerScreen("Systems (space to toggle)", systems, lambda s: s.name or "", multi=True)
        )
        if choice is not None:
            self.systems = choice
            self._refresh_labels()

    @work
    async def _pick_template(self):
        from .picker import PickerScreen

        try:
            templates = await asyncio.to_thread(self.session.data.logbook_templates)
        except Exception as e:
            self.notify(f"Could not load templates: {e}", severity="error")
            return
        items = [_NO_TEMPLATE] + list(templates)
        choice = await self.app.push_screen_wait(
            PickerScreen("Template", items, lambda t: t.name or "")
        )
        if choice is None:
            return
        if choice is _NO_TEMPLATE:
            self.template = None
            self.skip_template = True
        else:
            self.template = choice
            self.skip_template = False
        self._refresh_labels()

    # -- create, then reproduce cmd_new_doc's post-create entry prompts --

    def action_submit(self):
        self._create()

    @work
    async def _create(self):
        name = self.query_one("#newdoc-name", Input).value.strip()
        if not name:
            self.notify("Document name is required.", severity="warning")
            return
        if self.logbook_type is None:
            self.notify("Pick a logbook type first.", severity="warning")
            return

        try:
            existing = await asyncio.to_thread(
                find_logdoc, self.session.factory.get_logbook_api(), name)
        except Exception:
            existing = None
        if existing:
            self.notify(f'A log document named "{name}" already exists.', severity="error")
            return

        api = await self.app.ensure_auth()
        if api is None:
            return

        system_id_list = [s.id for s in self.systems] or None
        template_id = self.template.id if self.template else None
        try:
            doc = await asyncio.to_thread(
                core.create_document, api, name, self.logbook_type.id,
                system_id_list=system_id_list, template_id=template_id,
                skip_default_template=self.skip_template,
            )
        except Exception as e:
            self.notify(f"Create failed: {e}", severity="error")
            return

        self.notify(f'Document "{doc.name}" created, id={doc.id}')
        await self._post_create(api, doc)

    async def _post_create(self, api, doc):
        from .compose import open_composer
        from .confirm import ConfirmScreen

        try:
            entries = await asyncio.to_thread(api.get_log_entries, log_document_id=doc.id)
        except Exception:
            entries = []

        if entries:
            entry = entries[0]
            edit_now = await self.app.push_screen_wait(
                ConfirmScreen(
                    f"Template generated log entry #{entry.log_id}. Edit it now?",
                    confirm_label="Edit now", cancel_label="Leave as-is",
                )
            )
            if edit_now:
                await open_composer(self.app, doc, api, entry=entry)
        else:
            create_entry = await self.app.push_screen_wait(
                ConfirmScreen("Create a log entry now?", confirm_label="Create entry", cancel_label="Skip")
            )
            if create_entry:
                await open_composer(self.app, doc, api)

        self.dismiss(doc)
