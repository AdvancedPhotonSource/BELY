"""Textual screens for `bely-cli tui`.

Split one-screen-per-file so no single module balloons; each screen still
follows the layering discipline of the rest of the tui package (pure logic
lives in ..format / ..data / ..session, screens only render and dispatch).
"""

from rich.table import Table


def rows_table(rows):
    """A two-column Rich grid for [(label, value), ...] metadata rows.

    Shared by every screen that renders a metadata/summary block (browse's
    preview pane, the new-document summary, the config screen).
    """
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column(ratio=1)
    for label, value in rows:
        table.add_row(label, value)
    return table

