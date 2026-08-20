"""Terminal image widget resolution for the entry preview.

`textual_image` is an optional extra (`bely-cli[images]`): base installs don't
pay for Pillow, and the TUI degrades to today's plain-markdown preview when
it isn't installed. Its protocol auto-detection queries the terminal, which
does not work once the Textual app has started -- so `load_image_widgets()`
must be called before `App.run()` (see tui/__init__.py's cmd_tui), not from
inside a screen or worker.
"""

IMAGE_MODES = ("auto", "off", "tgp", "sixel", "halfcell", "unicode")

# Short description per mode, shown in the TUI configuration panel's Select
# dropdown (see tui/screens/configscreen.py) and documented in README.md.
IMAGE_MODE_HELP = {
    "auto": "autodetect protocol (recommended)",
    "off": "no images, plain link text",
    "tgp": "Kitty Graphics Protocol (kitty, Ghostty, ...)",
    "sixel": "Sixel protocol (xterm, iTerm2, ...)",
    "halfcell": "block-art fallback, higher resolution",
    "unicode": "block-art fallback, lowest resolution",
}


def load_image_widgets():
    """Resolve every image mode to its Textual widget class.

    Returns {} if textual_image isn't installed. Resolving every mode up
    front (not just the one currently configured) is what lets the
    configuration screen switch modes without restarting the TUI.
    """
    try:
        from textual_image.widget import (
            HalfcellImage, Image, SixelImage, TGPImage, UnicodeImage,
        )
    except ImportError:
        return {}

    return {
        "auto": Image,
        "tgp": TGPImage,
        "sixel": SixelImage,
        "halfcell": HalfcellImage,
        "unicode": UnicodeImage,
    }


def widget_for(widgets, mode):
    """The widget class for `mode`, or None if images are unavailable/off.

    Falls back to "auto" for an unset or unrecognized mode (e.g. a settings
    file from a version with a smaller IMAGE_MODES set).
    """
    if mode == "off" or not widgets:
        return None
    return widgets.get(mode) or widgets.get("auto")
