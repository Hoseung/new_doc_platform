"""Emitter for figure.binary@v1 payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .pandoc_builders import make_attr, make_inlines_from_text, make_para


def emit_figure(
    image_path: Path,
    meta: dict[str, Any] | None = None,
    semantic_id: str = "",
) -> dict:
    """
    Emit a figure.binary@v1 payload as a Pandoc Figure block.

    Args:
        image_path: Resolved path to the image file.
        meta: Optional sidecar metadata with caption, alt, notes.
        semantic_id: Semantic ID for the figure (used as identifier).

    Returns:
        Pandoc Figure block dict.
    """
    # Extract metadata
    caption_text = ""
    alt_text = ""

    if meta:
        caption_text = meta.get("caption", "")
        alt_text = meta.get("alt", "")

    # Build image inline
    # Image structure: [Attr, [Inline] (alt text), Target]
    # Target is [url, title]
    image_inline = {
        "t": "Image",
        "c": [
            make_attr(),
            make_inlines_from_text(alt_text) if alt_text else [],
            [str(image_path), ""],  # [url, title]
        ],
    }

    # Build caption
    # Caption is: [ShortCaption, [Block]]
    if caption_text:
        caption_blocks = [make_para(make_inlines_from_text(caption_text))]
        caption = [None, caption_blocks]
    else:
        caption = [None, []]

    # Figure structure: [Attr, Caption, [Block]]
    # The content block is typically a Para containing the Image
    figure = {
        "t": "Figure",
        "c": [
            make_attr(identifier=semantic_id, classes=["figure"]),
            caption,
            [make_para([image_inline])],
        ],
    }

    return figure


def emit_figure_as_para(
    image_path: Path,
    meta: dict[str, Any] | None = None,
) -> dict:
    """
    Emit a figure as a simple Para with Image (for simpler output).

    Args:
        image_path: Resolved path to the image file.
        meta: Optional sidecar metadata with caption, alt.

    Returns:
        Pandoc Para block containing the Image.
    """
    alt_text = ""
    if meta:
        alt_text = meta.get("alt", "")

    image_inline = {
        "t": "Image",
        "c": [
            make_attr(),
            make_inlines_from_text(alt_text) if alt_text else [],
            [str(image_path), ""],
        ],
    }

    return make_para([image_inline])
