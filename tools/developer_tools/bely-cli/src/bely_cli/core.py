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


def find_entry(entries, log_id):
    """Return the entry with this log_id, or None."""
    for e in entries:
        if e.log_id == log_id:
            return e
    return None


def last_entry_by_user(entries, username):
    """Return the most recent entry entered by username (case-insensitive), or None."""
    user_entries = [
        e for e in entries
        if e.entered_by_username and e.entered_by_username.lower() == username.lower()
    ]
    return user_entries[-1] if user_entries else None


def entry_list_items(entries):
    """Row dicts (log_id/date/author/snippet) for cmd_list_entries / the TUI list."""
    items = []
    for e in entries:
        date = e.entered_on_date_time.strftime("%Y-%m-%d %H:%M") if e.entered_on_date_time else ""
        snippet = (e.log_entry or "").strip().splitlines()[0] if e.log_entry else ""
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."
        items.append({
            "log_id": e.log_id,
            "date": date,
            "author": e.entered_by_username or "",
            "snippet": snippet,
        })
    return items


# -- attachments --

def validate_attachment_path(path):
    """Expand and validate an attachment path. Raises ValueError if not a file."""
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        raise ValueError(f"attachment file not found: {path}")
    return path


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
    return {
        "original_filename": att.original_filename,
        "stored_filename": att.stored_filename,
        "download_path": att.download_path,
        "markdown_reference": att.markdown_reference,
    }


def download_attachment(download_api, stored_filename, scaling=None):
    """Return an attachment's raw bytes, optionally a server-scaled variant.

    The plain get_attachment()/get_attachment1() wrappers discard the response
    body (their _response_types_map maps '200' to None) -- only the
    _without_preload_content variants return the actual bytes.
    """
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
