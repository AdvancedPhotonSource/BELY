"""`bely-cli tui` / `bely-cli tui lookup`: the Textual app entry point.

`.app` (Textual/rich) and `.session` are imported lazily inside cmd_tui, not
at module scope, so `bely-cli --help` (which imports this package via
cli.py) stays fast.
"""

from .. import auth
from ..common import is_no_prompt, print_result
from .data import LogbookData
from .format import entry_reference

__all__ = ["cmd_tui", "LogbookData"]


def cmd_tui(limit=100, fmt="text", mode="app"):
    """Launch the TUI: the full app (mode="app") or the browse-and-exit lookup."""
    import sys

    if not sys.stdout.isatty() or not sys.stdin.isatty():
        raise RuntimeError("the tui requires an interactive terminal.")
    if is_no_prompt():
        raise RuntimeError("the tui cannot run with --no-prompt.")

    from .. import config
    from .app import BelyTuiApp  # lazy: keeps --help fast
    from .images import load_image_widgets
    from .session import TuiSession

    factory = auth.get_factory()
    session = TuiSession(factory)

    # Must probe the terminal before the Textual app takes over stdin/stdout; "off" skips the probe entirely.
    image_widgets = {} if config.get_setting("images") == "off" else load_image_widgets()

    result = BelyTuiApp(session, limit=limit, mode=mode, image_widgets=image_widgets).run()
    if not result:
        return
    doc, entry = result

    if fmt == "text":
        print(f"doc-id: {doc.id}")
        print(f"log-id: {entry.log_id}")
        print(f"# fetch with: bely-cli entry get -d {doc.id} --id {entry.log_id}")
    else:
        print_result(entry_reference(doc, entry), "", fmt)
