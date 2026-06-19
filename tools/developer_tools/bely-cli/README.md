# bely-cli

A command-line client for the **BELY logbook**. Create log documents, add and update log
entries (from files, inline text, an editor, or with attachments), list and fetch entries,
and manage local configuration.

The published command is `bely.py`.

## Getting started

After loading the `aux` module the command is on your `PATH`:

```bash
module add aux
bely.py -h
```

Every command and group accepts `-h` / `--help`:

```bash
bely.py doc -h
bely.py entry add -h
```

### Set the server host

The CLI needs to know the BELY server URL. If it is not set, commands exit with an error.
The host is resolved in this order:

1. `BELY_HOST` environment variable
2. `host` in `~/.config/bely/settings.yaml`
3. otherwise → error

Set it once with `config set`:

```bash
bely.py config set host https://tinkerbox.aps.anl.gov:8181/bely
```

> A convenience wrapper named `bely` ships in the source directory; it presets
> `BELY_HOST` to `https://tinkerbox.aps.anl.gov:8181/bely` before invoking `bely.py`. The
> examples in this README use `bely.py` directly, so set the host (or export `BELY_HOST`)
> as shown above.

## Authentication

Mutating operations (creating documents, adding/updating entries) require authentication;
lookups (listing types, systems, templates, finding documents) do not.

- **Username** — from `BELY_USER`, else `user` in the settings file, else you are prompted.
- **Password** — from `BELY_PASSWORD` (useful for automation), else you are prompted.

On success a token is cached at `~/.config/bely/token` (permissions `0600`) and reused on
later runs. Expired or invalid tokens are discarded and you re-authenticate automatically.

## Output format

A global `--format` option controls output for all commands:

```bash
bely.py --format json doc list
```

| Value  | Behavior                                              |
|--------|-------------------------------------------------------|
| `text` | Human-readable tables and messages (default)          |
| `json` | Structured JSON — for scripting                       |
| `yaml` | Structured YAML — for scripting                       |

`--format` goes before the command group, e.g. `bely.py --format yaml entry list -n "..."`.

## Commands

### `doc` — log documents

#### `bely.py doc new`

Create a new log document (and optionally its first entry).

| Option | Description |
|--------|-------------|
| `--type TEXT` | Logbook type (e.g. `ops`, `controls`). Prompted if omitted. |
| `-n, --name TEXT` | Name for the new document. Prompted if omitted. |
| `-f, --file TEXT` | Markdown file to use as the first log entry. |
| `--template TEXT` | Template name to use for the first entry. |
| `--systems TEXT` | Comma-separated system list, e.g. `SR,software`. |
| `--no-template` | Skip template selection. Mutually exclusive with `--template`. |
| `-o, --output TEXT` | Directory to write a template-generated entry into (default: cwd). |
| `--list-options {system,type,template}` | List the available values for that option and exit. |

#### `bely.py doc list`

List recent log documents you created, newest first.

| Option | Description |
|--------|-------------|
| `--limit INTEGER` | Maximum documents to return (default: 20). |

### `entry` — log entries

All `entry` commands identify the target document with **either** `-n/--doc-name` **or**
`-d/--doc-id` (provide one).

#### `bely.py entry add`

Add a new entry to an existing document. If none of `--file`, `--text`, or
`--add-attachment` is given, your `$EDITOR` opens for the entry text.

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |
| `-f, --file TEXT` | Markdown file with the entry content. |
| `-t, --text TEXT` | Inline text for the entry. |
| `--add-attachment TEXT` | File to attach to the entry. |

#### `bely.py entry update`

Update an existing entry. With no `--id`, your most recent entry in the document is
updated. If none of `--file`, `--text`, or `--add-attachment` is given, your `$EDITOR`
opens. `--file` and `--text` are mutually exclusive.

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |
| `--id INTEGER` | Specific entry ID to update (default: your most recent entry). |
| `-f, --file TEXT` | Markdown file with the updated content. |
| `-t, --text TEXT` | Inline text for the entry. |
| `--add-attachment TEXT` | File to attach to the entry. |

#### `bely.py entry list`

List the entries in a document (Log ID, date, author, and a snippet of the first line).

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |

#### `bely.py entry get`

Write the markdown of an entry to a file named `<doc_name>_entry_<log_id>.md`.

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |
| `--id INTEGER` | Specific entry ID (default: latest). |
| `-o, --output TEXT` | Directory to write the file into (default: cwd). |

### `config` — local configuration

#### `bely.py config show`

Show the current configuration: values from the settings file and the relevant environment
variables (`BELY_PASSWORD` is masked).

#### `bely.py config edit`

Open `~/.config/bely/settings.yaml` in your `$EDITOR` (defaults to `vi`). The file and
directory are created if needed.

#### `bely.py config set FIELD VALUE`

Set a single configuration field. `FIELD` is one of `host` or `user`.

```bash
bely.py config set user alice
bely.py config set host https://tinkerbox.aps.anl.gov:8181/bely
```

## Configuration & environment

| Location / variable | Purpose |
|---------------------|---------|
| `~/.config/bely/settings.yaml` | Persistent settings (`host`, `user`); permissions `0600`. |
| `~/.config/bely/token` | Cached auth token; permissions `0600`. |
| `BELY_HOST` | Server URL (overrides the settings file). |
| `BELY_USER` | Username (overrides the settings file). |
| `BELY_PASSWORD` | Password for non-interactive authentication. |
| `EDITOR` | Editor used for interactive entries and `config edit` (default: `vi`). |

## Examples

```bash
# One-time setup
bely.py config set host https://tinkerbox.aps.anl.gov:8181/bely
bely.py config set user alice

# Discover available values
bely.py doc new --list-options type
bely.py doc new --list-options system
bely.py doc new --list-options template

# Create a document interactively (prompts for type and name)
bely.py doc new

# Create a document with everything specified, plus a first entry from a file
bely.py doc new --type ops --name "Shift Report" --systems SR,software --file entry.md

# List your recent documents
bely.py doc list --limit 50

# Add an entry — inline text, from a file, or via your editor
bely.py entry add -n "Shift Report" -t "Beam restored after RF trip."
bely.py entry add -n "Shift Report" -f entry.md
bely.py entry add -n "Shift Report"                 # opens $EDITOR

# Attach a file to an entry
bely.py entry add -n "Shift Report" --add-attachment plot.png

# Update your most recent entry, or a specific one
bely.py entry update -n "Shift Report" -t "Corrected: trip was on RF2."
bely.py entry update -n "Shift Report" --id 42 -f revised.md

# List and fetch entries
bely.py entry list -n "Shift Report"
bely.py entry get -n "Shift Report"                 # latest, to cwd
bely.py entry get -d 99 --id 42 -o ~/logs/

# Structured output for scripting
bely.py --format json doc list
bely.py --format yaml entry list -n "Shift Report"
```
