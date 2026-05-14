import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import auth
from commands import find_logdoc


def resolve_doc(logbook_api, doc_name, doc_id):
    """Resolve a document by name or ID. Exits on error."""
    if doc_name and doc_id:
        print("Error: --doc-name and --doc-id are mutually exclusive.", file=sys.stderr)
        sys.exit(1)
    if not doc_name and not doc_id:
        print("Error: --doc-name or --doc-id is required.", file=sys.stderr)
        sys.exit(1)
    if doc_id:
        return SimpleNamespace(id=doc_id, name=f"id={doc_id}")
    doc = find_logdoc(logbook_api, doc_name)
    if not doc:
        print(f'Error: log document "{doc_name}" not found.', file=sys.stderr)
        sys.exit(1)
    return doc


def _sanitize_for_filename(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def write_entry_to_file(entry, doc_name, output_dir=None):
    """Write entry markdown to <doc_name>_entry_<id>.md in output_dir (cwd if None)."""
    directory = os.path.expanduser(output_dir) if output_dir else "."
    if not os.path.isdir(directory):
        print(f"Error: output directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    safe_doc = _sanitize_for_filename(doc_name)
    out_path = os.path.join(directory, f"{safe_doc}_entry_{entry.log_id}.md")
    with open(out_path, "w") as f:
        f.write(entry.log_entry or "")
    print(f'Wrote log entry id={entry.log_id} to {out_path}')
    return out_path


def upload_and_print_attachment(logbook_api, doc_id, log_id, path):
    basename = os.path.basename(path)
    att = logbook_api.upload_attachment(
        log_document_id=doc_id,
        log_id=log_id,
        body=path,
        append_reference=True,
        file_name=basename,
    )
    print(f'Attachment "{basename}" uploaded')
    print(f"  original_filename:  {att.original_filename}")
    print(f"  stored_filename:    {att.stored_filename}")
    print(f"  download_path:      {att.download_path}")
    print(f"  markdown_reference: {att.markdown_reference}")


def cmd_update_entry(doc_name, doc_id, entry_id, file, text, add_attachment):
    """Update an existing log entry."""
    if file and text:
        print("Error: --file and --text are mutually exclusive.", file=sys.stderr)
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
                print(f'Error: entry with log_id={entry_id} not found in document "{doc.name}".',
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
                print(f'Error: no entries by user "{username}" found in document "{doc.name}".',
                      file=sys.stderr)
                sys.exit(1)
            entry = user_entries[-1]

        # Update entry content
        if content:
            entry.log_entry = content
            entry = logbook_api.add_update_log_entry(log_entry=entry)
            print(f'Log entry updated in "{doc.name}", log_id={entry.log_id}')
        elif add_attachment:
            upload_and_print_attachment(logbook_api, doc.id, entry.log_id, add_attachment)
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


def cmd_add_entry(doc_name, doc_id, file, text, add_attachment):
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

    # Resolve document (unauthenticated)
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)

    # Authenticate and create entry
    with auth.get_authenticated_factory() as auth_factory:
        logbook_api = auth_factory.get_logbook_api()

        entry = logbook_api.get_log_entry_template(log_document_id=doc.id)
        entry.log_entry = content or ""
        entry = logbook_api.add_update_log_entry(log_entry=entry)
        print(f'Log entry added to "{doc.name}", log_id={entry.log_id}')

        if add_attachment:
            upload_and_print_attachment(logbook_api, doc.id, entry.log_id, add_attachment)


def cmd_list_entries(doc_name, doc_id):
    """List entries in a log document."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)
    entries = logbook_api.get_log_entries(log_document_id=doc.id)

    if not entries:
        print(f'No entries found in document {doc.name}.')
        return

    print(f"{'Log ID':<10} {'Date':<18} {'Author':<20} {'Snippet'}")
    print(f"{'------':<10} {'----':<18} {'------':<20} {'-------'}")
    for e in entries:
        date = e.entered_on_date_time.strftime("%Y-%m-%d %H:%M") if e.entered_on_date_time else ""
        author = e.entered_by_username or ""
        snippet = (e.log_entry or "").strip().splitlines()[0] if e.log_entry else ""
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."
        print(f"{e.log_id:<10} {date:<18} {author:<20} {snippet}")


def cmd_get_entry(doc_name, doc_id, entry_id, output_dir):
    """Write the markdown of a log entry to a file (latest by default)."""
    factory = auth.get_factory()
    logbook_api = factory.get_logbook_api()
    doc = resolve_doc(logbook_api, doc_name, doc_id)
    entries = logbook_api.get_log_entries(log_document_id=doc.id)

    if not entries:
        print(f'No entries found in document {doc.name}.', file=sys.stderr)
        sys.exit(1)

    if entry_id:
        entry = next((e for e in entries if e.log_id == entry_id), None)
        if not entry:
            print(f'Error: entry with log_id={entry_id} not found in document {doc.name}.',
                  file=sys.stderr)
            sys.exit(1)
    else:
        entry = entries[-1]

    name_for_file = doc_name if doc_name else str(doc.id)
    write_entry_to_file(entry, name_for_file, output_dir)
