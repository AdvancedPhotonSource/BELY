"""Shell completion cache and installation helpers."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

from . import auth, config

CACHE_TTL_SECONDS = 24 * 60 * 60
CACHE_DIR_NAME = "completion-cache"
BLOCK_START = "# >>> bely-cli completion >>>"
BLOCK_END = "# <<< bely-cli completion <<<"
SHELL_ENV = {"bash": "bash_source", "zsh": "zsh_source"}


def _host_key(host):
    return hashlib.sha256(host.encode("utf-8")).hexdigest()[:16]


def cache_dir():
    return os.path.join(config.CONFIG_DIR, CACHE_DIR_NAME)


def cache_path(host):
    return os.path.join(cache_dir(), f"{_host_key(host)}.json")


def lock_path(host):
    return os.path.join(cache_dir(), f"{_host_key(host)}.lock")


def load_cache(host):
    """Load this host's cache, returning None for missing or invalid data."""
    try:
        with open(cache_path(host), "r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("host") != host:
        return None
    return data


def cache_is_fresh(data, now=None):
    if not data:
        return False
    now = time.time() if now is None else now
    try:
        return now - float(data["refreshed_at"]) < CACHE_TTL_SECONDS
    except (KeyError, TypeError, ValueError):
        return False


def _write_cache_data(host, data):
    """Atomically replace this host's cache with already-formed data."""
    directory = cache_dir()
    os.makedirs(directory, mode=0o700, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix=".completion-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as cache_file:
            json.dump(data, cache_file, indent=2, sort_keys=True)
            cache_file.write("\n")
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, cache_path(host))
    finally:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
    return data


def write_cache(host, values, now=None):
    """Atomically replace this host's cache and return the stored data."""
    data = {
        "version": 1,
        "host": host,
        "refreshed_at": time.time() if now is None else now,
        **values,
    }
    return _write_cache_data(host, data)


def add_cached_document(document, logbook_type=""):
    """Add a newly created document to an existing current-host cache."""
    try:
        host = auth.get_host()
        data = load_cache(host)
        if data is None:
            return False
        document_id = getattr(document, "id", None)
        if document_id is None:
            return False
        documents = [
            item for item in data.get("documents", [])
            if str(item.get("id")) != str(document_id)
        ]
        documents.append({
            "id": document_id,
            "name": getattr(document, "name", None) or "",
            "type": getattr(document, "logbook_type", None) or logbook_type or "",
        })
        data["documents"] = sorted(documents, key=lambda item: item["name"].lower())
        _write_cache_data(host, data)
        return True
    except (OSError, TypeError, ValueError):
        return False


def remove_cached_document(document_id):
    """Remove a deleted document from the current-host cache."""
    try:
        host = auth.get_host()
        data = load_cache(host)
        if data is None:
            return False
        documents = data.get("documents", [])
        retained = [item for item in documents if str(item.get("id")) != str(document_id)]
        if len(retained) == len(documents):
            return False
        data["documents"] = retained
        _write_cache_data(host, data)
        return True
    except (OSError, TypeError, ValueError):
        return False


def clear_cache(host=None):
    """Clear one host cache, or all completion cache files when host is None."""
    directory = cache_dir()
    if host is not None:
        paths = (cache_path(host), lock_path(host))
    else:
        try:
            names = os.listdir(directory)
        except FileNotFoundError:
            return 0
        paths = tuple(os.path.join(directory, name) for name in names)

    removed = 0
    for path in paths:
        try:
            os.unlink(path)
            removed += 1
        except (FileNotFoundError, IsADirectoryError):
            pass
    return removed


def fetch_completion_values(factory=None):
    """Fetch public metadata used by completion."""
    factory = factory or auth.get_factory()
    logbook_api = factory.get_logbook_api()
    types = logbook_api.get_logbook_types()
    systems = logbook_api.get_logbook_systems()
    templates = logbook_api.get_logbook_templates()

    documents = {}
    for logbook_type in types:
        for document in logbook_api.get_log_documents(
                logbook_type_id=logbook_type.id, limit=100):
            document_id = getattr(document, "id", None)
            if document_id is None:
                continue
            documents[str(document_id)] = {
                "id": document_id,
                "name": getattr(document, "name", None) or "",
                "type": getattr(document, "logbook_type", None)
                        or getattr(logbook_type, "display_name", None)
                        or getattr(logbook_type, "name", None)
                        or "",
            }

    def metadata(items):
        return [
            {
                "name": getattr(item, "name", None) or "",
                "description": getattr(item, "description", None) or "",
            }
            for item in items if getattr(item, "name", None)
        ]

    return {
        "types": metadata(types),
        "systems": metadata(systems),
        "templates": metadata(templates),
        "documents": sorted(documents.values(), key=lambda item: item["name"].lower()),
    }


def refresh_cache(host=None, factory=None):
    """Synchronously fetch and store completion values."""
    host = host or auth.get_host()
    return write_cache(host, fetch_completion_values(factory))


def acquire_refresh_lock(host):
    """Acquire a per-host refresh lock, returning its fd or None."""
    os.makedirs(cache_dir(), mode=0o700, exist_ok=True)
    path = lock_path(host)
    try:
        if time.time() - os.path.getmtime(path) > 10 * 60:
            os.unlink(path)
    except (FileNotFoundError, OSError):
        pass
    try:
        return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return None


def release_refresh_lock(host, fd=None):
    if fd is not None:
        os.close(fd)
    try:
        os.unlink(lock_path(host))
    except FileNotFoundError:
        pass


def start_background_refresh(host):
    """Start one quiet refresh process for a stale host cache."""
    lock_fd = acquire_refresh_lock(host)
    if lock_fd is None:
        return False
    os.close(lock_fd)
    env = os.environ.copy()
    env["BELY_HOST"] = host
    try:
        subprocess.Popen(
            [sys.executable, "-m", "bely_cli.shell_completion", "--refresh", host],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        release_refresh_lock(host)
        return False
    return True


def cached_values_for_completion():
    """Return cached values without network access, refreshing stale data asynchronously."""
    try:
        host = auth.get_host()
    except (OSError, ValueError):
        return {}
    data = load_cache(host)
    if not cache_is_fresh(data):
        start_background_refresh(host)
    return data or {}


def detect_shell(shell=None):
    if shell:
        return shell
    detected = os.path.basename(os.environ.get("SHELL", ""))
    if detected not in SHELL_ENV:
        raise ValueError("could not detect Bash or Zsh; use --shell bash or --shell zsh")
    return detected


def rc_path(shell):
    return os.path.expanduser("~/.bashrc" if shell == "bash" else "~/.zshrc")


def completion_block(shell):
    source = SHELL_ENV[shell]
    return (
        f"{BLOCK_START}\n"
        f'eval "$(_BELY_CLI_COMPLETE={source} bely-cli)"\n'
        f"{BLOCK_END}\n"
    )


def install_completion(shell, path=None):
    """Add or replace the marked completion block in a shell rc file."""
    path = path or rc_path(shell)
    try:
        with open(path, "r", encoding="utf-8") as rc_file:
            content = rc_file.read()
    except FileNotFoundError:
        content = ""

    start = content.find(BLOCK_START)
    end = content.find(BLOCK_END, start + len(BLOCK_START)) if start >= 0 else -1
    if start >= 0 and end >= 0:
        end += len(BLOCK_END)
        if end < len(content) and content[end] == "\n":
            end += 1
        content = content[:start] + completion_block(shell) + content[end:]
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        if content:
            content += "\n"
        content += completion_block(shell)

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as rc_file:
        rc_file.write(content)
    return path


def _items(section, incomplete, value_key="name", description_key="description"):
    from click.shell_completion import CompletionItem

    values = cached_values_for_completion().get(section, [])
    incomplete_lower = incomplete.lower()
    return [
        CompletionItem(str(item.get(value_key, "")), help=item.get(description_key) or None)
        for item in values
        if str(item.get(value_key, "")).lower().startswith(incomplete_lower)
    ]


def complete_types(ctx, param, incomplete):
    return _items("types", incomplete)


def complete_templates(ctx, param, incomplete):
    return _items("templates", incomplete)


def complete_systems(ctx, param, incomplete):
    """Complete the final value in a comma-separated system list."""
    prefix, separator, fragment = incomplete.rpartition(",")
    completed_prefix = f"{prefix}," if separator else ""
    selected = {name.strip().lower() for name in prefix.split(",") if name.strip()}
    items = [item for item in _items("systems", fragment.lstrip())
             if item.value.lower() not in selected]
    for item in items:
        item.value = completed_prefix + item.value
    return items


def complete_document_names(ctx, param, incomplete):
    return _items("documents", incomplete, description_key="type")


def complete_document_ids(ctx, param, incomplete):
    return _items("documents", incomplete, value_key="id", description_key="name")


def complete_entry_ids(ctx, param, incomplete):
    """Fetch entry IDs for the selected document without caching them."""
    from click.shell_completion import CompletionItem

    doc_id = ctx.params.get("doc_id")
    doc_name = ctx.params.get("doc_name")
    if doc_id is None and not doc_name:
        return []
    try:
        logbook_api = auth.get_factory().get_logbook_api()
        if doc_id is None:
            document = logbook_api.get_log_document_by_name(name=doc_name)
            doc_id = document.id
        entries = logbook_api.get_log_entries(
            log_document_id=doc_id, load_replies=True)
    except Exception:
        return []

    def flatten(items):
        for entry in items or []:
            yield entry
            yield from flatten(getattr(entry, "log_replies", None))

    results = []
    for entry in flatten(entries):
        entry_id = str(getattr(entry, "log_id", ""))
        if not entry_id.startswith(incomplete):
            continue
        text = (getattr(entry, "log_entry", None) or "").strip().splitlines()
        description = text[0][:60] if text else None
        results.append(CompletionItem(entry_id, help=description))
    return results


def _background_refresh(host):
    try:
        refresh_cache(host)
    finally:
        release_refresh_lock(host)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--refresh":
        _background_refresh(sys.argv[2])
