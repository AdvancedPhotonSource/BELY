"""Split entry markdown into renderable segments: plain markdown vs. images.

No textual/rich import here -- pure data-in/data-out logic so it can be unit
tested without a terminal (see test/test_tui_mdimages.py), matching the style
of format.py. Only markdown_it is used, which textual already depends on.

Server-side, an uploaded image gets a markdown reference of the form
`![name](/log/attachments/<stored>)` appended to the entry body in its own
paragraph (LogAttachmentUtility.java); the web portal rewrites that prefix to
`/api/Downloads/Attachments/<stored>` when rendering. We recognize either
form. Non-image attachments (pdf, etc.) and any other URL are left as plain
markdown links -- textual's Markdown widget already renders those as text.
"""

from markdown_it import MarkdownIt

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")

_ATTACHMENT_PREFIXES = ("/log/attachments/", "/api/Downloads/Attachments/")


def attachment_name(src):
    """The stored filename if src is a renderable BELY attachment reference, else None.

    Rejects external URLs (http://, https://) and non-image attachments (pdf) --
    those stay as ordinary markdown links, never fetched.
    """
    if not src:
        return None
    for prefix in _ATTACHMENT_PREFIXES:
        if src.startswith(prefix):
            name = src[len(prefix):].split("/")[0]
            if name.lower().endswith(IMAGE_EXTENSIONS):
                return name
            return None
    return None


def _image_only_children(children):
    """children of an inline token, if they are exclusively image(s) plus whitespace."""
    images = []
    for child in children:
        if child.type == "image":
            images.append(child)
        elif child.type == "text" and not child.content.strip():
            continue
        elif child.type == "softbreak":
            continue
        else:
            return None
    return images or None


def split_entry_markdown(text):
    """Split entry markdown into ("markdown", str) / ("image", stored_name, alt) segments.

    A paragraph whose inline content is exclusively image(s) (as the server
    appends after an upload) becomes one or more image segments; everything
    else -- including a paragraph that mixes text and an image -- is left as
    markdown, verbatim. Returns a single ("markdown", text) segment when
    nothing is renderable, so the caller can take the cheap unsplit path.
    """
    text = text or ""
    lines = text.splitlines(keepends=True)
    tokens = MarkdownIt("gfm-like").parse(text)

    segments = []
    md_start = 0  # line index where the pending markdown chunk begins

    def flush_markdown(end_line):
        if end_line > md_start:
            chunk = "".join(lines[md_start:end_line])
            if chunk.strip():
                segments.append(("markdown", chunk))

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "paragraph_open" and token.map:
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            images = None
            if inline is not None and inline.type == "inline" and inline.children:
                images = _image_only_children(inline.children)
            if images is not None:
                names = [(attachment_name(img.attrs.get("src", "")), img.content)
                         for img in images]
                if all(name for name, _alt in names):
                    flush_markdown(token.map[0])
                    for name, alt in names:
                        segments.append(("image", name, alt))
                    md_start = token.map[1]
                    i += 3  # paragraph_open, inline, paragraph_close
                    continue
        i += 1

    flush_markdown(len(lines))

    if not segments:
        return [("markdown", text)]
    return segments
