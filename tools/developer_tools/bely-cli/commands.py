import os
import sys

import belyApi

import auth
import config


ENV_VARS = ["BELY_HOST", "BELY_USER", "BELY_PASSWORD"]


def cmd_show_config():
    """Show current configuration from settings file and environment."""
    print(f"Settings file: {config.SETTINGS_FILE}")
    data = config.load_settings()
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
    config._ensure_config_dir()
    if not os.path.exists(config.SETTINGS_FILE):
        config.save_settings({})
    editor = os.environ.get("EDITOR", "vi")
    os.execvp(editor, [editor, config.SETTINGS_FILE])


def cmd_set_config(field, value):
    """Set a single configuration field in settings.yaml."""
    if field not in config.VALID_FIELDS:
        valid = ", ".join(config.VALID_FIELDS)
        print(f"Error: unknown field '{field}'. Valid fields: {valid}", file=sys.stderr)
        sys.exit(1)
    config.set_setting(field, value)
    print(f"Set {field} = {value}")



def cmd_new_doc(type_, name, file, template, systems, no_template, no_prompt, output_dir):
    """Create a new log document, optionally adding a first log entry."""
    if template and no_template:
        print("Error: --template and --no-template are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    # Resolve names to IDs using unauthenticated API
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()

    # Prompt for required fields if missing
    if not type_:
        if no_prompt:
            print("Error: --type is required.", file=sys.stderr)
            sys.exit(1)
        types = logbook_api.get_logbook_types()
        print("Available logbook types:")
        for i, t in enumerate(types, 1):
            print(f"  {i}) {t.name} ({t.display_name})")
        choice = input("Select type (number or name): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if not (0 <= idx < len(types)):
                print("Error: invalid selection.", file=sys.stderr)
                sys.exit(1)
            type_ = types[idx].name
        else:
            type_ = choice

    if not name:
        if no_prompt:
            print("Error: --name is required.", file=sys.stderr)
            sys.exit(1)
        name = input("Document name: ").strip()
        if not name:
            print("Error: name cannot be empty.", file=sys.stderr)
            sys.exit(1)

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
            from entry import write_entry_to_file
            print(f"Template generated a default log entry (log_id={entries[0].log_id})")
            write_entry_to_file(entries[0], doc.name, output_dir)


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
