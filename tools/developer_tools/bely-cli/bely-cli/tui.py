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


def step_index(index, delta, length):
    """Clamp index+delta to [0, length-1]. length<=0 returns 0."""
    if length <= 0:
        return 0
    return max(0, min(index + delta, length - 1))


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


# Display attributes. These start as monochrome fallbacks (used when the
# terminal has no color support) and are upgraded to theme-aware colors by
# _init_colors() once curses is running.
_A_TITLE = curses.A_BOLD
_A_SELECTED = curses.A_REVERSE | curses.A_BOLD
_A_FOOTER = curses.A_DIM
_A_ERROR = curses.A_BOLD

_PAIR_TITLE = 1
_PAIR_FOOTER = 2
_PAIR_ERROR = 3


def _init_colors():
    """Derive display attributes from the terminal's own palette.

    use_default_colors() lets us pass -1 for the background so the terminal's
    own background shows through, and the named ANSI colors resolve to whatever
    the user's theme defines for them. That keeps the UI legible on both light
    and dark terminals without hardcoding a background. The selected-row
    highlight uses reverse video, which simply swaps the terminal's current
    foreground/background and so adapts to any theme.
    """
    global _A_TITLE, _A_FOOTER, _A_ERROR
    if not curses.has_colors():
        return
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        return
    curses.init_pair(_PAIR_TITLE, curses.COLOR_CYAN, -1)
    curses.init_pair(_PAIR_FOOTER, curses.COLOR_BLUE, -1)
    curses.init_pair(_PAIR_ERROR, curses.COLOR_RED, -1)
    _A_TITLE = curses.color_pair(_PAIR_TITLE) | curses.A_BOLD
    _A_FOOTER = curses.color_pair(_PAIR_FOOTER)
    _A_ERROR = curses.color_pair(_PAIR_ERROR) | curses.A_BOLD


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
        _addstr(stdscr, 0, 0, title, width, _A_TITLE)

        if not shown:
            _addstr(stdscr, 2, 2, "(no items)", width)
        else:
            for row, item in enumerate(shown[top:top + body_h]):
                idx = top + row
                selected = idx == pos
                text = " " + render_fn(item)
                if selected:
                    # Pad to full width so the highlight reads as a solid bar.
                    text = text.ljust(width)
                _addstr(stdscr, 2 + row, 0, text, width,
                        _A_SELECTED if selected else 0)

        footer = f"Filter: {query}_   [Up/Down PgUp/PgDn] move  [Enter] open  [Esc] back  (type to filter)"
        _addstr(stdscr, height - 1, 0, footer, width, _A_FOOTER)
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


def _view_entry(stdscr, doc, entries, index):
    """Scrollable view of an entry's markdown, with Left/Right to move between
    entries in the document. Return (action, index) where action is 'select' or
    'back' and index is the (possibly changed) entry the user ended on."""
    top = 0

    while True:
        entry = entries[index]
        body = getattr(entry, "log_entry", None) or "(empty entry)"
        header = (
            f'{getattr(doc, "name", "")}  /  log_id={getattr(entry, "log_id", "")}'
            f'   ({index + 1}/{len(entries)})'
        )

        height, width = stdscr.getmaxyx()
        body_h = max(1, height - 3)

        lines = []
        for raw in body.splitlines() or [""]:
            wrapped = textwrap.wrap(raw, max(1, width - 1)) or [""]
            lines.extend(wrapped)

        max_top = max(0, len(lines) - body_h)
        top = min(top, max_top)

        stdscr.erase()
        _addstr(stdscr, 0, 0, header, width, _A_TITLE)
        for row, line in enumerate(lines[top:top + body_h]):
            _addstr(stdscr, 2 + row, 0, line, width)
        footer = "[Up/Down PgUp/PgDn] scroll  [Left/Right] prev/next entry  [Enter/q] select  [Esc] back"
        _addstr(stdscr, height - 1, 0, footer, width, _A_FOOTER)
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
        elif ch == curses.KEY_LEFT:
            new = step_index(index, -1, len(entries))
            if new != index:
                index, top = new, 0   # reset scroll on entry change
        elif ch == curses.KEY_RIGHT:
            new = step_index(index, +1, len(entries))
            if new != index:
                index, top = new, 0
        elif ch in _ENTER_KEYS or ch in (ord("q"), ord("Q")):
            return "select", index
        elif ch == _ESC or ch in _BACKSPACE_KEYS:
            return "back", index


def _loading(stdscr, message):
    """Show a transient status line while a network call runs."""
    _, width = stdscr.getmaxyx()
    stdscr.erase()
    _addstr(stdscr, 0, 0, message, width, _A_FOOTER)
    stdscr.refresh()


def _show_error(stdscr, message):
    """Show an error and wait for a keypress."""
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    _addstr(stdscr, 0, 0, "Error", width, _A_ERROR)
    for row, line in enumerate(textwrap.wrap(message, max(1, width - 1))):
        _addstr(stdscr, 2 + row, 0, line, width)
    _addstr(stdscr, height - 1, 0, "Press any key to go back", width, _A_FOOTER)
    stdscr.refresh()
    stdscr.getch()


def _run(stdscr, api, limit):
    """Drill-down loop. Return (doc, entry) if confirmed, else None."""
    curses.curs_set(0)
    # ncurses waits ESCDELAY ms after an ESC byte to see if it begins an escape
    # sequence (arrows, PgUp, ...). The default is 1000ms, which makes "Esc to
    # go back" feel frozen. 25ms is plenty to disambiguate real key sequences.
    if hasattr(curses, "set_escdelay"):
        curses.set_escdelay(25)
    _init_colors()

    level = 0
    sel_type = sel_doc = sel_entry = None

    # Per-session caches so back-navigation redraws from memory instead of
    # re-hitting the network. Keyed by parent id; errors are left uncached so a
    # later visit retries. `is None` checks distinguish "not fetched" from a
    # legitimately empty result list (which we do cache).
    types = None
    docs_cache = {}      # type_id -> list of documents
    entries_cache = {}   # doc_id -> list of entries

    while True:
        if level == 0:
            if types is None:
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
            docs = docs_cache.get(sel_type.id)
            if docs is None:
                _loading(stdscr, f"Loading recent documents in '{format_type(sel_type)}'...")
                try:
                    docs = api.get_log_documents(logbook_type_id=sel_type.id, limit=limit)
                except Exception as e:
                    _show_error(stdscr, f"Could not load documents: {e}")
                    level = 0
                    continue
                docs_cache[sel_type.id] = docs
            chosen = _select(
                stdscr, f"{format_type(sel_type)} - recent documents", docs, format_doc)
            if chosen is None:
                level = 0
                continue
            sel_doc = chosen
            level = 2

        elif level == 2:
            entries = entries_cache.get(sel_doc.id)
            if entries is None:
                _loading(stdscr, f"Loading entries in '{format_doc(sel_doc)}'...")
                try:
                    entries = api.get_log_entries(log_document_id=sel_doc.id)
                except Exception as e:
                    _show_error(stdscr, f"Could not load entries: {e}")
                    level = 1
                    continue
                entries_cache[sel_doc.id] = entries
            chosen = _select(
                stdscr, f"{format_doc(sel_doc)} - entries", entries, format_entry)
            if chosen is None:
                level = 1
                continue
            sel_entry = chosen
            level = 3

        elif level == 3:
            entries = entries_cache[sel_doc.id]   # already populated at level 2
            idx = next(i for i, e in enumerate(entries) if e is sel_entry)
            action, idx = _view_entry(stdscr, sel_doc, entries, idx)
            sel_entry = entries[idx]
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
