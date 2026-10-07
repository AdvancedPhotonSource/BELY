"""API operations shared by the Click commands and the TUI screens.

Everything here takes an already-built `logbook_api` / `factory` (callers own
auth) and returns data or raises `ValueError`/`RuntimeError` — never prints,
never prompts, never imports Click or Textual. This is what lets the same
"add an entry" / "create a document" / "read config" logic be driven from a
`cmd_*` function (which prints) or a TUI screen (which renders widgets).

`belyApi` is imported lazily inside the functions that need it, matching the
import-cost discipline used elsewhere in this package.
"""

import os
from types import SimpleNamespace

from . import config


ENV_VARS = ["BELY_HOST", "BELY_USER", "BELY_PASSWORD", "BELY_SETTINGS_FILE", "EDITOR"]


# -- logbook type / system / template lookups (name -> object/IDs) --

def find_logbook_type(logbook_api, name):
    """Find a logbook type by name (case-insensitive). Raises ValueError if not found."""
    types = logbook_api.get_logbook_types()
    for t in types:
        if t.name and t.name.lower() == name.lower():
            return t
    available = ", ".join(t.name for t in types if t.name)
    raise ValueError(f"Unknown logbook type '{name}'. Available: {available}")


def find_systems(logbook_api, names_csv):
    """Resolve comma-separated system names to IDs. Raises ValueError on unknown name."""
    all_systems = logbook_api.get_logbook_systems()
    by_name = {s.name.lower(): s for s in all_systems}
    ids = []
    for name in names_csv.split(","):
        name = name.strip()
        if name.lower() not in by_name:
            available = ", ".join(s.name for s in all_systems)
            raise ValueError(f"Unknown system '{name}'. Available: {available}")
        ids.append(by_name[name.lower()].id)
    return ids


def find_template(logbook_api, name):
    """Find a template by name (case-insensitive). Raises ValueError if not found."""
    templates = logbook_api.get_logbook_templates()
    for t in templates:
        if t.name and t.name.lower() == name.lower():
            return t
    available = ", ".join(t.name for t in templates if t.name)
    raise ValueError(f"Unknown template '{name}'. Available: {available}")


# -- documents --

def resolve_doc(logbook_api, doc_name, doc_id):
    """Resolve a document by name or ID. Raises ValueError on error."""
    from .common import find_logdoc

    if doc_name and doc_id:
        raise ValueError("--doc-name and --doc-id are mutually exclusive.")
    if not doc_name and not doc_id:
        raise ValueError("--doc-name or --doc-id is required.")
    if doc_id:
        return SimpleNamespace(id=doc_id, name=f"id={doc_id}")
    doc = find_logdoc(logbook_api, doc_name)
    if not doc:
        raise ValueError(f'log document "{doc_name}" not found.')
    return doc


def get_document(factory, doc_name, doc_id):
    """Fetch a complete document by name or ID."""
    if doc_name and doc_id:
        raise ValueError("--doc-name and --doc-id are mutually exclusive.")
    if not doc_name and not doc_id:
        raise ValueError("--doc-name or --doc-id is required.")

    logbook_api = factory.get_logbook_api()
    if doc_name:
        from .common import find_logdoc
        doc = find_logdoc(logbook_api, doc_name)
        if not doc:
            raise ValueError(f'log document "{doc_name}" not found.')
        return doc

    results = factory.get_search_api().search_logbook(search_text="*")
    match = next(
        (item for item in (results.document_results or []) if item.object_id == doc_id),
        None,
    )
    if not match or not match.object_name:
        raise ValueError(f"log document id={doc_id} not found.")
    doc = logbook_api.get_log_document_by_name(name=match.object_name)
    if doc.id != doc_id:
        raise ValueError(f"log document id={doc_id} not found.")
    return doc


def _names(items):
    return [item.name for item in (items or []) if getattr(item, "name", None)]


def document_summary(doc):
    """Return stable summary fields for a log document."""
    more_info = getattr(doc, "more_info", None)
    domain = getattr(doc, "domain", None)
    return {
        "id": doc.id,
        "name": doc.name or "",
        "description": getattr(doc, "description", None) or "",
        "logbook": getattr(domain, "name", None) or "",
        "logbook_types": _names(getattr(doc, "entity_type_list", None)),
        "systems": _names(getattr(doc, "item_type_list", None)),
        "owner": getattr(more_info, "owner_username", None) or "",
        "owner_group": getattr(more_info, "owner_user_group_name", None) or "",
        "group_writeable": getattr(more_info, "is_group_writeable", None),
        "created_by": getattr(more_info, "created_by_username", None) or "",
        "created": getattr(more_info, "created_on_date_time", None),
        "modified_by": getattr(more_info, "last_modified_by_username", None) or "",
        "modified": getattr(more_info, "last_modified_on_date_time", None),
        "lockout_hours": getattr(doc, "log_lockout_hours", None),
    }


def create_document(logbook_api, name, logbook_type_id, system_id_list=None,
                     template_id=None, skip_default_template=False):
    """Create a new log document and return it."""
    import belyApi

    doc_opts = belyApi.LogDocumentOptions(name=name, logbook_type_id=logbook_type_id)
    if system_id_list:
        doc_opts.system_id_list = system_id_list
    if template_id:
        doc_opts.template_id = template_id
    if skip_default_template:
        doc_opts.skip_default_logbook_type_template = True
    return logbook_api.create_logbook_document(log_document_options=doc_opts)


def delete_document(logbook_api, doc_id):
    """Delete a top-level log document."""
    return logbook_api.delete_log_document(log_document_id=doc_id)


def recent_documents(factory, username, limit):
    """Return the user's most recently modified log documents, newest first.

    Returns objects shaped like log documents (id, name, description,
    logbook_type, more_info.last_modified_on_date_time) so tui.format's
    doc_row/doc_metadata_rows can render them like any other document.
    """
    users_api = factory.get_users_api()
    try:
        user_info = users_api.get_user_by_username(username=username)
    except Exception as e:
        raise RuntimeError(f"could not look up user '{username}': {e}") from e

    search_api = factory.get_search_api()
    results = search_api.search_logbook(search_text="*", user_id=[user_info.id])

    docs = results.document_results or []
    docs.sort(key=lambda d: d.last_modified_on or "", reverse=True)
    docs = docs[:limit]

    return [
        SimpleNamespace(
            id=d.object_id,
            name=d.object_name or "",
            description=None,
            logbook_type=d.logbook_type or "",
            more_info=SimpleNamespace(last_modified_on_date_time=d.last_modified_on),
        )
        for d in docs
    ]


# -- entries --

def new_entry_template(logbook_api, doc_id):
    """Return a blank/template entry for a document, ready to fill in and save."""
    return logbook_api.get_log_entry_template(log_document_id=doc_id)


def save_entry(logbook_api, entry, content):
    """Set an entry's content and save it. Returns the saved entry."""
    entry.log_entry = content
    return logbook_api.add_update_log_entry(log_entry=entry)


def new_reply_template(logbook_api, doc_id, parent_log_id):
    """Return a new entry template configured as a reply."""
    entry = new_entry_template(logbook_api, doc_id)
    entry.parent_log_id = parent_log_id
    return entry


def find_entry(entries, log_id):
    """Return the entry or nested reply with this log_id, or None."""
    for entry in entries:
        if entry.log_id == log_id:
            return entry
        reply = find_entry(getattr(entry, "log_replies", None) or [], log_id)
        if reply is not None:
            return reply
    return None


def last_entry_by_user(entries, username):
    """Return the most recent entry entered by username (case-insensitive), or None."""
    user_entries = [
        e for e in entries
        if e.entered_by_username and e.entered_by_username.lower() == username.lower()
    ]
    return user_entries[-1] if user_entries else None


def delete_entry(logbook_api, doc_id, log_id):
    """Delete a log entry or reply."""
    return logbook_api.delete_log_entry(log_document_id=doc_id, log_id=log_id)


def entry_list_items(entries, include_replies=False, parent_log_id=None):
    """Return display rows for entries, optionally followed by their replies."""
    items = []
    for entry in entries:
        date = (
            entry.entered_on_date_time.strftime("%Y-%m-%d %H:%M")
            if entry.entered_on_date_time else ""
        )
        snippet = (entry.log_entry or "").strip().splitlines()[0] if entry.log_entry else ""
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."
        item = {
            "log_id": entry.log_id,
            "date": date,
            "author": entry.entered_by_username or "",
            "snippet": snippet,
        }
        if include_replies:
            item["parent_log_id"] = parent_log_id or ""
        items.append(item)
        if include_replies:
            items.extend(entry_list_items(
                getattr(entry, "log_replies", None) or [],
                include_replies=True,
                parent_log_id=entry.log_id,
            ))
    return items


# -- attachments --

def validate_attachment_path(path):
    """Expand and validate an attachment path. Raises ValueError if not a file."""
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        raise ValueError(f"attachment file not found: {path}")
    return path


def attachment_info(att):
    """Return stable attachment fields for command and TUI consumers."""
    return {
        "id": att.id,
        "original_filename": att.original_filename,
        "stored_filename": att.stored_filename,
        "download_path": att.download_path,
        "markdown_reference": att.markdown_reference,
    }


def entry_attachments(logbook_api, doc_id, log_id):
    """Return attachment details for one log entry."""
    attachments = logbook_api.get_log_entry_attachments(
        log_document_id=doc_id, log_id=log_id)
    return [attachment_info(att) for att in attachments]


def upload_attachment(logbook_api, doc_id, log_id, path):
    """Upload an attachment and return its details as a dict."""
    basename = os.path.basename(path)
    att = logbook_api.upload_attachment(
        log_document_id=doc_id,
        log_id=log_id,
        body=path,
        append_reference=True,
        file_name=basename,
    )
    return attachment_info(att)


def delete_attachment(logbook_api, doc_id, log_id, attachment_id):
    """Delete an attachment by its numeric ID."""
    return logbook_api.delete_attachment(
        log_document_id=doc_id, log_id=log_id, attachment_id=attachment_id)


def download_attachment(download_api, stored_filename, scaling=None):
    """Return an attachment's raw bytes, optionally a server-scaled variant."""
    if scaling:
        response = download_api.get_attachment1_without_preload_content(
            stored_filename, scaling)
    else:
        response = download_api.get_attachment_without_preload_content(stored_filename)
    return response.data


# -- config --

def collect_config():
    """Return {settings_file, settings, environment} with passwords masked."""
    settings = config.load_settings()
    environment = {}
    for var in ENV_VARS:
        val = os.environ.get(var)
        if val is not None:
            environment[var] = "****" if "PASSWORD" in var else val
    return {
        "settings_file": config.SETTINGS_FILE,
        "settings": settings,
        "environment": environment,
    }


def ensure_settings_file():
    """Create the settings file (empty) if it doesn't exist yet. Returns its path."""
    config._ensure_config_dir()
    if not os.path.exists(config.SETTINGS_FILE):
        config.save_settings({})
    return config.SETTINGS_FILE
