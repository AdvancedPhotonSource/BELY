#!/C2/conda/envs/bely/bin/python

import sys

import click

from common import FORMATS, set_no_prompt
from config import VALID_FIELDS
from commands import (
    cmd_new_doc,
    cmd_list_docs,
    cmd_show_config,
    cmd_edit_config,
    cmd_set_config,
)
from entry import (
    cmd_add_entry,
    cmd_get_entry,
    cmd_list_entries,
    cmd_update_entry,
)
from tui import cmd_tui


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


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


def common_options(f):
    """Options shared by all leaf commands (--format and --no-prompt)."""
    return format_option(no_prompt_option(f))


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """BELY logbook CLI"""
    pass


# -- doc --

@cli.group("doc")
def doc_group():
    """Log document commands."""
    pass


@doc_group.command("new")
@click.option("--type", "type_", default=None, help="Logbook type (e.g. ops, controls)")
@click.option("--name", "-n", default=None, help="Name for the new document")
@click.option("--file", "-f", "file", default=None, help="Markdown file for the first log entry")
@click.option("--template", default=None, help="Template name to use")
@click.option("--systems", default=None, help="Comma-separated system list (e.g. SR,software)")
@click.option("--no-template", is_flag=True, help="Skip template selection")
@click.option("--output", "-o", "output_dir", default=None,
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


# -- entry --

@cli.group("entry")
def entry_group():
    """Log entry commands."""
    pass


@entry_group.command("add")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@click.option("--file", "-f", "file", default=None, help="Markdown file with entry content")
@click.option("--text", "-t", default=None, help="Inline text for the entry")
@click.option("--add-attachment", default=None, help="File to attach to the entry")
@common_options
def entry_add(output_format, **kwargs):
    """Add a new log entry to an existing document."""
    if kwargs.get('file') == '-':
        set_no_prompt()
    cmd_add_entry(fmt=output_format, **kwargs)


@entry_group.command("update")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@click.option("--id", "entry_id", default=None, type=int, help="Specific log entry ID to update")
@click.option("--file", "-f", "file", default=None, help="Markdown file with updated content")
@click.option("--text", "-t", default=None, help="Inline text for the entry")
@click.option("--add-attachment", default=None, help="File to attach to the entry")
@common_options
def entry_update(output_format, **kwargs):
    """Update an existing log entry."""
    if kwargs.get('file') == '-':
        set_no_prompt()
    cmd_update_entry(fmt=output_format, **kwargs)


@entry_group.command("list")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@common_options
def entry_list(output_format, **kwargs):
    """List entries in a log document."""
    cmd_list_entries(fmt=output_format, **kwargs)


@entry_group.command("get")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@click.option("--id", "entry_id", default=None, type=int, help="Specific log entry ID (default: latest)")
@click.option("--output", "-o", "output_dir", default=None,
              help="Directory to write <doc_name>_entry_<log_id>.md into (default: cwd)")
@common_options
def entry_get(output_format, **kwargs):
    """Write the markdown of a log entry to a file (latest by default)."""
    cmd_get_entry(fmt=output_format, **kwargs)


# -- tui --

@cli.group("tui")
def tui_group():
    """Interactive terminal UIs."""
    pass


@tui_group.command("lookup")
@click.option("--limit", default=100, type=int,
              help="Recent documents to load per logbook (default 100)")
@common_options
def tui_lookup(output_format, **kwargs):
    """Interactively browse logbooks -> documents -> entries to find a log entry."""
    cmd_tui(fmt=output_format, **kwargs)


# -- config --

@cli.group("config")
def config_group():
    """Configuration commands."""
    pass


@config_group.command("show")
@common_options
def config_show(output_format):
    """Show current configuration."""
    cmd_show_config(fmt=output_format)


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



if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
