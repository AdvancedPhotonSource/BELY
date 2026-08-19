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
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from ... import core
from ...common import find_logdoc

# Sentinel for "explicitly skip the default template" -- distinct from
# PickerScreen's own None-on-cancel so the two can't be confused.
_NO_TEMPLATE = SimpleNamespace(id=None, name="(no template)")


class NewDocScreen(ModalScreen):
    DEFAULT_CSS = """
    NewDocScreen {
        align: center middle;
    }

    #newdoc-dialog {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("ctrl+t", "pick_type", "Type"),
        Binding("ctrl+y", "pick_systems", "Systems"),
        Binding("ctrl+m", "pick_template", "Template"),
        Binding("ctrl+s", "submit", "Create"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, session, logbook_type=None):
        super().__init__()
        self.session = session
        self.logbook_type = logbook_type
        self.systems = []
        self.template = None
        self.skip_template = False

    def compose(self) -> ComposeResult:
        with Vertical(id="newdoc-dialog"):
            yield Static("New document", id="newdoc-title")
            yield Input(placeholder="document name", id="newdoc-name")
            yield Static(id="newdoc-type")
            yield Static(id="newdoc-systems")
            yield Static(id="newdoc-template")
            yield Static(
                "[ctrl+t] type   [ctrl+y] systems   [ctrl+m] template   "
                "[ctrl+s] create   [escape] cancel",
                id="newdoc-hint",
            )

    def on_mount(self):
        self._refresh_labels()
        self.query_one("#newdoc-name", Input).focus()

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

    def action_cancel(self):
        self.dismiss(None)

    # -- pickers --

    def action_pick_type(self):
        self._pick_type()

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

    def action_pick_systems(self):
        self._pick_systems()

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

    def action_pick_template(self):
        self._pick_template()

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
            self.notify("Pick a logbook type (ctrl+t) first.", severity="warning")
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
        from .picker import PickerScreen

        try:
            entries = await asyncio.to_thread(api.get_log_entries, log_document_id=doc.id)
        except Exception:
            entries = []

        if entries:
            entry = entries[0]
            choice = await self.app.push_screen_wait(
                PickerScreen(
                    f"Template generated log entry #{entry.log_id}. Edit it now?",
                    ["Edit now", "Leave as-is"], lambda x: x,
                )
            )
            if choice == "Edit now":
                await open_composer(self.app, doc, api, entry=entry)
        else:
            choice = await self.app.push_screen_wait(
                PickerScreen("Create a log entry now?", ["Create entry", "Skip"], lambda x: x)
            )
            if choice == "Create entry":
                await open_composer(self.app, doc, api)

        self.dismiss(doc)
