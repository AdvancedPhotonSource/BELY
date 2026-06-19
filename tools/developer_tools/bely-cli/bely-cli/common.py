import json
import os
import subprocess
import sys
import tempfile

import yaml

import belyApi


# Supported values for the global --format option (single source of truth).
FORMATS = ("text", "json", "yaml")


def print_items(items, columns, fmt="text"):
    """Print a list of dicts as a table, JSON array, or YAML sequence.

    columns: list of (key, header, width) tuples for the table format.
    fmt: one of FORMATS.
    """
    if fmt == "json":
        print(json.dumps(items, indent=2, default=str))
        return
    if fmt == "yaml":
        print(yaml.safe_dump(items, sort_keys=False, default_flow_style=False), end="")
        return
    header = "  ".join(f"{h:<{w}}" for _, h, w in columns)
    sep = "  ".join(f"{'-' * len(h):<{w}}" for _, h, w in columns)
    print(header)
    print(sep)
    for item in items:
        print("  ".join(f"{str(item.get(k, '')):<{w}}" for k, _, w in columns))


def print_result(data, message, fmt="text"):
    """Print a confirmation message (text) or structured data (json/yaml)."""
    if fmt == "json":
        print(json.dumps(data, default=str))
    elif fmt == "yaml":
        print(yaml.safe_dump(data, sort_keys=False, default_flow_style=False), end="")
    else:
        print(message)


def find_logdoc(logbook_api, name):
    try:
        existing = logbook_api.get_log_document_by_name(name=name)
        return existing
    except belyApi.exceptions.NotFoundException:
        return None


def _sanitize_for_filename(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def write_entry_to_file(entry, doc_name, output_dir=None, fmt="text"):
    """Write entry markdown to <doc_name>_entry_<id>.md in output_dir (cwd if None).

    Returns the path written. Prints the confirmation line only for text format.
    """
    directory = os.path.expanduser(output_dir) if output_dir else "."
    if not os.path.isdir(directory):
        print(f"Error: output directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    safe_doc = _sanitize_for_filename(doc_name)
    out_path = os.path.join(directory, f"{safe_doc}_entry_{entry.log_id}.md")
    with open(out_path, "w") as f:
        f.write(entry.log_entry or "")
    if fmt == "text":
        print(f'Wrote log entry id={entry.log_id} to {out_path}')
    return out_path


def open_in_editor(initial_content=""):
    """Open initial_content in $EDITOR and return the edited text."""
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as tmp:
        tmp.write(initial_content)
        tmp_path = tmp.name
    try:
        editor = os.environ.get("EDITOR", "vi")
        subprocess.call([editor, tmp_path])
        with open(tmp_path, "r") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
