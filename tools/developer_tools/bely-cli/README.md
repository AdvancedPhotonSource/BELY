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

The token location can be changed with the `token_path` setting; by default it sits beside
the settings file (see [Configuration & environment](#configuration--environment)).

## Output format

A `--format` option controls output, appended to the command:

```bash
bely.py doc list --format json
```

| Value  | Behavior                                              |
|--------|-------------------------------------------------------|
| `text` | Human-readable tables and messages (default)          |
| `json` | Structured JSON — for scripting                       |
| `yaml` | Structured YAML — for scripting                       |

`--format` is given at the end of a command, e.g. `bely.py entry list -n "..." --format yaml`.

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

### `tui` — interactive terminal UIs

#### `bely.py tui lookup`

Interactively browse to find a log entry when you don't already know its document. The TUI
drills down through three levels — **logbook → recent documents → entries** — and then shows
the entry's markdown in a scrollable view. Browsing is read-only and needs no authentication.

```bash
bely.py tui lookup
bely.py tui lookup --limit 50
```

| Option | Description |
|--------|-------------|
| `--limit INTEGER` | Recent documents to load per logbook (default: 100). |

Keys:

| Key | Action |
|-----|--------|
| `Up` / `Down`, `PgUp` / `PgDn` | Move the highlight (or scroll, in the entry view). |
| *type any text* | Incrementally filter the current list (case-insensitive substring). |
| `Backspace` | Edit the filter; with an empty filter, go back one level. |
| `Enter` | Open the highlighted item / drill in. In the entry view, select the entry. |
| `q` | (Entry view only) select the entry. |
| `Esc` | Go back one level; quits from the logbook list. |

On selecting an entry the TUI exits and prints its `doc-id` / `log-id`, plus a ready-to-run
`bely.py entry get` command so you can fetch it:

```
doc-id: 99
log-id: 42
# fetch with: bely.py entry get -d 99 --id 42
```

With `--format json` / `--format yaml` the selected reference is printed as structured data
instead.

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

Open the settings file in your editor. The editor is resolved from `EDITOR`, then the
`editor` setting, then `vi`. The file and directory are created if needed.

#### `bely.py config set FIELD VALUE`

Set a single configuration field. `FIELD` is one of `host`, `user`, `editor`, or
`token_path`.

```bash
bely.py config set user alice
bely.py config set host https://tinkerbox.aps.anl.gov:8181/bely
bely.py config set editor nano
bely.py config set token_path ~/.secrets/bely-token
```

## Configuration & environment

| Location / variable | Purpose |
|---------------------|---------|
| `~/.config/bely/settings.yaml` | Persistent settings (`host`, `user`, `editor`, `token_path`); permissions `0600`. |
| `~/.config/bely/token` | Cached auth token; permissions `0600`. Override with the `token_path` setting. |
| `BELY_SETTINGS_FILE` | Path to the settings file (overrides the default location). The default token sits beside it. |
| `BELY_HOST` | Server URL (overrides the settings file). |
| `BELY_USER` | Username (overrides the settings file). |
| `BELY_PASSWORD` | Password for non-interactive authentication. |
| `EDITOR` | Editor for interactive entries and `config edit`. Falls back to the `editor` setting, then `vi`. |

Settings that hold paths (`token_path`, `setting_override_path`) and the
`BELY_SETTINGS_FILE` env var expand `~` and `$VARS`.

### Shared settings with per-user overrides

When the settings file lives in a shared, read-only location, add a
`setting_override_path` key pointing to a file the user owns. Keys in that file are merged
on top of the shared settings, so each user can override individual values (e.g. `user` or
`token_path`) without write access to the shared file. The override file is plain YAML and
is hand-edited — `setting_override_path` is **not** set via the CLI, and a
`setting_override_path` key inside the override file itself is ignored (no chaining).

Shared `settings.yaml` (read-only). It can still hold per-user paths like `token_path`
because `~` expands to each user's own home directory:

```yaml
host: https://tinkerbox.aps.anl.gov:8181/bely
token_path: ~/.config/bely/token
setting_override_path: ~/.config/bely/overrides.yaml
```

User-owned `~/.config/bely/overrides.yaml` — only the keys that differ per user:

```yaml
user: alice
```

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
bely.py doc list --format json
bely.py entry list -n "Shift Report" --format yaml
```
