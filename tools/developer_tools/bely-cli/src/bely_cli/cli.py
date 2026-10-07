import sys

import click

from .common import FORMATS, format_error_message, set_no_prompt
from .config import VALID_FIELDS
from .commands import (
    cmd_new_doc,
    cmd_delete_doc,
    cmd_list_docs,
    cmd_auth_login,
    cmd_auth_logout,
    cmd_auth_verify,
    cmd_show_config,
    cmd_edit_config,
    cmd_set_config,
)
from .entry import (
    cmd_add_attachment,
    cmd_add_entry,
    cmd_delete_attachment,
    cmd_delete_entry,
    cmd_get_entry,
    cmd_list_attachments,
    cmd_list_entries,
    cmd_reply_entry,
    cmd_update_entry,
)
from .tui import cmd_tui
from . import shell_completion
from .shell_completion import (
    complete_attachment_ids,
    complete_document_ids,
    complete_document_names,
    complete_entry_ids,
    complete_top_level_entry_ids,
    complete_systems,
    complete_templates,
    complete_types,
)


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class AliasHelpGroup(click.Group):
    """Display aliases together instead of as duplicate help rows."""

    def format_commands(self, ctx, formatter):
        grouped = {}
        for name in self.list_commands(ctx):
            command = self.get_command(ctx, name)
            if command is not None and not command.hidden:
                grouped.setdefault(id(command), (command, []))[1].append(name)
        rows = []
        for command, names in grouped.values():
            label = ", ".join(sorted(names))
            rows.append((label, command.get_short_help_str()))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


def format_option(f):
    """Per-command --format option, appended to each leaf command."""
    return click.option(
        "--format", "output_format", type=click.Choice(FORMATS), default="text",
        help="Output format: text, json, yaml (default: text)",
    )(f)


def no_prompt_option(f):
    """Per-command --no-prompt flag: enable non-interactive mode."""
    def _set(ctx, param, value):
        if value:
            set_no_prompt()
        return value
    return click.option(
        "--no-prompt", is_flag=True, default=False,
        expose_value=False, callback=_set,
        help="Non-interactive mode: fail if any prompt would be needed. "
             "Enabled automatically when --file=-.",
    )(f)


def doc_name_option(f):
    return click.option(
        "--doc-name", "-n", default=None, shell_complete=complete_document_names,
        help="Log document name",
    )(f)


def doc_id_option(f):
    return click.option(
        "--doc-id", "-d", default=None, type=int, shell_complete=complete_document_ids,
        help="Log document ID",
    )(f)


def entry_id_option(required=True, help="Log entry ID"):
    def decorator(f):
        return click.option(
            "--id", "entry_id", required=required, default=None, type=int,
            shell_complete=complete_entry_ids, help=help,
        )(f)
    return decorator


def common_options(f):
    """Options shared by all leaf commands (--format and --no-prompt)."""
    return format_option(no_prompt_option(f))


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """BELY logbook CLI"""
    pass


# -- auth --

@cli.group("auth", cls=AliasHelpGroup)
def auth_group():
    """Authentication commands."""
    pass


@auth_group.command("login")
@common_options
def auth_login(output_format):
    """Log in and cache an authentication token."""
    cmd_auth_login(fmt=output_format)


@auth_group.command("logout")
@common_options
def auth_logout(output_format):
    """Log out and remove the cached authentication token."""
    cmd_auth_logout(fmt=output_format)


@auth_group.command("verify")
@common_options
def auth_verify(output_format):
    """Verify the cached authentication token."""
    cmd_auth_verify(fmt=output_format)


# -- doc --

@cli.group("doc", cls=AliasHelpGroup)
def doc_group():
    """Log document commands."""
    pass


@doc_group.command("new")
@click.option("--type", "type_", default=None, shell_complete=complete_types,
              help="Logbook type (e.g. ops, controls)")
@click.option("--name", "-n", default=None, help="Name for the new document")
@click.option("--file", "-f", "file", default=None, type=click.Path(path_type=str, allow_dash=True),
              help="Markdown file for the first log entry")
@click.option("--template", default=None, shell_complete=complete_templates,
              help="Template name to use")
@click.option("--systems", default=None, shell_complete=complete_systems,
              help="Comma-separated system list (e.g. SR,software)")
@click.option("--no-template", is_flag=True, help="Skip template selection")
@click.option("--output", "-o", "output_dir", default=None,
              type=click.Path(path_type=str, file_okay=False),
              help="Directory to write template-generated entry into (default: cwd)")
@click.option("--list-options", "list_options",
              type=click.Choice(["system", "type", "template"]),
              default=None,
              help="List available values for the given option and exit")
@common_options
def doc_new(output_format, **kwargs):
    """Create a new log document."""
    if kwargs.get('file') == '-':
        set_no_prompt()
    cmd_new_doc(fmt=output_format, **kwargs)


@doc_group.command("list")
@click.option("--limit", default=20, type=int, help="Max documents to return (default 20)")
@common_options
def doc_list(output_format, **kwargs):
    """List recent log documents created by you."""
    cmd_list_docs(fmt=output_format, **kwargs)


@doc_group.command("delete")
@doc_name_option
@doc_id_option
@click.option("--yes", is_flag=True, help="Delete without confirmation")
@click.option("--force", is_flag=True, help="Allow deletion when the document contains entries")
@common_options
def doc_delete(output_format, **kwargs):
    """Delete a log document."""
    cmd_delete_doc(fmt=output_format, **kwargs)


doc_group.add_command(doc_list, "ls")
doc_group.add_command(doc_new, "add")
doc_group.add_command(doc_delete, "rm")


# -- entry --

@cli.group("entry", cls=AliasHelpGroup)
def entry_group():
    """Log entry commands."""
    pass


@entry_group.group("attachment", cls=AliasHelpGroup)
def entry_attachment_group():
    """Log entry attachment commands."""
    pass


@entry_attachment_group.command("add")
@doc_name_option
@doc_id_option
@entry_id_option()
@click.option("--file", "-f", required=True, type=click.Path(path_type=str),
              help="File to attach")
@common_options
def entry_attachment_add(output_format, **kwargs):
    """Upload an attachment to an existing log entry."""
    cmd_add_attachment(fmt=output_format, **kwargs)


@entry_attachment_group.command("list")
@doc_name_option
@doc_id_option
@entry_id_option()
@common_options
def entry_attachment_list(output_format, **kwargs):
    """List attachments on a log entry."""
    cmd_list_attachments(fmt=output_format, **kwargs)


@entry_attachment_group.command("delete")
@doc_name_option
@doc_id_option
@entry_id_option()
@click.option(
    "--attachment-id", required=True, type=int,
    shell_complete=complete_attachment_ids, help="Numeric attachment ID",
)
@click.option("--yes", is_flag=True, help="Delete without confirmation")
@common_options
def entry_attachment_delete(output_format, **kwargs):
    """Delete an attachment from a log entry."""
    cmd_delete_attachment(fmt=output_format, **kwargs)


entry_attachment_group.add_command(entry_attachment_list, "ls")
entry_attachment_group.add_command(entry_attachment_delete, "rm")


@entry_group.command("add")
@doc_name_option
@doc_id_option
@click.option("--file", "-f", "file", default=None, type=click.Path(path_type=str, allow_dash=True),
              help="Markdown file with entry content")
@click.option("--text", "-t", default=None, help="Inline text for the entry")
@click.option("--add-attachment", default=None, type=click.Path(path_type=str),
              help="File to attach to the entry")
@common_options
def entry_add(output_format, **kwargs):
    """Add a new log entry to an existing document."""
    if kwargs.get('file') == '-':
        set_no_prompt()
    cmd_add_entry(fmt=output_format, **kwargs)


@entry_group.command("reply")
@doc_name_option
@doc_id_option
@click.option(
    "--id", "entry_id", required=True, type=int,
    shell_complete=complete_top_level_entry_ids, help="Parent log entry ID",
)
@click.option("--file", "-f", "file", default=None, type=click.Path(path_type=str, allow_dash=True),
              help="Markdown file with reply content")
@click.option("--text", "-t", default=None, help="Inline reply text")
@click.option("--add-attachment", default=None, type=click.Path(path_type=str),
              help="File to attach to the reply")
@common_options
def entry_reply(output_format, **kwargs):
    """Reply to an existing log entry."""
    if kwargs.get('file') == '-':
        set_no_prompt()
    cmd_reply_entry(fmt=output_format, **kwargs)


@entry_group.command("update")
@doc_name_option
@doc_id_option
@entry_id_option(required=False, help="Specific log entry ID to update")
@click.option("--file", "-f", "file", default=None, type=click.Path(path_type=str, allow_dash=True),
              help="Markdown file with updated content")
@click.option("--text", "-t", default=None, help="Inline text for the entry")
@click.option("--add-attachment", default=None, type=click.Path(path_type=str),
              help="File to attach to the entry")
@common_options
def entry_update(output_format, **kwargs):
    """Update an existing log entry or reply."""
    if kwargs.get('file') == '-':
        set_no_prompt()
    cmd_update_entry(fmt=output_format, **kwargs)


@entry_group.command("list")
@doc_name_option
@doc_id_option
@click.option("--replies", is_flag=True, help="Include replies and their parent entry IDs")
@common_options
def entry_list(output_format, **kwargs):
    """List entries in a log document."""
    cmd_list_entries(fmt=output_format, **kwargs)


@entry_group.command("get")
@doc_name_option
@doc_id_option
@entry_id_option(required=False, help="Specific log entry ID (default: latest)")
@click.option("--output", "-o", "output_dir", default=None,
              type=click.Path(path_type=str, file_okay=False),
              help="Directory to write <doc_name>_entry_<log_id>.md into (default: cwd)")
@common_options
def entry_get(output_format, **kwargs):
    """Write the markdown of a log entry to a file (latest by default)."""
    cmd_get_entry(fmt=output_format, **kwargs)


@entry_group.command("delete")
@doc_name_option
@doc_id_option
@entry_id_option(help="Log entry or reply ID")
@click.option("--yes", is_flag=True, help="Delete without confirmation")
@common_options
def entry_delete(output_format, **kwargs):
    """Delete a log entry or reply."""
    cmd_delete_entry(fmt=output_format, **kwargs)


entry_group.add_command(entry_list, "ls")
entry_group.add_command(entry_get, "show")
entry_group.add_command(entry_update, "edit")
entry_group.add_command(entry_delete, "rm")


# -- tui --

# Bare `bely-cli tui` launches the full interactive app, so the group itself
# is a leaf invocation when no subcommand is given -- the one place
# --format/--no-prompt sit on a group rather than a leaf command.
@cli.group("tui", cls=AliasHelpGroup, invoke_without_command=True)
@click.option("--limit", default=100, type=int,
              help="Recent documents to load per logbook (default 100)")
@common_options
@click.pass_context
def tui_group(ctx, output_format, **kwargs):
    """Interactive terminal UIs."""
    ctx.obj = {"output_format": output_format, **kwargs}
    if ctx.invoked_subcommand is None:
        cmd_tui(fmt=output_format, mode="app", **kwargs)


@tui_group.command("lookup")
@click.option("--limit", default=100, type=int,
              help="Recent documents to load per logbook (default 100)")
@common_options
def tui_lookup(output_format, **kwargs):
    """Interactively browse logbooks -> documents -> entries to find a log entry."""
    cmd_tui(fmt=output_format, mode="lookup", **kwargs)


# -- shell --

@cli.group("shell")
def shell_group():
    """Shell completion setup and cache management."""
    pass


@shell_group.command("init")
@click.option("--shell", "shell_name", type=click.Choice(["bash", "zsh"]), default=None,
              help="Shell to configure (default: detect from $SHELL)")
@click.option("--print", "print_only", is_flag=True,
              help="Print setup without editing the shell rc file")
@click.option("--yes", is_flag=True, help="Install without confirmation")
def shell_init(shell_name, print_only, yes):
    """Install completion in .bashrc or .zshrc."""
    shell_name = shell_completion.detect_shell(shell_name)
    block = shell_completion.completion_block(shell_name)
    target = shell_completion.rc_path(shell_name)
    click.echo(f"Shell: {shell_name}\nTarget: {target}\n\n{block}", nl=False)
    if print_only:
        return
    if not yes and not click.confirm("Add this completion setup?", default=False):
        click.echo("No changes made.")
        return
    shell_completion.install_completion(shell_name, target)
    click.echo(f"Updated {target}. Restart the shell or source that file to activate completion.")


@shell_group.group("cache")
def shell_cache_group():
    """Manage cached dynamic completion values."""
    pass


@shell_cache_group.command("refresh")
def shell_cache_refresh():
    """Refresh completion values from the configured BELY server."""
    data = shell_completion.refresh_cache()
    click.echo(
        "Completion cache refreshed: "
        f"{len(data.get('types', []))} types, "
        f"{len(data.get('systems', []))} systems, "
        f"{len(data.get('templates', []))} templates, "
        f"{len(data.get('documents', []))} documents."
    )


@shell_cache_group.command("clear")
@click.option("--all-hosts", is_flag=True, help="Clear caches for every configured host")
def shell_cache_clear(all_hosts):
    """Clear cached dynamic completion values."""
    host = None if all_hosts else shell_completion.auth.get_host()
    shell_completion.clear_cache(host)
    click.echo("Completion cache cleared.")


@shell_cache_group.command("status")
def shell_cache_status():
    """Show completion cache location and freshness."""
    host = shell_completion.auth.get_host()
    ttl = shell_completion.config.get_completion_cache_ttl()
    if ttl <= 0:
        click.echo(
            f"Host: {host}\nStatus: disabled (live completion)\n"
            f"Path: {shell_completion.cache_path(host)}"
        )
        return
    data = shell_completion.load_cache(host)
    if data is None:
        click.echo(f"No completion cache for {host}.\nPath: {shell_completion.cache_path(host)}")
        return
    state = "fresh" if shell_completion.cache_is_fresh(data) else "stale"
    refreshed = __import__("datetime").datetime.fromtimestamp(data["refreshed_at"]).astimezone()
    click.echo(
        f"Host: {host}\nPath: {shell_completion.cache_path(host)}\n"
        f"Status: {state}\nTTL: {shell_completion.config.get_setting('completion_cache_ttl') or shell_completion.config.DEFAULT_COMPLETION_CACHE_TTL}\n"
        f"Refreshed: {refreshed.isoformat(timespec='seconds')}\n"
        f"Types: {len(data.get('types', []))}\nSystems: {len(data.get('systems', []))}\n"
        f"Templates: {len(data.get('templates', []))}\nDocuments: {len(data.get('documents', []))}"
    )


# -- config --

@cli.group("config", cls=AliasHelpGroup)
def config_group():
    """Configuration commands."""
    pass


@config_group.command("show")
@common_options
def config_show(output_format):
    """Show current configuration."""
    cmd_show_config(fmt=output_format)


config_group.add_command(config_show, "ls")


@config_group.command("edit")
def config_edit():
    """Open the settings file in your editor."""
    cmd_edit_config()


@config_group.command("set")
@click.argument("field", type=click.Choice(VALID_FIELDS))
@click.argument("value")
@common_options
def config_set(field, value, output_format):
    """Set a configuration field to a value."""
    cmd_set_config(field, value, fmt=output_format)



def main():
    try:
        cli()
    except Exception as e:
        print(f"Error: {format_error_message(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
