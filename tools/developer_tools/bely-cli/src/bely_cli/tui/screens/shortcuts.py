"""Searchable keyboard-shortcut reference for the TUI."""

from typing import NamedTuple

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, Static

from .dialog import DialogScreen


class Shortcut(NamedTuple):
    key: str
    action: str
    category: str
    contexts: tuple[str, ...]


CATEGORY_ORDER = (
    "Navigation",
    "Browsing and display",
    "Documents and entries",
    "Attachments",
    "Dialogs and editing",
    "Application",
)

ALL_SHORTCUTS = (
    Shortcut("Up / Down", "Move the highlight", "Navigation", ("types", "docs", "entries", "attachments")),
    Shortcut("PgUp / PgDn", "Move by one page", "Navigation", ("types", "docs", "entries", "attachments")),
    Shortcut("Enter", "Open or select the highlighted item", "Navigation", ("types", "docs", "entries")),
    Shortcut("Esc / Backspace", "Go back one level", "Navigation", ("types", "docs", "entries")),
    Shortcut("/", "Filter the current table", "Browsing and display", ("types", "docs", "entries")),
    Shortcut("i", "Toggle the details panel", "Browsing and display", ("types", "docs")),
    Shortcut("f", "Toggle the full-width entry preview", "Browsing and display", ("entries",)),
    Shortcut("t", "Toggle replies", "Browsing and display", ("entries_with_replies",)),
    Shortcut("r", "Refresh the current level", "Browsing and display", ("types", "docs", "entries")),
    Shortcut("d", "Create a document", "Documents and entries", ("types", "docs")),
    Shortcut("n", "Add a top-level entry", "Documents and entries", ("docs", "entries")),
    Shortcut("p", "Add a reply", "Documents and entries", ("entries",)),
    Shortcut("u", "Edit the highlighted entry in the TUI", "Documents and entries", ("entries",)),
    Shortcut("e", "Edit the highlighted entry in $EDITOR", "Documents and entries", ("entries",)),
    Shortcut("s", "Save the highlighted entry to a file", "Documents and entries", ("entries",)),
    Shortcut("y", "Copy a CLI reference", "Documents and entries", ("entries",)),
    Shortcut("x", "Delete the highlighted document or entry", "Documents and entries", ("docs", "entries")),
    Shortcut("Shift+A", "Open the attachment browser", "Attachments", ("entries",)),
    Shortcut("u", "Upload an attachment", "Attachments", ("attachments",)),
    Shortcut("y", "Copy an attachment reference", "Attachments", ("attachments",)),
    Shortcut("x", "Delete an attachment", "Attachments", ("attachments",)),
    Shortcut("p", "Toggle the local-file preview", "Attachments", ("attachment_picker",)),
    Shortcut("/", "Filter filenames", "Attachments", ("attachment_picker",)),
    Shortcut("Tab / Right", "Complete a filesystem path", "Attachments", ("attachment_picker",)),
    Shortcut("Ctrl+U", "Clear the filesystem path", "Attachments", ("attachment_picker",)),
    Shortcut("Ctrl+Shift+A", "Select the filesystem path", "Attachments", ("attachment_picker",)),
    Shortcut("Ctrl+S", "Submit or save the current dialog", "Dialogs and editing", ("dialogs",)),
    Shortcut("Esc", "Cancel or close the current dialog", "Dialogs and editing", ("dialogs", "attachments")),
    Shortcut("Tab / Shift+Tab", "Move between fields and buttons", "Dialogs and editing", ("dialogs",)),
    Shortcut("Arrow keys", "Move between dialog buttons", "Dialogs and editing", ("dialogs",)),
    Shortcut("Space", "Toggle an item in a multi-select picker", "Dialogs and editing", ("dialogs",)),
    Shortcut("?", "Open or close keyboard shortcuts", "Application", ("types", "docs", "entries")),
    Shortcut("Ctrl+P", "Open the command palette", "Application", ("types", "docs", "entries")),
    Shortcut("q", "Quit", "Application", ("types", "docs", "entries")),
)


def shortcuts_for(context, *, has_replies=False, query=""):
    """Return relevant shortcuts, or key/action matches from the full catalog."""
    if query:
        needle = query.casefold()
        return [
            shortcut for shortcut in ALL_SHORTCUTS
            if needle in shortcut.key.casefold() or needle in shortcut.action.casefold()
        ]
    contexts = {context}
    if context == "entries" and has_replies:
        contexts.add("entries_with_replies")
    return [shortcut for shortcut in ALL_SHORTCUTS if contexts.intersection(shortcut.contexts)]


def format_shortcuts(shortcuts):
    """Format shortcut rows under stable logical category headings."""
    lines = []
    for category in CATEGORY_ORDER:
        rows = [shortcut for shortcut in shortcuts if shortcut.category == category]
        if not rows:
            continue
        if lines:
            lines.append("")
        lines.append(category)
        lines.append("─" * len(category))
        width = max(len(shortcut.key) for shortcut in rows)
        lines.extend(f"{shortcut.key:<{width}}  {shortcut.action}" for shortcut in rows)
    return "\n".join(lines) if lines else "No shortcuts match that key."


class ShortcutFilterInput(Input):
    """Search field where `?` closes help instead of entering the character."""

    def on_key(self, event: events.Key):
        if event.key == "question_mark":
            event.prevent_default()
            event.stop()
            self.screen.dismiss(None)


class ShortcutScreen(DialogScreen):
    """Modal shortcut list, relevant by default and global while searching."""

    DEFAULT_CSS = """
    #shortcut-dialog { width: 76; height: 80%; }
    #shortcut-filter { margin: 1 0; }
    #shortcut-scroll { height: 1fr; }
    #shortcut-list { height: auto; }
    """

    BINDINGS = [
        Binding("question_mark", "cancel", "Close", show=False, priority=True),
    ]

    def __init__(self, context, *, has_replies=False):
        super().__init__()
        self.context = context
        self.has_replies = has_replies

    def compose(self) -> ComposeResult:
        with Vertical(id="shortcut-dialog", classes="dialog"):
            yield Static("Keyboard shortcuts  ·  Esc/? close", id="shortcut-title")
            yield ShortcutFilterInput(
                placeholder="Search keys and actions", id="shortcut-filter")
            with VerticalScroll(id="shortcut-scroll"):
                yield Static(id="shortcut-list")

    def on_mount(self):
        self._show("")
        self.query_one("#shortcut-filter", Input).focus()

    def on_input_changed(self, event):
        if event.input.id == "shortcut-filter":
            self._show(event.value)

    def _show(self, query):
        rows = shortcuts_for(
            self.context, has_replies=self.has_replies, query=query.strip())
        self.query_one("#shortcut-list", Static).update(format_shortcuts(rows))
