import os

from . import auth
from . import config
from . import core
from .common import find_logdoc, is_no_prompt, read_file_or_stdin, write_entry_to_file, open_in_editor, print_items, print_result

# Re-exported for backward compatibility: these used to live here and tests /
# callers may still import them from this module.
from .core import find_logbook_type, find_systems, find_template  # noqa: F401

ENV_VARS = core.ENV_VARS


def cmd_show_config(fmt="text"):
    """Show current configuration from settings file and environment."""
    data = core.collect_config()

    if fmt != "text":
        print_result(data, "", fmt)
        return

    print(f"Settings file: {data['settings_file']}")
    if data["settings"]:
        for key, value in data["settings"].items():
            print(f"  {key} = {value}")
    else:
        print("  (no settings)")

    print()
    print("Environment variables:")
    if data["environment"]:
        for var, display in data["environment"].items():
            print(f"  {var} = {display}")
    else:
        print("  (none set)")


def cmd_edit_config():
    """Open the settings file in the user's editor."""
    settings_file = core.ensure_settings_file()
    editor = config.get_editor()
    os.execvp(editor, [editor, settings_file])


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

    if is_no_prompt():
        missing = [opt for opt, val in [("--type", type_), ("--name", name)] if not val]
        if missing:
            raise ValueError(f"{', '.join(missing)} required in non-interactive mode")

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

    logbook_type = core.find_logbook_type(logbook_api, type_)
    system_id_list = core.find_systems(logbook_api, systems) if systems else None
    template_id = core.find_template(logbook_api, template).id if template else None
    if find_logdoc(logbook_api, name):
        raise ValueError(f"A log document named '{name}' already exists")

    # Authenticate and create document
    result = {"id": None, "name": name}
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()
        doc = core.create_document(
            logbook_api, name, logbook_type.id,
            system_id_list=system_id_list, template_id=template_id,
            skip_default_template=no_template,
        )
        result["id"] = doc.id
        result["name"] = doc.name
        if fmt == "text":
            print(f'New document "{doc.name}" created, id={doc.id}')

        # Determine entry content from --file or --text
        content = read_file_or_stdin(file) if file else None

        # Check if creating the doc already produced a default entry
        entries = logbook_api.get_log_entries(log_document_id=doc.id)

        if content:
            entry = entries[0] if entries else core.new_entry_template(logbook_api, doc.id)
            entry = core.save_entry(logbook_api, entry, content)
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
                        entry = core.save_entry(logbook_api, entry, edited)
                        print(f"Log entry updated, log_id={entry.log_id}")
                    else:
                        print("No changes made.")
                else:
                    write_entry_to_file(entry, doc.name, output_dir, fmt)
        else:
            if fmt == "text":
                answer = input("Create a log entry? [y/N] ").strip().lower()
                if answer in ("y", "yes"):
                    entry = core.new_entry_template(logbook_api, doc.id)
                    edited = open_in_editor(entry.log_entry or "")
                    if edited.strip():
                        entry = core.save_entry(logbook_api, entry, edited)
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
    docs = core.recent_documents(factory, username, limit)

    if not docs:
        if fmt == "text":
            print("No documents found.")
        else:
            print_items([], [], fmt)
        return

    items = []
    for d in docs:
        modified = getattr(d.more_info, "last_modified_on_date_time", None)
        items.append({
            "id": d.id,
            "name": d.name or "",
            "type": d.logbook_type or "",
            "last_modified": modified.strftime("%Y-%m-%d %H:%M") if modified else "",
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
