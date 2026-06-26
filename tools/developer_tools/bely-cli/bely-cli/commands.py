import os

import auth
import config
from common import find_logdoc, write_entry_to_file, open_in_editor, print_items, print_result


ENV_VARS = ["BELY_HOST", "BELY_USER", "BELY_PASSWORD", "BELY_SETTINGS_FILE", "EDITOR"]


def cmd_show_config(fmt="text"):
    """Show current configuration from settings file and environment."""
    settings = config.load_settings()
    environment = {}
    for var in ENV_VARS:
        val = os.environ.get(var)
        if val is not None:
            environment[var] = "****" if "PASSWORD" in var else val

    if fmt != "text":
        print_result(
            {
                "settings_file": config.SETTINGS_FILE,
                "settings": settings,
                "environment": environment,
            },
            "",
            fmt,
        )
        return

    print(f"Settings file: {config.SETTINGS_FILE}")
    if settings:
        for key, value in settings.items():
            print(f"  {key} = {value}")
    else:
        print("  (no settings)")

    print()
    print("Environment variables:")
    if environment:
        for var, display in environment.items():
            print(f"  {var} = {display}")
    else:
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

def cmd_edit_config():
    """Open the settings file in the user's editor."""
    config._ensure_config_dir()
    if not os.path.exists(config.SETTINGS_FILE):
        config.save_settings({})
    editor = config.get_editor()
    os.execvp(editor, [editor, config.SETTINGS_FILE])


def cmd_set_config(field, value, fmt="text"):
    """Set a single configuration field in settings.yaml."""
    if field not in config.VALID_FIELDS:
        valid = ", ".join(config.VALID_FIELDS)
        raise ValueError(f"unknown field '{field}'. Valid fields: {valid}")
    config.set_setting(field, value)
    print_result({field: value}, f"Set {field} = {value}", fmt)



def cmd_new_doc(type_, name, file, template, systems, no_template,
                output_dir, list_options, fmt="text"):
    """Create a new log document, optionally adding a first log entry."""
    if list_options:
        _list_doc_option(list_options, fmt)
        return

    if template and no_template:
        raise ValueError("--template and --no-template are mutually exclusive.")

    # Resolve names to IDs using unauthenticated API
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()

    # Prompt for required fields if missing
    if not type_:
        types = logbook_api.get_logbook_types()
        print("Available logbook types:")
        for i, t in enumerate(types, 1):
            print(f"  {i}) {t.name} ({t.display_name})")
        choice = input("Select type (number or name): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if not (0 <= idx < len(types)):
                raise ValueError("invalid selection.")
            type_ = types[idx].name
        else:
            type_ = choice

    if not name:
        name = input("Document name: ").strip()
        if not name:
            raise ValueError("name cannot be empty.")

    logbook_type = find_logbook_type(logbook_api, type_)
    system_id_list = find_systems(logbook_api, systems) if systems else None
    template_id = find_template(logbook_api, template).id if template else None
    if find_logdoc(logbook_api, name):
        raise ValueError(f"A log document named '{name}' already exists")


    # Build document options
    import belyApi
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
    result = {"id": None, "name": name}
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()
        doc = logbook_api.create_logbook_document(log_document_options=doc_opts)
        result["id"] = doc.id
        result["name"] = doc.name
        if fmt == "text":
            print(f'New document "{doc.name}" created, id={doc.id}')

        # Determine entry content from --file or --text
        content = None
        if file:
            file = os.path.expanduser(file)
            if not os.path.isfile(file):
                raise ValueError(f"file not found: {file}")
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
            result["log_id"] = entry.log_id
            if fmt == "text":
                print(f"Log entry added, log_id={entry.log_id}")
        elif entries:
            entry = entries[0]
            result["log_id"] = entry.log_id
            if fmt == "text":
                print(f"Template generated a default log entry (log_id={entry.log_id})")
                answer = input("Update the entry? [y/N] ").strip().lower()
                if answer in ("y", "yes"):
                    edited = open_in_editor(entry.log_entry or "")
                    if edited != (entry.log_entry or ""):
                        entry.log_entry = edited
                        entry = logbook_api.add_update_log_entry(log_entry=entry)
                        print(f"Log entry updated, log_id={entry.log_id}")
                    else:
                        print("No changes made.")
                else:
                    write_entry_to_file(entry, doc.name, output_dir, fmt)
        else:
            if fmt == "text":
                answer = input("Create a log entry? [y/N] ").strip().lower()
                if answer in ("y", "yes"):
                    entry = logbook_api.get_log_entry_template(log_document_id=doc.id)
                    edited = open_in_editor(entry.log_entry or "")
                    if edited.strip():
                        entry.log_entry = edited
                        entry = logbook_api.add_update_log_entry(log_entry=entry)
                        result["log_id"] = entry.log_id
                        print(f"Log entry added, log_id={entry.log_id}")
                    else:
                        print("Empty entry, skipped.")

    if fmt != "text":
        print_result(result, "", fmt)


def cmd_list_docs(limit, fmt="text"):
    """List recent log documents created by the current user."""
    username = auth.get_username()
    if not username:
        raise ValueError("cannot determine username. Set BELY_USER or 'user' in settings.")

    factory = auth.get_factory()
    users_api = factory.get_users_api()
    try:
        user_info = users_api.get_user_by_username(username=username)
    except Exception as e:
        raise RuntimeError(f"could not look up user '{username}': {e}") from e

    search_api = factory.get_search_api()
    results = search_api.search_logbook(search_text="*", user_id=[user_info.id])

    docs = results.document_results or []
    # Sort by last_modified_on descending
    docs.sort(key=lambda d: d.last_modified_on or "", reverse=True)
    docs = docs[:limit]

    if not docs:
        if fmt == "text":
            print("No documents found.")
        else:
            print_items([], [], fmt)
        return

    items = []
    for d in docs:
        items.append({
            "id": d.object_id,
            "name": d.object_name or "",
            "type": d.logbook_type or "",
            "last_modified": d.last_modified_on.strftime("%Y-%m-%d %H:%M") if d.last_modified_on else "",
        })
    columns = [("id", "ID", 8), ("name", "Name", 50), ("type", "Type", 15), ("last_modified", "Last Modified", 20)]
    print_items(items, columns, fmt)


def _list_doc_option(option, fmt="text"):
    """Dispatch --list-options choice to the matching listing helper."""
    {
        "system": cmd_list_systems,
        "type": cmd_list_types,
        "template": cmd_list_templates,
    }[option](fmt)


def cmd_list_types(fmt="text"):
    """List all logbook types."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    types = logbook_api.get_logbook_types()

    items = [
        {
            "id": t.id,
            "name": t.name or "",
            "display_name": t.display_name or "",
            "description": t.description or "",
        }
        for t in types
    ]
    if not items and fmt == "text":
        print("No logbook types found.")
        return
    columns = [("id", "ID", 6), ("name", "Name", 20),
               ("display_name", "Display Name", 30), ("description", "Description", 0)]
    print_items(items, columns, fmt)


def cmd_list_systems(fmt="text"):
    """List all logbook systems."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    systems = logbook_api.get_logbook_systems()

    items = [
        {"id": s.id, "name": s.name or "", "description": s.description or ""}
        for s in systems
    ]
    if not items and fmt == "text":
        print("No logbook systems found.")
        return
    columns = [("id", "ID", 6), ("name", "Name", 30), ("description", "Description", 0)]
    print_items(items, columns, fmt)


def cmd_list_templates(fmt="text"):
    """List all logbook templates."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    templates = logbook_api.get_logbook_templates()

    items = [
        {"id": t.id, "name": t.name or "", "description": t.description or ""}
        for t in templates
    ]
    if not items and fmt == "text":
        print("No logbook templates found.")
        return
    columns = [("id", "ID", 6), ("name", "Name", 30), ("description", "Description", 0)]
    print_items(items, columns, fmt)
