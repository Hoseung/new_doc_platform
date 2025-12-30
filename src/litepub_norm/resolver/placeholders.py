"""Placeholder detection and handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PlaceholderKind = Literal["METRIC", "TABLE", "FIGURE"]


@dataclass(frozen=True)
class Placeholder:
    """Placeholder token information."""

    kind: PlaceholderKind
    token: str


# Supported placeholder tokens
PLACEHOLDERS = {
    "[[COMPUTED:METRIC]]": Placeholder(kind="METRIC", token="[[COMPUTED:METRIC]]"),
    "[[COMPUTED:TABLE]]": Placeholder(kind="TABLE", token="[[COMPUTED:TABLE]]"),
    "[[COMPUTED:FIGURE]]": Placeholder(kind="FIGURE", token="[[COMPUTED:FIGURE]]"),
}

# Map from placeholder kind to artifact_type
KIND_TO_ARTIFACT_TYPE = {
    "METRIC": "metric",
    "TABLE": "table",
    "FIGURE": "figure",
}

# Map from artifact_type to placeholder kind
ARTIFACT_TYPE_TO_KIND = {
    "metric": "METRIC",
    "table": "TABLE",
    "figure": "FIGURE",
}


def extract_placeholder_text(block: dict) -> str | None:
    """
    Extract placeholder text from a block if it's placeholder-only.

    A placeholder-only block is a Para containing only a placeholder token.

    Returns:
        The placeholder token string, or None if not a placeholder block.
    """
    if block.get("t") != "Para":
        return None

    contents = block.get("c", [])
    if not contents:
        return None

    # Extract all text from inlines
    text_parts = []
    for inline in contents:
        t = inline.get("t")
        if t == "Str":
            text_parts.append(inline.get("c", ""))
        elif t in ("Space", "SoftBreak"):
            pass  # Ignore whitespace for matching
        else:
            # Other inline types - not a simple placeholder
            return None

    text = "".join(text_parts).strip()
    return text if text else None


def is_placeholder_block(block: dict) -> Placeholder | None:
    """
    Check if a block is a placeholder block.

    Returns:
        The Placeholder if found, None otherwise.
    """
    text = extract_placeholder_text(block)
    if text and text in PLACEHOLDERS:
        return PLACEHOLDERS[text]
    return None


def find_placeholders_in_blocks(
    blocks: list[dict],
) -> list[tuple[Placeholder, int]]:
    """
    Find all placeholder blocks in a list of blocks.

    Returns:
        List of (Placeholder, index) tuples.
    """
    results = []
    for i, block in enumerate(blocks):
        placeholder = is_placeholder_block(block)
        if placeholder:
            results.append((placeholder, i))
    return results
