# bely-cli

A command-line client for the **BELY logbook**. Create log documents, add and update log
entries (from files, inline text, an editor, or with attachments), list and fetch entries,
and manage local configuration.

The published command is `bely-cli`.

## Installation

From PyPI:

```bash
pip install bely-cli
```

For development, from this directory:

```bash
uv sync
uv run bely-cli -h
```

`uv run` only works from inside this directory. To get a `bely-cli` on your `$PATH` that
still tracks your local working-tree edits (no `uv run` prefix, usable from anywhere),
install it as an editable uv tool instead:

```bash
uv tool install --editable .
bely-cli -h
```
Re-run that command (add `--force` to overwrite without prompting) any time `pyproject.toml`'s
dependencies change — code edits alone are picked up immediately, but new/changed
dependencies aren't installed into the tool's environment until you reinstall.

For deployment, install the conda package built from `conda-recipe/` (see
`conda-recipe/conda-build.sh`):

```bash
conda install bely-cli -c <channel>
```

To view images inline in `bely-cli tui` (see [Images](#images) below), install the optional
`images` extra — it pulls in Pillow and `textual-image`, which the base install skips:

```bash
pip install 'bely-cli[images]'                  # from PyPI
uv sync --extra images                        # development, via uv run
uv tool install --force --editable '.[images]'  # development, editable tool install
conda install bely-cli textual-image -c <channel>  # deployment
```

## Getting started

Once installed, the command is on your `PATH`:

```bash
bely-cli -h
```

Every command and group accepts `-h` / `--help`:

```bash
bely-cli doc -h
bely-cli entry add -h
```

### Set the server host

The CLI needs to know the BELY server URL. If it is not set, commands exit with an error.
The host is resolved in this order:

1. `BELY_HOST` environment variable
2. `host` in `~/.config/bely/settings.yaml`
3. otherwise → error

Set it once with `config set`:

```bash
bely-cli config set host https://tinkerbox.aps.anl.gov:8181/bely
```

> A convenience wrapper named `bely-cli-test` ships alongside the source; it presets
> `BELY_HOST` to `https://tinkerbox.aps.anl.gov:8181/bely` before invoking `bely-cli`. The
> examples in this README use `bely-cli` directly, so set the host (or export `BELY_HOST`)
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
bely-cli doc list --format json
```

| Value  | Behavior                                              |
|--------|-------------------------------------------------------|
| `text` | Human-readable tables and messages (default)          |
| `json` | Structured JSON — for scripting                       |
| `yaml` | Structured YAML — for scripting                       |

`--format` is given at the end of a command, e.g. `bely-cli entry list -n "..." --format yaml`.

## Commands

### `doc` — log documents

#### `bely-cli doc new`

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

#### `bely-cli doc list`

List recent log documents you created, newest first.

| Option | Description |
|--------|-------------|
| `--limit INTEGER` | Maximum documents to return (default: 20). |

### `tui` — interactive terminal UIs

#### `bely-cli tui`

Launches the full interactive app, covering the same operations as the flag-driven
commands: browsing, creating documents, adding/updating entries, and viewing or editing
configuration. There's no separate menu screen — it opens straight on the list of
logbooks, the same drill-down `tui lookup` uses, just not read-only.

```bash
bely-cli tui
bely-cli tui --limit 50
```

| Option | Description |
|--------|-------------|
| `--limit INTEGER` | Recent documents to load per logbook (default: 100). |

Browsing needs no authentication. `Enter` on an entry just keeps it in the preview
instead of exiting, and `Esc` at the logbook list does nothing (there's nothing above it to
pop back to) — press `q` to quit. A few keys are available once you've drilled in:

| Key | Level | Action |
|-----|-------|--------|
| `d` | Logbook, document | Create a new document — see "New document" below. Prefilled with the current logbook if you drilled into one. |
| `n` | Document, entry | Add a new entry to the current document. |
| `u` | Entry | Update the highlighted entry. |

`n`/`u`/`d` all open a mutation flow (the entry composer, or the new-document form
below), which is the point where the app authenticates if it hasn't already (see
"Authentication" below).

**Command palette**

Press `ctrl+p` for everything that isn't tied to the current logbook/document — the
equivalent of Home's old menu items, plus what Textual provides by default:

| Command | Action |
|---------|--------|
| Configuration | Opens the configuration dialog — equivalent of `config show` / `config set` / `config edit`. |
| My documents | Opens a browse starting at your recently modified documents — equivalent of `doc list`. `Esc` pops back to wherever you opened it from. |
| Log in | Authenticate now instead of waiting for the first mutation. |
| Refresh cache | Discard all cached logbook data so the next view re-fetches from the server. |
| Theme | Built-in: change the app's color theme; the choice is saved as the `theme` setting and reused on the next launch. |
| Quit | Built-in: exit the app. |

**Entry composer**

A Markdown-aware `TextArea` for the entry body, an optional attachment path, and three
buttons (`Tab`/arrows move focus between the fields and buttons; `Enter` presses the
focused button):

| Button | Action |
|--------|--------|
| Save  `^S` | Save (and upload the attachment, if a path was entered). Also `ctrl+s` from anywhere in the dialog. |
| Edit in $EDITOR | Suspend the TUI and open the buffer in `$EDITOR`; the edited text comes back into the `TextArea`. |
| Cancel  `Esc` | Cancel; asks for confirmation first if the buffer or attachment has unsaved changes. Also `Esc` from anywhere in the dialog. |

An empty new entry is skipped rather than saved, matching `entry add`'s behavior.

**New document**

Mirrors `doc new`: a name field, plus buttons that open pickers for type, systems, and
template:

| Button | Action |
|--------|--------|
| Type… | Pick the logbook type. |
| Systems… | Pick systems (multi-select — `space` toggles, `Enter`/Confirm button confirms). |
| Template… | Pick a template, or "(no template)" to skip. |
| Create  `^S` | Create the document. Also `ctrl+s` from anywhere in the dialog. |
| Cancel  `Esc` | Cancel. Also `Esc` from anywhere in the dialog. |

After creating, it reproduces `doc new`'s post-create prompts: if the template already
generated an entry it offers to edit it, otherwise it offers to create one — both open the
same entry composer.

**Configuration**

Opened from the command palette. Mirrors `config show` / `config set` / `config edit`: one
field per setting (a dropdown for `images`, a text input for everything else), prefilled
from `settings.yaml`, alongside a summary of the current settings and any
environment-variable overrides.

| Button | Action |
|--------|--------|
| Save  `^S` | Save changed fields (same effect as `config set FIELD VALUE`). Also `ctrl+s` from anywhere in the dialog. |
| Edit file | Suspend the TUI and open the settings file in `$EDITOR`, then reload. |
| Reload | Reload from disk, discarding unsaved edits in the form. |
| Close  `Esc` | Close the dialog. Also `Esc` from anywhere in the dialog. |

A field whose effective value comes from an environment variable (`BELY_HOST`, `BELY_USER`,
`EDITOR`) shows that in its placeholder, and saving it warns that the env var will keep
overriding it.

**Authentication**

Browsing needs no login. The first time you add or update an entry, create a document, or
save a config change, the app looks for the token the CLI already caches (see
[Authentication](#authentication) above) and reuses it silently if it's valid — so if you've
already run an authenticated `bely-cli` command, or a previous `tui` session, you won't be
prompted again. Otherwise a login modal appears (username, password, and `Log in`/`Cancel`
buttons — `ctrl+s` also submits, `Esc` also cancels); a successful login is cached the same
way the CLI caches it, shared by later `bely-cli` commands and TUI sessions alike.

#### `bely-cli tui lookup`

Interactively browse to find a log entry when you don't already know its document. The TUI
(built on [Textual](https://textual.textualize.io/)) drills down through three levels —
**logbook → recent documents → entries**. Browsing is read-only and needs no authentication.

All three levels render as full-width, aligned tables (rows stay in API order, not sorted):

| Level | Columns |
|-------|---------|
| Logbook | Name, Display, Description |
| Document | Name, Description, Systems, Owner, Modified |
| Entry | Date, Author, Entry (a snippet of the first line) — replies render as indented rows beneath their parent, expanded by default |

Press `i` at the logbook/document levels to open a side info panel with a few extra fields
for the highlighted row (it splits the table's width; `i` again closes it). Entries always
show a preview pane alongside the table — the entry body rendered as markdown (headings,
lists, tables, and syntax-highlighted code), since the row itself is just a one-line
snippet.

```bash
bely-cli tui lookup
bely-cli tui lookup --limit 50
```

| Option | Description |
|--------|-------------|
| `--limit INTEGER` | Recent documents to load per logbook (default: 100). |

The info panel (`i`, logbook/document levels only) shows, depending on the level: for a logbook,
its name, display name(s), and description; for a document, its description, logbook types,
systems, owner, and creation/modification info. The entry preview (always shown at that level)
has author and modification info, reply/reaction counts, and attachments (fetched lazily as
you highlight each entry) — and, for a reply, which entry it's a reply to.

Keys:

The footer at the bottom of the screen only ever shows the keys that apply to the level you're
on — `i` disappears once you drill into entries, and `s` / `y` / `e` / `f` / `t` only appear there.

| Key | Action |
|-----|--------|
| `Up` / `Down`, `PgUp` / `PgDn` | Move the highlight; the preview/info panel follows. |
| `/` | Reveal and focus the filter box; incrementally filters the current table (case-insensitive substring, matched against the entry text — not the reply tree's glyphs or reply count). |
| `Enter` | In the filter box, return focus to the table. Elsewhere, drill into the highlighted row, or select the entry at the entries level. |
| `Esc` / `Backspace` | Go back one level (from the table); does nothing at the logbook list — press `q` to quit. In the filter box, `Esc` returns focus to the table. |
| `d` | Logbook/document levels only: create a new document (see `bely-cli tui`'s "New document" above) — a mutation, so this is where the app authenticates if it hasn't already. |
| `s` | Entries level only: save the highlighted entry's markdown to a file in the current directory. |
| `y` | Entries level only: copy a `bely-cli entry get` reference for the highlighted entry to the clipboard. |
| `e` | Entries level only: open the highlighted entry in `$EDITOR`; if you change it, offers to save the result back to the server (a mutation, so this is where the app authenticates if it hasn't already). |
| `t` | Entries level only: collapse/expand the reply thread under the highlighted entry (or its parent, if the highlight is on a reply). Replies start expanded. |
| `i` | Logbook/document levels only: toggle the side info panel. |
| `f` | Entries level only: toggle the table to widen the preview pane. |
| `r` | Refresh the current level, bypassing the in-session cache. Collapsed threads stay collapsed. |
| `q` | Quit without selecting. |

Replies only ever nest one level deep — the server doesn't return replies-to-replies — and
`n` on a highlighted reply adds a new top-level entry, not a reply to that reply (there's no
API for that yet).

On selecting an entry the TUI exits and prints its `doc-id` / `log-id`, plus a ready-to-run
`bely-cli entry get` command so you can fetch it:

```
doc-id: 99
log-id: 42
# fetch with: bely-cli entry get -d 99 --id 42
```

With `--format json` / `--format yaml` the selected reference is printed as structured data
instead.

#### Images

When an entry's markdown references an image attachment, the preview (in both `tui` and
`tui lookup`) renders it inline as an actual picture if your terminal and the `images`
setting support it, instead of a plain link.

Requires the optional `images` extra (see [Installation](#installation)) and a terminal with
a graphics protocol. Controlled by the `images` setting, one of:

| Mode | Renders via |
|------|-------------|
| `auto` (default) | Autodetects the terminal's protocol — recommended. |
| `off` | No images; the old link-text preview. |
| `tgp` | Kitty Graphics Protocol (kitty, Ghostty, WezTerm, Konsole, ...). |
| `sixel` | Sixel (xterm, foot, iTerm2, WezTerm, Windows Terminal ≥1.22, ...). |
| `halfcell` | Block-art fallback (higher resolution), no graphics protocol needed. |
| `unicode` | Block-art fallback (lowest resolution), works in any terminal. |

```bash
bely-cli config set images sixel
```
or from the TUI's Configuration dialog (`ctrl+p` → Configuration) — the `images` field is a
dropdown listing all six modes with a short description of each. A mode change there takes
effect on the very next entry you preview, no restart needed — unless the TUI was launched
with `images: off` (which skips the terminal graphics probe at startup entirely), in which
case it warns that a restart is required.

If the extra isn't installed, entries with images show a one-time notice suggesting
`pip install 'bely-cli[images]'`; the link-text preview otherwise behaves exactly as before.
Only BELY attachment images (`![...](/log/attachments/...)`) are ever fetched — external
`http(s)://` image URLs in entry markdown are left as plain links, never downloaded.

**tmux**: `tgp` does not work through tmux — `textual-image` writes Kitty's raw escape
sequences directly to the terminal without tmux's DCS passthrough wrapping, so tmux can't
forward them regardless of configuration. `sixel` does work, but needs tmux ≥3.3 with:
```tmux
set -g allow-passthrough on
set -ga terminal-features ',*:RGB:sixel'
```
`halfcell` needs no tmux configuration at all and is the more reliable choice inside tmux.

### `entry` — log entries

All `entry` commands identify the target document with **either** `-n/--doc-name` **or**
`-d/--doc-id` (provide one).

#### `bely-cli entry add`

Add a new entry to an existing document. If none of `--file`, `--text`, or
`--add-attachment` is given, your `$EDITOR` opens for the entry text.

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |
| `-f, --file TEXT` | Markdown file with the entry content. |
| `-t, --text TEXT` | Inline text for the entry. |
| `--add-attachment TEXT` | File to attach to the entry. |

#### `bely-cli entry update`

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

#### `bely-cli entry list`

List the entries in a document (Log ID, date, author, and a snippet of the first line).

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |

#### `bely-cli entry get`

Write the markdown of an entry to a file named `<doc_name>_entry_<log_id>.md`.

| Option | Description |
|--------|-------------|
| `-n, --doc-name TEXT` | Document name. |
| `-d, --doc-id INTEGER` | Document ID. |
| `--id INTEGER` | Specific entry ID (default: latest). |
| `-o, --output TEXT` | Directory to write the file into (default: cwd). |

### `config` — local configuration

#### `bely-cli config show`

Show the current configuration: values from the settings file and the relevant environment
variables (`BELY_PASSWORD` is masked).

#### `bely-cli config edit`

Open the settings file in your editor. The editor is resolved from `EDITOR`, then the
`editor` setting, then `vi`. The file and directory are created if needed.

#### `bely-cli config set FIELD VALUE`

Set a single configuration field. `FIELD` is one of `host`, `user`, `editor`,
`token_path`, `theme`, or `images`.

```bash
bely-cli config set user alice
bely-cli config set host https://tinkerbox.aps.anl.gov:8181/bely
bely-cli config set editor nano
bely-cli config set token_path ~/.secrets/bely-token
bely-cli config set theme nord
bely-cli config set images sixel
```

## Configuration & environment

| Location / variable | Purpose |
|---------------------|---------|
| `~/.config/bely/settings.yaml` | Persistent settings (`host`, `user`, `editor`, `token_path`, `theme`, `images`); permissions `0600`. |
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
bely-cli config set host https://tinkerbox.aps.anl.gov:8181/bely
bely-cli config set user alice

# Discover available values
bely-cli doc new --list-options type
bely-cli doc new --list-options system
bely-cli doc new --list-options template

# Create a document interactively (prompts for type and name)
bely-cli doc new

# Create a document with everything specified, plus a first entry from a file
bely-cli doc new --type ops --name "Shift Report" --systems SR,software --file entry.md

# List your recent documents
bely-cli doc list --limit 50

# Add an entry — inline text, from a file, or via your editor
bely-cli entry add -n "Shift Report" -t "Beam restored after RF trip."
bely-cli entry add -n "Shift Report" -f entry.md
bely-cli entry add -n "Shift Report"                 # opens $EDITOR

# Attach a file to an entry
bely-cli entry add -n "Shift Report" --add-attachment plot.png

# Update your most recent entry, or a specific one
bely-cli entry update -n "Shift Report" -t "Corrected: trip was on RF2."
bely-cli entry update -n "Shift Report" --id 42 -f revised.md

# List and fetch entries
bely-cli entry list -n "Shift Report"
bely-cli entry get -n "Shift Report"                 # latest, to cwd
bely-cli entry get -d 99 --id 42 -o ~/logs/

# Structured output for scripting
bely-cli doc list --format json
bely-cli entry list -n "Shift Report" --format yaml
```
