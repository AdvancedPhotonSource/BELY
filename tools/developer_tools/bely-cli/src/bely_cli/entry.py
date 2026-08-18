import os
from types import SimpleNamespace

from . import auth
from .common import find_logdoc, is_no_prompt, read_file_or_stdin, write_entry_to_file, open_in_editor, print_items, print_result


def resolve_doc(logbook_api, doc_name, doc_id):
    """Resolve a document by name or ID. Raises ValueError on error."""
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


def upload_and_print_attachment(logbook_api, doc_id, log_id, path, fmt="text"):
    """Upload an attachment and return its details as a dict.

    Prints the human-readable summary only for text format.
    """
    basename = os.path.basename(path)
    att = logbook_api.upload_attachment(
        log_document_id=doc_id,
        log_id=log_id,
        body=path,
        append_reference=True,
        file_name=basename,
    )
    info = {
        "original_filename": att.original_filename,
        "stored_filename": att.stored_filename,
        "download_path": att.download_path,
        "markdown_reference": att.markdown_reference,
    }
    if fmt == "text":
        print(f'Attachment "{basename}" uploaded')
        print(f"  original_filename:  {att.original_filename}")
        print(f"  stored_filename:    {att.stored_filename}")
        print(f"  download_path:      {att.download_path}")
        print(f"  markdown_reference: {att.markdown_reference}")
    return info


def cmd_update_entry(doc_name, doc_id, entry_id, file, text, add_attachment, fmt="text"):
    """Update an existing log entry."""
    if file and text:
        raise ValueError("--file and --text are mutually exclusive.")

    if is_no_prompt() and not entry_id and not auth.get_configured_username():
        raise ValueError("--id or a configured username (BELY_USER / 'user' setting) required in non-interactive mode")

    # Validate attachments and read content before any network calls
    if add_attachment:
        add_attachment = os.path.expanduser(add_attachment)
        if not os.path.isfile(add_attachment):
            raise ValueError(f"attachment file not found: {add_attachment}")

    content = read_file_or_stdin(file) if file else text

    # Resolve document (unauthenticated)
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)

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
                raise ValueError(f'entry with log_id={entry_id} not found in document "{doc.name}".')
        else:
            # Find last entry by current user
            username = auth.get_username()
            if not username:
                raise ValueError("cannot determine username. Set BELY_USER or 'user' in settings.")
            user_entries = [e for e in entries
                           if e.entered_by_username
                           and e.entered_by_username.lower() == username.lower()]
            if not user_entries:
                raise ValueError(f'no entries by user "{username}" found in document "{doc.name}".')
            entry = user_entries[-1]

        # Update entry content
        result = {"doc": doc.name, "log_id": entry.log_id, "status": None,
                  "attachment": None}
        if content:
            entry.log_entry = content
            entry = logbook_api.add_update_log_entry(log_entry=entry)
            result["log_id"] = entry.log_id
            result["status"] = "updated"
            if fmt == "text":
                print(f'Log entry updated in "{doc.name}", log_id={entry.log_id}')
        elif add_attachment:
            result["attachment"] = upload_and_print_attachment(
                logbook_api, doc.id, entry.log_id, add_attachment, fmt)
            result["status"] = "attachment_added"
        else:
            # Interactive edit: open entry in editor
            original = entry.log_entry or ""
            edited = open_in_editor(original)
            if edited != original:
                entry.log_entry = edited
                entry = logbook_api.add_update_log_entry(log_entry=entry)
                result["log_id"] = entry.log_id
                result["status"] = "updated"
                if fmt == "text":
                    print(f'Log entry updated in "{doc.name}", log_id={entry.log_id}')
            else:
                result["status"] = "no_change"
                if fmt == "text":
                    print("No changes made.")

        if fmt != "text":
            print_result(result, "", fmt)


def cmd_add_entry(doc_name, doc_id, file, text, add_attachment, fmt="text"):
    """Add a new log entry to an existing document."""
    if file and text:
        raise ValueError("--file and --text are mutually exclusive.")
    use_editor = not file and not text and not add_attachment

    # Validate attachments and read content before any network calls
    if add_attachment:
        add_attachment = os.path.expanduser(add_attachment)
        if not os.path.isfile(add_attachment):
            raise ValueError(f"attachment file not found: {add_attachment}")

    content = read_file_or_stdin(file) if file else text

    # Resolve document (unauthenticated)
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)

    # Authenticate and create entry
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()

        entry = logbook_api.get_log_entry_template(log_document_id=doc.id)

        result = {"doc": doc.name, "log_id": None, "status": None, "attachment": None}
        if use_editor:
            edited = open_in_editor(entry.log_entry or "")
            if edited.strip():
                entry.log_entry = edited
                entry = logbook_api.add_update_log_entry(log_entry=entry)
                result["log_id"] = entry.log_id
                result["status"] = "added"
                if fmt == "text":
                    print(f'Log entry added to "{doc.name}", log_id={entry.log_id}')
            else:
                result["status"] = "skipped"
                if fmt == "text":
                    print("Empty entry, skipped.")
        else:
            entry.log_entry = content or ""
            entry = logbook_api.add_update_log_entry(log_entry=entry)
            result["log_id"] = entry.log_id
            result["status"] = "added"
            if fmt == "text":
                print(f'Log entry added to "{doc.name}", log_id={entry.log_id}')

            if add_attachment:
                result["attachment"] = upload_and_print_attachment(
                    logbook_api, doc.id, entry.log_id, add_attachment, fmt)

        if fmt != "text":
            print_result(result, "", fmt)


def cmd_list_entries(doc_name, doc_id, fmt="text"):
    """List entries in a log document."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)
    entries = logbook_api.get_log_entries(log_document_id=doc.id)

    if not entries:
        if fmt == "text":
            print(f'No entries found in document {doc.name}.')
        else:
            print_items([], [], fmt)
        return

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
    columns = [("log_id", "Log ID", 10), ("date", "Date", 18),
               ("author", "Author", 20), ("snippet", "Snippet", 0)]
    print_items(items, columns, fmt)


def cmd_get_entry(doc_name, doc_id, entry_id, output_dir, fmt="text"):
    """Write the markdown of a log entry to a file (latest by default)."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)
    entries = logbook_api.get_log_entries(log_document_id=doc.id)

    if not entries:
        raise ValueError(f'No entries found in document {doc.name}.')

    if entry_id:
        entry = next((e for e in entries if e.log_id == entry_id), None)
        if not entry:
            raise ValueError(f'entry with log_id={entry_id} not found in document {doc.name}.')
    else:
        entry = entries[-1]

    name_for_file = doc_name if doc_name else str(doc.id)
    out_path = write_entry_to_file(entry, name_for_file, output_dir, fmt)
    if fmt != "text":
        print_result(
            {"log_id": entry.log_id, "path": out_path, "doc": doc.name},
            "",
            fmt,
        )
