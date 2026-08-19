"""Pure display helpers for the TUI: no textual/rich import here.

Everything in this module is plain data-in, string/list-out logic so it can be
unit-tested with plain SimpleNamespace stand-ins for the API models (see
test/test_tui.py) without touching a terminal.
"""


# -- list-row formatting (used by both the old curses UI and the new
#    Textual OptionList rows) --

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


def format_attachment(att):
    """Display string for a LogEntryAttachment."""
    name = getattr(att, "original_filename", None) or "(unnamed)"
    path = getattr(att, "download_path", None)
    return f"{name}  ({path})" if path else name


# -- table rows (DataTable columns for the types/docs nav levels) --

def _fmt_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""


def _named(items):
    """['name', ...] for a list of objects exposing a .name attribute."""
    names = [getattr(it, "name", None) or "" for it in (items or [])]
    return [n for n in names if n]


def _doc_systems(d):
    """Comma-joined system names from an ItemDomainLogbook's item_type_list."""
    return ", ".join(_named(getattr(d, "item_type_list", None)))


def _doc_modified(d):
    """Last-modified timestamp string from an ItemDomainLogbook's more_info."""
    more_info = getattr(d, "more_info", None)
    if more_info is None:
        return ""
    return _fmt_dt(getattr(more_info, "last_modified_on_date_time", None))


def _doc_owner(d):
    """Owner username from an ItemDomainLogbook's more_info."""
    more_info = getattr(d, "more_info", None)
    if more_info is None:
        return ""
    return getattr(more_info, "owner_username", None) or ""


TYPE_COLUMNS = [("Name", 24), ("Display", 24), ("Description", None)]


def type_row(t):
    """DataTable row cells for a logbook type (EntityType)."""
    name = getattr(t, "name", None) or ""
    display = getattr(t, "display_name", None) or ""
    description = getattr(t, "description", None) or ""
    return (name, display, description)


DOC_COLUMNS = [
    ("Name", 32), ("Description", None), ("Systems", 20), ("Owner", 14), ("Modified", 16),
]


def doc_row(d):
    """DataTable row cells for a log document (ItemDomainLogbook)."""
    name = getattr(d, "name", None) or "(unnamed)"
    description = getattr(d, "description", None) or ""
    return (name, description, _doc_systems(d), _doc_owner(d), _doc_modified(d))


def entry_row(e):
    """Row cells for a log entry: kept 1-tuple since entries stay list-rendered."""
    return (format_entry(e),)


# -- filtering / navigation --

def filter_items(items, query, render_fn):
    """Return items whose rendered string contains query (case-insensitive)."""
    if not query:
        return list(items)
    q = query.lower()
    return [it for it in items if q in render_fn(it).lower()]


# -- selection reference / reproduction command --

def entry_reference(doc, entry):
    """Reference dict for the selected entry, for json/yaml output."""
    return {
        "doc_id": getattr(doc, "id", None),
        "doc_name": getattr(doc, "name", None),
        "log_id": getattr(entry, "log_id", None),
    }


def reference_command(doc_id, log_id):
    """The ready-to-run command line for fetching the selected entry."""
    return f"bely-cli entry get -d {doc_id} --id {log_id}"


# -- metadata blocks for the preview pane --

def summarize_reactions(reactions):
    """Aggregate a list of LogReaction into a compact "emoji count" string."""
    if not reactions:
        return ""
    counts = {}
    order = []
    for r in reactions:
        reaction = getattr(r, "reaction", None)
        label = getattr(reaction, "emoji", None) or getattr(reaction, "name", None) or "?"
        if label not in counts:
            order.append(label)
        counts[label] = counts.get(label, 0) + 1
    return "  ".join(f"{label} {counts[label]}" for label in order)


def entry_metadata_rows(entry, doc):
    """[(label, value)] metadata rows for the entry preview header."""
    rows = [
        ("log_id", str(getattr(entry, "log_id", "") or "")),
        ("doc", getattr(doc, "name", None) or ""),
    ]

    entered_by = getattr(entry, "entered_by_username", None) or ""
    entered_at = _fmt_dt(getattr(entry, "entered_on_date_time", None))
    if entered_by or entered_at:
        rows.append(("by", "  ".join(v for v in (entered_by, entered_at) if v)))

    modified_by = getattr(entry, "last_modified_by_username", None) or ""
    modified_at = _fmt_dt(getattr(entry, "last_modified_on_date_time", None))
    if modified_by or modified_at:
        rows.append(("modified", "  ".join(v for v in (modified_by, modified_at) if v)))

    replies = getattr(entry, "log_replies", None) or []
    if replies:
        rows.append(("replies", str(len(replies))))

    reactions = summarize_reactions(getattr(entry, "log_reactions", None))
    if reactions:
        rows.append(("reactions", reactions))

    return rows


def doc_metadata_rows(doc):
    """[(label, value)] metadata rows for the document preview header."""
    rows = [("name", getattr(doc, "name", None) or "")]

    description = getattr(doc, "description", None)
    if description:
        rows.append(("description", description))

    type_names = _named(getattr(doc, "entity_type_list", None))
    if type_names:
        rows.append(("logbook types", ", ".join(type_names)))

    systems = _doc_systems(doc)
    if systems:
        rows.append(("systems", systems))

    more_info = getattr(doc, "more_info", None)
    if more_info is not None:
        owner = getattr(more_info, "owner_username", None)
        if owner:
            rows.append(("owner", owner))
        created_by = getattr(more_info, "created_by_username", None)
        created_at = _fmt_dt(getattr(more_info, "created_on_date_time", None))
        if created_by or created_at:
            rows.append(("created", "  ".join(v for v in (created_by, created_at) if v)))
        modified_by = getattr(more_info, "last_modified_by_username", None)
        modified_at = _fmt_dt(getattr(more_info, "last_modified_on_date_time", None))
        if modified_by or modified_at:
            rows.append(("modified", "  ".join(v for v in (modified_by, modified_at) if v)))

    lockout = getattr(doc, "log_lockout_hours", None)
    if lockout:
        rows.append(("lockout", f"{lockout}h"))

    return rows


def type_metadata_rows(t):
    """[(label, value)] metadata rows for the logbook-type preview header."""
    rows = [("name", getattr(t, "name", None) or "")]

    display_name = getattr(t, "display_name", None)
    if display_name:
        rows.append(("display name", display_name))

    long_display_name = getattr(t, "long_display_name", None)
    if long_display_name and long_display_name != display_name:
        rows.append(("long display name", long_display_name))

    description = getattr(t, "description", None)
    if description:
        rows.append(("description", description))

    return rows
