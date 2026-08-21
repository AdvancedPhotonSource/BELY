"""Terminal image widget resolution -- must run before App.run() (see cmd_tui), since detection probes the terminal."""

IMAGE_MODES = ("auto", "off", "tgp", "sixel", "halfcell", "unicode")

# Short description per mode, shown in the config panel's dropdown (configscreen.py).
IMAGE_MODE_HELP = {
    "auto": "autodetect protocol (recommended)",
    "off": "no images, plain link text",
    "tgp": "Kitty Graphics Protocol (kitty, Ghostty, ...)",
    "sixel": "Sixel protocol (xterm, iTerm2, ...)",
    "halfcell": "block-art fallback, higher resolution",
    "unicode": "block-art fallback, lowest resolution",
}


def load_image_widgets():
    """Resolve every image mode to its Textual widget class; {} if textual_image isn't installed."""
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
    """The widget class for `mode`, or None if images are unavailable/off; unrecognized modes fall back to auto."""
    if mode == "off" or not widgets:
        return None
    return widgets.get(mode) or widgets.get("auto")
