import curses
import sys
import textwrap

import auth
from common import print_result

# belyApi is intentionally NOT imported at module scope: the heavy client is
# pulled in lazily by auth.get_factory() only when the TUI actually runs, so the
# --help path stays fast (see auth.py).


# -- pure helpers (no curses; unit-tested) --

def format_type(t):
    """Display string for a logbook type (EntityType)."""
    display = getattr(t, "display_name", None) or ""
    name = getattr(t, "name", None) or ""
    return f"{name}  ({display})" if display else name


def format_doc(d):
    """Display string for a log document (ItemDomainLogbook)."""
    name = getattr(d, "name", None) or "(unnamed)"
    desc = getattr(d, "description", None)
    return f"{name}  -  {desc}" if desc else name


def format_entry(e):
    """Display string for a log entry: date, author, first-line snippet.

    Mirrors the snippet logic used by cmd_list_entries (entry.py).
    """
    dt = getattr(e, "entered_on_date_time", None)
    date = dt.strftime("%Y-%m-%d %H:%M") if dt else ""
    author = getattr(e, "entered_by_username", None) or ""
    body = getattr(e, "log_entry", None) or ""
    lines = [ln for ln in body.strip().splitlines() if ln.strip()]
    snippet = lines[0] if lines else ""
    if len(snippet) > 60:
        snippet = snippet[:57] + "..."
    return f"{date}  {author:<16}  {snippet}".rstrip()


def filter_items(items, query, render_fn):
    """Return items whose rendered string contains query (case-insensitive)."""
    if not query:
        return list(items)
    q = query.lower()
    return [it for it in items if q in render_fn(it).lower()]


def entry_reference(doc, entry):
    """Reference dict for the selected entry, for json/yaml output."""
    return {
        "doc_id": getattr(doc, "id", None),
        "doc_name": getattr(doc, "name", None),
        "log_id": getattr(entry, "log_id", None),
    }


# -- curses helpers --

_ENTER_KEYS = (curses.KEY_ENTER, 10, 13)
_BACKSPACE_KEYS = (curses.KEY_BACKSPACE, 127, 8)
_ESC = 27


def _addstr(stdscr, y, x, text, width, attr=0):
    """Write text truncated to width, swallowing curses edge errors."""
    try:
        stdscr.addstr(y, x, text[:max(0, width)], attr)
    except curses.error:
        pass


def _select(stdscr, title, items, render_fn):
    """Interactive, filterable list. Return the chosen item, or None to go back.

    Up/Down/PgUp/PgDn move; printable chars filter; Backspace edits the filter
    (and goes back when the filter is empty); Enter selects; Esc goes back.
    """
    query = ""
    pos = 0      # highlighted index within the filtered list
    top = 0      # first visible row (for scrolling)

    while True:
        height, width = stdscr.getmaxyx()
        body_h = max(1, height - 3)  # rows available for list items
        shown = filter_items(items, query, render_fn)

        if pos >= len(shown):
            pos = max(0, len(shown) - 1)
        if pos < top:
            top = pos
        elif pos >= top + body_h:
            top = pos - body_h + 1

        stdscr.erase()
        _addstr(stdscr, 0, 0, title, width, curses.A_BOLD)

        if not shown:
            _addstr(stdscr, 2, 2, "(no items)", width)
        else:
            for row, item in enumerate(shown[top:top + body_h]):
                idx = top + row
                attr = curses.A_REVERSE if idx == pos else 0
                _addstr(stdscr, 2 + row, 0, " " + render_fn(item), width, attr)

        footer = f"Filter: {query}_   [Up/Down PgUp/PgDn] move  [Enter] open  [Esc] back  (type to filter)"
        _addstr(stdscr, height - 1, 0, footer, width, curses.A_DIM)
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == curses.KEY_UP:
            pos = max(0, pos - 1)
        elif ch == curses.KEY_DOWN:
            pos = min(len(shown) - 1, pos + 1) if shown else 0
        elif ch == curses.KEY_PPAGE:
            pos = max(0, pos - body_h)
        elif ch == curses.KEY_NPAGE:
            pos = min(len(shown) - 1, pos + body_h) if shown else 0
        elif ch in _ENTER_KEYS:
            if shown:
                return shown[pos]
        elif ch == _ESC:
            return None
        elif ch in _BACKSPACE_KEYS:
            if query:
                query = query[:-1]
                pos = 0
            else:
                return None  # empty filter + backspace = go back
        elif 32 <= ch <= 126:
            query += chr(ch)
            pos = 0


def _view_entry(stdscr, doc, entry):
    """Scrollable view of an entry's markdown. Return 'select' or 'back'."""
    body = getattr(entry, "log_entry", None) or "(empty entry)"
    top = 0
    header = f'{getattr(doc, "name", "")}  /  log_id={getattr(entry, "log_id", "")}'

    while True:
        height, width = stdscr.getmaxyx()
        body_h = max(1, height - 3)

        lines = []
        for raw in body.splitlines() or [""]:
            wrapped = textwrap.wrap(raw, max(1, width - 1)) or [""]
            lines.extend(wrapped)

        max_top = max(0, len(lines) - body_h)
        top = min(top, max_top)

        stdscr.erase()
        _addstr(stdscr, 0, 0, header, width, curses.A_BOLD)
        for row, line in enumerate(lines[top:top + body_h]):
            _addstr(stdscr, 2 + row, 0, line, width)
        footer = "[Up/Down PgUp/PgDn] scroll  [Enter/q] select this entry  [Esc] back"
        _addstr(stdscr, height - 1, 0, footer, width, curses.A_DIM)
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == curses.KEY_UP:
            top = max(0, top - 1)
        elif ch == curses.KEY_DOWN:
            top = min(max_top, top + 1)
        elif ch == curses.KEY_PPAGE:
            top = max(0, top - body_h)
        elif ch == curses.KEY_NPAGE:
            top = min(max_top, top + body_h)
        elif ch in _ENTER_KEYS or ch in (ord("q"), ord("Q")):
            return "select"
        elif ch == _ESC or ch in _BACKSPACE_KEYS:
            return "back"


def _loading(stdscr, message):
    """Show a transient status line while a network call runs."""
    _, width = stdscr.getmaxyx()
    stdscr.erase()
    _addstr(stdscr, 0, 0, message, width, curses.A_DIM)
    stdscr.refresh()


def _show_error(stdscr, message):
    """Show an error and wait for a keypress."""
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    _addstr(stdscr, 0, 0, "Error", width, curses.A_BOLD)
    for row, line in enumerate(textwrap.wrap(message, max(1, width - 1))):
        _addstr(stdscr, 2 + row, 0, line, width)
    _addstr(stdscr, height - 1, 0, "Press any key to go back", width, curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()


def _run(stdscr, api, limit):
    """Drill-down loop. Return (doc, entry) if confirmed, else None."""
    curses.curs_set(0)

    level = 0
    sel_type = sel_doc = sel_entry = None
    docs = entries = []

    while True:
        if level == 0:
            _loading(stdscr, "Loading logbooks...")
            try:
                types = api.get_logbook_types()
            except Exception as e:  # broad: avoid importing belyApi just for its exceptions
                _show_error(stdscr, f"Could not load logbooks: {e}")
                return None
            chosen = _select(stdscr, "Select a logbook", types, format_type)
            if chosen is None:
                return None
            sel_type = chosen
            level = 1

        elif level == 1:
            _loading(stdscr, f"Loading recent documents in '{format_type(sel_type)}'...")
            try:
                docs = api.get_log_documents(logbook_type_id=sel_type.id, limit=limit)
            except Exception as e:
                _show_error(stdscr, f"Could not load documents: {e}")
                level = 0
                continue
            chosen = _select(
                stdscr, f"{format_type(sel_type)} - recent documents", docs, format_doc)
            if chosen is None:
                level = 0
                continue
            sel_doc = chosen
            level = 2

        elif level == 2:
            _loading(stdscr, f"Loading entries in '{format_doc(sel_doc)}'...")
            try:
                entries = api.get_log_entries(log_document_id=sel_doc.id)
            except Exception as e:
                _show_error(stdscr, f"Could not load entries: {e}")
                level = 1
                continue
            chosen = _select(
                stdscr, f"{format_doc(sel_doc)} - entries", entries, format_entry)
            if chosen is None:
                level = 1
                continue
            sel_entry = chosen
            level = 3

        elif level == 3:
            action = _view_entry(stdscr, sel_doc, sel_entry)
            if action == "back":
                level = 2
                continue
            return (sel_doc, sel_entry)


def cmd_tui(limit=100, fmt="text"):
    """Interactively browse logbooks -> documents -> entries to find an entry."""
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        print("Error: the tui requires an interactive terminal.", file=sys.stderr)
        sys.exit(1)

    factory = auth.get_factory()
    api = factory.get_logbook_api()

    result = curses.wrapper(_run, api, limit)
    if not result:
        return
    doc, entry = result

    if fmt == "text":
        print(f"doc-id: {doc.id}")
        print(f"log-id: {entry.log_id}")
        print(f"# fetch with: bely.py entry get -d {doc.id} --id {entry.log_id}")
    else:
        print_result(entry_reference(doc, entry), "", fmt)
