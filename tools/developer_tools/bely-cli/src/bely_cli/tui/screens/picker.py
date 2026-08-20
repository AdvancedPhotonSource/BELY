"""PickerScreen: a reusable single/multi-select modal.

Wraps an OptionList with a filter Input (reusing format.filter_items, the
same filtering used by BrowseScreen). Single-select dismisses with the chosen
item on Enter or the Select button. Multi-select toggles the highlighted item
with `space` and dismisses with the list of selected items on Enter or the
Confirm button.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Input, OptionList, Static

from ..format import filter_items
from .dialog import CANCEL_HINT, DialogButtons, DialogScreen, hinted_label


class PickerScreen(DialogScreen):
    DEFAULT_CSS = """
    #picker-dialog {
        width: 60;
    }

    #picker-list {
        height: auto;
        max-height: 16;
    }
    """

    BINDINGS = [Binding("space", "toggle", "Toggle", show=False)]

    BUTTON_ROWS = [["picker-select", "picker-cancel"]]

    def __init__(self, title, items, label_fn, *, multi=False):
        super().__init__()
        self.title_text = title
        self.items = list(items)
        self.label_fn = label_fn
        self.multi = multi
        self.selected = set()
        self.shown = list(self.items)

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-dialog", classes="dialog"):
            yield Static(self.title_text, id="picker-title")
            yield Input(placeholder="type to filter", id="picker-filter")
            yield OptionList(id="picker-list")
            with DialogButtons():
                select_label = "Confirm" if self.multi else "Select"
                yield Button(hinted_label(select_label), variant="primary", id="picker-select")
                yield Button(hinted_label("Cancel", CANCEL_HINT), id="picker-cancel")

    def on_mount(self):
        self._populate("")
        self.query_one("#picker-filter", Input).focus()

    def _option_text(self, item):
        label = self.label_fn(item)
        if not self.multi:
            return label
        idx = self.items.index(item)
        mark = "[x]" if idx in self.selected else "[ ]"
        return f"{mark} {label}"

    def _populate(self, query):
        self.shown = filter_items(self.items, query, self.label_fn)
        lst = self.query_one("#picker-list", OptionList)
        highlighted = lst.highlighted
        lst.clear_options()
        for item in self.shown:
            lst.add_option(self._option_text(item))
        if self.shown:
            lst.highlighted = min(highlighted, len(self.shown) - 1) if highlighted is not None else 0

    def on_input_changed(self, event):
        if event.input.id == "picker-filter":
            self._populate(event.value)

    def on_input_submitted(self, event):
        if event.input.id == "picker-filter":
            self.query_one("#picker-list", OptionList).focus()

    def on_option_list_option_selected(self, event):
        if event.option_list.id != "picker-list":
            return
        self._select_highlighted()

    def on_button_pressed(self, event):
        if event.button.id == "picker-select":
            self._select_highlighted()
        elif event.button.id == "picker-cancel":
            self.dismiss(None)

    def _select_highlighted(self):
        if self.multi:
            self._confirm_multi()
            return
        lst = self.query_one("#picker-list", OptionList)
        if lst.highlighted is None or not self.shown:
            return
        self.dismiss(self.shown[lst.highlighted])

    def action_toggle(self):
        if not self.multi:
            return
        lst = self.query_one("#picker-list", OptionList)
        if lst.highlighted is None or not self.shown:
            return
        item = self.shown[lst.highlighted]
        idx = self.items.index(item)
        if idx in self.selected:
            self.selected.discard(idx)
        else:
            self.selected.add(idx)
        query = self.query_one("#picker-filter", Input).value
        self._populate(query)

    def _confirm_multi(self):
        self.dismiss([self.items[i] for i in sorted(self.selected)])
