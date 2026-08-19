"""`bely-cli tui lookup`: interactive Textual browser for logbooks/entries.

`.app` (Textual/rich) is imported lazily inside cmd_tui, not at module scope,
so `bely-cli --help` (which imports this package via cli.py) stays fast.
"""

from .. import auth
from ..common import print_result
from .data import LogbookData
from .format import entry_reference

__all__ = ["cmd_tui", "LogbookData"]


def cmd_tui(limit=100, fmt="text"):
    """Interactively browse logbooks -> documents -> entries to find an entry."""
    import sys

    if not sys.stdout.isatty() or not sys.stdin.isatty():
        raise RuntimeError("the tui requires an interactive terminal.")

    from .app import BelyTuiApp  # lazy: keeps --help fast

    factory = auth.get_factory()
    data = LogbookData(factory.get_logbook_api())

    result = BelyTuiApp(data, limit=limit).run()
    if not result:
        return
    doc, entry = result

    if fmt == "text":
        print(f"doc-id: {doc.id}")
        print(f"log-id: {entry.log_id}")
        print(f"# fetch with: bely-cli entry get -d {doc.id} --id {entry.log_id}")
    else:
        print_result(entry_reference(doc, entry), "", fmt)
