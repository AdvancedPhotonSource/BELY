import os
import subprocess
import sys
import tempfile

import belyApi

import auth
import settings


ENV_VARS = ["BELY_HOST", "BELY_USER", "BELY_PASSWORD"]


def cmd_show_config():
    """Show current configuration from settings file and environment."""
    print(f"Settings file: {settings.SETTINGS_FILE}")
    data = settings.load_settings()
    if data:
        for key, value in data.items():
            print(f"  {key} = {value}")
    else:
        print("  (no settings)")

    print()
    print("Environment variables:")
    found = False
    for var in ENV_VARS:
        val = os.environ.get(var)
        if val is not None:
            display = "****" if "PASSWORD" in var else val
            print(f"  {var} = {display}")
            found = True
    if not found:
        print("  (none set)")


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

def find_logdoc(logbook_api, name):
    try:
        existing = logbook_api.get_log_document_by_name(name=name)
        return existing
    except belyApi.exceptions.NotFoundException:
        return None


def cmd_edit_config():
    """Open the settings file in the user's editor."""
    settings._ensure_config_dir()
    if not os.path.exists(settings.SETTINGS_FILE):
        settings.save_settings({})
    editor = os.environ.get("EDITOR", "vi")
    os.execvp(editor, [editor, settings.SETTINGS_FILE])



def cmd_new_doc(type_, name, file, template, systems, no_template, no_prompt):
    """Create a new log document, optionally adding a first log entry."""
    if template and no_template:
        print("Error: --template and --no-template are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    # Resolve names to IDs using unauthenticated API
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()

    try:
        logbook_type = find_logbook_type(logbook_api, type_)
        system_id_list = find_systems(logbook_api, systems) if systems else None
        template_id = find_template(logbook_api, template).id if template else None
        if find_logdoc(logbook_api, name):
            raise ValueError(f"A log document named '{name}' already exists")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


    # Build document options
    doc_opts = belyApi.LogDocumentOptions(
        name=name,
        logbook_type_id=logbook_type.id,
    )
    if system_id_list:
        doc_opts.system_id_list = system_id_list
    if template_id:
        doc_opts.template_id = template_id
    if no_template:
        doc_opts.skip_default_logbook_type_template = True

    # Authenticate and create document
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()
        doc = logbook_api.create_logbook_document(log_document_options=doc_opts)
        print(f'New document "{doc.name}" created, id={doc.id}')

        # Determine entry content from --file or --text
        content = None
        if file:
            file = os.path.expanduser(file)
            with open(file, "r") as f:
                content = f.read()

        # Check if creating the doc already produced a default entry
        entries = logbook_api.get_log_entries(log_document_id=doc.id)

        if content:
            if entries:
                entry = entries[0]
                entry.log_entry = content
            else:
                entry = logbook_api.get_log_entry_template(log_document_id=doc.id)
                entry.log_entry = content
            entry = logbook_api.add_update_log_entry(log_entry=entry)
            print(f"Log entry added, log_id={entry.log_id}")
        elif entries:
            entry = entries[0]
            print(f"Default entry (log_id={entry.log_id}):")
            print(entry.log_entry)


def cmd_list_docs(limit):
    """List recent log documents created by the current user."""
    username = auth.get_username()
    if not username:
        print("Error: cannot determine username. Set BELY_USER or 'user' in settings.",
              file=sys.stderr)
        sys.exit(1)

    factory = auth.get_factory()
    users_api = factory.get_users_api()
    try:
        user_info = users_api.get_user_by_username(username=username)
    except Exception as e:
        print(f"Error: could not look up user '{username}': {e}", file=sys.stderr)
        sys.exit(1)

    search_api = factory.get_search_api()
    results = search_api.search_logbook(search_text="*", user_id=[user_info.id])

    docs = results.document_results or []
    # Sort by last_modified_on descending
    docs.sort(key=lambda d: d.last_modified_on or "", reverse=True)
    docs = docs[:limit]

    if not docs:
        print("No documents found.")
        return

    print(f"{'ID':<8} {'Name':<50} {'Type':<15} {'Last Modified'}")
    print(f"{'--':<8} {'----':<50} {'----':<15} {'-------------'}")
    for d in docs:
        modified = d.last_modified_on.strftime("%Y-%m-%d %H:%M") if d.last_modified_on else ""
        doc_type = d.logbook_type or ""
        name = d.object_name or ""
        print(f"{d.object_id:<8} {name:<50} {doc_type:<15} {modified}")


def cmd_update_entry(name, entry_id, file, text, add_attachment):
    """Update an existing log entry."""
    if file and text:
        print("Error: --file and --text are mutually exclusive.", file=sys.stderr)
        sys.exit(1)
    if not name:
        print("Error: --name is required.", file=sys.stderr)
        sys.exit(1)

    # Validate files exist before any network calls
    if file:
        file = os.path.expanduser(file)
        if not os.path.isfile(file):
            print(f"Error: file not found: {file}", file=sys.stderr)
            sys.exit(1)
    if add_attachment:
        add_attachment = os.path.expanduser(add_attachment)
        if not os.path.isfile(add_attachment):
            print(f"Error: attachment file not found: {add_attachment}", file=sys.stderr)
            sys.exit(1)

    # Determine content
    content = None
    if file:
        with open(file, "r") as f:
            content = f.read()
    elif text:
        content = text

    # Look up document (unauthenticated)
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = find_logdoc(logbook_api, name)
    if not doc:
        print(f'Error: log document "{name}" not found.', file=sys.stderr)
        sys.exit(1)

    # Authenticate and find/update entry
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()
        entries = logbook_api.get_log_entries(log_document_id=doc.id)

        if entry_id:
            # Find specific entry by log_id
            entry = None
            for e in entries:
                if e.log_id == entry_id:
                    entry = e
                    break
            if not entry:
                print(f'Error: entry with log_id={entry_id} not found in document "{name}".',
                      file=sys.stderr)
                sys.exit(1)
        else:
            # Find last entry by current user
            username = auth.get_username()
            if not username:
                print("Error: cannot determine username. Set BELY_USER or 'user' in settings.",
                      file=sys.stderr)
                sys.exit(1)
            user_entries = [e for e in entries
                           if e.entered_by_username
                           and e.entered_by_username.lower() == username.lower()]
            if not user_entries:
                print(f'Error: no entries by user "{username}" found in document "{name}".',
                      file=sys.stderr)
                sys.exit(1)
            entry = user_entries[-1]

        # Update entry content
        if content:
            entry.log_entry = content
            entry = logbook_api.add_update_log_entry(log_entry=entry)
            print(f'Log entry updated in "{doc.name}", log_id={entry.log_id}')
        elif add_attachment:
            logbook_api.upload_attachment(
                log_document_id=doc.id,
                log_id=entry.log_id,
                body=add_attachment,
                append_reference=True,
                file_name=os.path.basename(add_attachment),
            )
            print(f'Attachment "{os.path.basename(add_attachment)}" uploaded')
        else:
            # Interactive edit: open entry in editor
            original = entry.log_entry or ""
            with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as tmp:
                tmp.write(original)
                tmp_path = tmp.name
            try:
                editor = os.environ.get("EDITOR", "vi")
                subprocess.call([editor, tmp_path])
                with open(tmp_path, "r") as f:
                    edited = f.read()
            finally:
                os.unlink(tmp_path)
            if edited != original:
                entry.log_entry = edited
                entry = logbook_api.add_update_log_entry(log_entry=entry)
                print(f'Log entry updated in "{doc.name}", log_id={entry.log_id}')
            else:
                print("No changes made.")


def cmd_add_entry(name, file, text, add_attachment):
    """Add a new log entry to an existing document."""
    if file and text:
        print("Error: --file and --text are mutually exclusive.", file=sys.stderr)
        sys.exit(1)
    if not file and not text and not add_attachment:
        print("Error: at least one of --file, --text, or --add-attachment is required.",
              file=sys.stderr)
        sys.exit(1)

    # Validate files exist before any network calls
    if file:
        file = os.path.expanduser(file)
        if not os.path.isfile(file):
            print(f"Error: file not found: {file}", file=sys.stderr)
            sys.exit(1)
    if add_attachment:
        add_attachment = os.path.expanduser(add_attachment)
        if not os.path.isfile(add_attachment):
            print(f"Error: attachment file not found: {add_attachment}", file=sys.stderr)
            sys.exit(1)

    # Determine content
    content = None
    if file:
        with open(file, "r") as f:
            content = f.read()
    elif text:
        content = text

    # Look up document (unauthenticated)
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = find_logdoc(logbook_api, name)
    if not doc:
        print(f'Error: log document "{name}" not found.', file=sys.stderr)
        sys.exit(1)

    # Authenticate and create entry
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()

        entry = logbook_api.get_log_entry_template(log_document_id=doc.id)
        entry.log_entry = content or ""
        entry = logbook_api.add_update_log_entry(log_entry=entry)
        print(f'Log entry added to "{doc.name}", log_id={entry.log_id}')

        if add_attachment:
            logbook_api.upload_attachment(
                log_document_id=doc.id,
                log_id=entry.log_id,
                body=add_attachment,
                append_reference=True,
                file_name=os.path.basename(add_attachment),
            )
            print(f'Attachment "{os.path.basename(add_attachment)}" uploaded')


def cmd_list_types():
    """List all logbook types."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    types = logbook_api.get_logbook_types()

    if not types:
        print("No logbook types found.")
        return

    print(f"{'ID':<6} {'Name':<20} {'Display Name':<30} {'Description'}")
    print(f"{'--':<6} {'----':<20} {'------------':<30} {'-----------'}")
    for t in types:
        desc = t.description or ""
        print(f"{t.id:<6} {t.name:<20} {t.display_name:<30} {desc}")


def cmd_list_systems():
    """List all logbook systems."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    systems = logbook_api.get_logbook_systems()

    if not systems:
        print("No logbook systems found.")
        return

    print(f"{'ID':<6} {'Name':<30} {'Description'}")
    print(f"{'--':<6} {'----':<30} {'-----------'}")
    for s in systems:
        desc = s.description or ""
        print(f"{s.id:<6} {s.name:<30} {desc}")


def cmd_list_templates():
    """List all logbook templates."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    templates = logbook_api.get_logbook_templates()

    if not templates:
        print("No logbook templates found.")
        return

    print(f"{'ID':<6} {'Name':<30} {'Description'}")
    print(f"{'--':<6} {'----':<30} {'-----------'}")
    for t in templates:
        desc = t.description or ""
        print(f"{t.id:<6} {t.name:<30} {desc}")
