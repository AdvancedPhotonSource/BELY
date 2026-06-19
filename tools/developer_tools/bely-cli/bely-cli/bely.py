#!/C2/conda/envs/bely/bin/python

import click

from common import FORMATS
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


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--format", "output_format", type=click.Choice(FORMATS),
              default="text", help="Output format (default: text)")
@click.pass_context
def cli(ctx, output_format):
    """BELY logbook CLI"""
    ctx.ensure_object(dict)
    ctx.obj["format"] = output_format


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
@click.pass_context
def doc_new(ctx, **kwargs):
    """Create a new log document."""
    cmd_new_doc(fmt=ctx.obj["format"], **kwargs)


@doc_group.command("list")
@click.option("--limit", default=20, type=int, help="Max documents to return (default 20)")
@click.pass_context
def doc_list(ctx, **kwargs):
    """List recent log documents created by you."""
    cmd_list_docs(fmt=ctx.obj["format"], **kwargs)


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
@click.pass_context
def entry_add(ctx, **kwargs):
    """Add a new log entry to an existing document."""
    cmd_add_entry(fmt=ctx.obj["format"], **kwargs)


@entry_group.command("update")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@click.option("--id", "entry_id", default=None, type=int, help="Specific log entry ID to update")
@click.option("--file", "-f", "file", default=None, help="Markdown file with updated content")
@click.option("--text", "-t", default=None, help="Inline text for the entry")
@click.option("--add-attachment", default=None, help="File to attach to the entry")
@click.pass_context
def entry_update(ctx, **kwargs):
    """Update an existing log entry."""
    cmd_update_entry(fmt=ctx.obj["format"], **kwargs)


@entry_group.command("list")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@click.pass_context
def entry_list(ctx, **kwargs):
    """List entries in a log document."""
    cmd_list_entries(fmt=ctx.obj["format"], **kwargs)


@entry_group.command("get")
@click.option("--doc-name", "-n", default=None, help="Log document name")
@click.option("--doc-id", "-d", default=None, type=int, help="Log document ID")
@click.option("--id", "entry_id", default=None, type=int, help="Specific log entry ID (default: latest)")
@click.option("--output", "-o", "output_dir", default=None,
              help="Directory to write <doc_name>_entry_<log_id>.md into (default: cwd)")
@click.pass_context
def entry_get(ctx, **kwargs):
    """Write the markdown of a log entry to a file (latest by default)."""
    cmd_get_entry(fmt=ctx.obj["format"], **kwargs)


# -- config --

@cli.group("config")
def config_group():
    """Configuration commands."""
    pass


@config_group.command("show")
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    cmd_show_config(fmt=ctx.obj["format"])


@config_group.command("edit")
def config_edit():
    """Open the settings file in your editor."""
    cmd_edit_config()


@config_group.command("set")
@click.argument("field", type=click.Choice(VALID_FIELDS))
@click.argument("value")
@click.pass_context
def config_set(ctx, field, value):
    """Set a configuration field to a value."""
    cmd_set_config(field, value, fmt=ctx.obj["format"])



if __name__ == "__main__":
    cli()
