"""Sectioning utilities for appendix and heading management."""

from __future__ import annotations

from typing import Any
import re


def slugify(text: str) -> str:
    """
    Convert text to a safe anchor slug.

    - Lowercase
    - Replace spaces with hyphens
    - Remove non-alphanumeric characters except hyphens
    """
    slug = text.lower().strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)  # Collapse multiple hyphens
    return slug.strip("-")


def make_anchor_id(semantic_id: str, prefix: str = "appendix") -> str:
    """
    Create a deterministic anchor ID from a semantic ID.

    Args:
        semantic_id: The semantic ID of the wrapper
        prefix: Anchor prefix (e.g., "appendix")

    Returns:
        Safe anchor ID like "appendix-my-semantic-id"
    """
    slug = slugify(semantic_id)
    return f"{prefix}-{slug}"


def make_header(level: int, text: str, anchor_id: str | None = None) -> dict[str, Any]:
    """
    Create a Pandoc Header block.

    Args:
        level: Header level (1-6)
        text: Header text
        anchor_id: Optional anchor ID

    Returns:
        Pandoc Header block
    """
    attr = [anchor_id or "", [], []]
    inlines = [{"t": "Str", "c": text}]
    return {"t": "Header", "c": [level, attr, inlines]}


def find_appendix_index(blocks: list[dict[str, Any]], title: str = "Appendix") -> int | None:
    """
    Find the index of an existing Appendix section.

    Args:
        blocks: List of Pandoc blocks
        title: Expected appendix title

    Returns:
        Index of appendix header, or None if not found
    """
    for i, block in enumerate(blocks):
        if block.get("t") != "Header":
            continue

        content = block.get("c", [])
        if not isinstance(content, list) or len(content) < 3:
            continue

        inlines = content[2]
        header_text = extract_text_from_inlines(inlines)
        if header_text.strip().lower() == title.lower():
            return i

    return None


def extract_text_from_inlines(inlines: list[Any]) -> str:
    """Extract plain text from inline elements."""
    if not isinstance(inlines, list):
        return ""

    parts = []
    for inline in inlines:
        if not isinstance(inline, dict):
            continue

        inline_type = inline.get("t", "")
        content = inline.get("c")

        if inline_type == "Str" and isinstance(content, str):
            parts.append(content)
        elif inline_type == "Space":
            parts.append(" ")
        elif inline_type in ("Emph", "Strong", "Underline"):
            if isinstance(content, list):
                parts.append(extract_text_from_inlines(content))

    return "".join(parts)


def ensure_appendix_section(
    ast: dict[str, Any],
    title: str = "Appendix",
    anchor_prefix: str = "appendix",
) -> tuple[dict[str, Any], int, str]:
    """
    Ensure an Appendix section exists in the AST.

    Creates one at the end if it doesn't exist.

    Args:
        ast: Pandoc AST (will be modified in place)
        title: Appendix section title
        anchor_prefix: Prefix for anchor ID

    Returns:
        Tuple of (ast, appendix_block_index, anchor_id)
    """
    blocks = ast.get("blocks", [])
    anchor_id = f"{anchor_prefix}-section"

    existing_idx = find_appendix_index(blocks, title)
    if existing_idx is not None:
        # Return existing appendix
        header = blocks[existing_idx]
        content = header.get("c", [])
        if len(content) >= 1:
            existing_anchor = content[0][0] if content[0] else anchor_id
            return ast, existing_idx, existing_anchor
        return ast, existing_idx, anchor_id

    # Create new appendix section
    appendix_header = make_header(1, title, anchor_id)
    blocks.append(appendix_header)

    return ast, len(blocks) - 1, anchor_id


def append_to_appendix(
    ast: dict[str, Any],
    appendix_index: int,
    subsection_title: str,
    content_blocks: list[dict[str, Any]],
    anchor_id: str,
) -> None:
    """
    Append a subsection to the appendix.

    Args:
        ast: Pandoc AST (will be modified in place)
        appendix_index: Index of the appendix header
        subsection_title: Title for the subsection
        content_blocks: Blocks to add
        anchor_id: Anchor ID for the subsection
    """
    blocks = ast.get("blocks", [])

    # Create subsection header (level 2)
    subsection_header = make_header(2, subsection_title, anchor_id)

    # Find insertion point (after appendix header and any existing subsections)
    insert_at = len(blocks)  # Default: end of document

    # Append at end of document
    blocks.append(subsection_header)
    blocks.extend(content_blocks)


def make_stub_para(text: str, link_text: str | None = None, link_target: str | None = None) -> dict[str, Any]:
    """
    Create a stub paragraph with optional link.

    Args:
        text: Main text before link
        link_text: Text for the link
        link_target: Link target (anchor or URL)

    Returns:
        Pandoc Para block
    """
    inlines = [{"t": "Str", "c": text}]

    if link_text and link_target:
        inlines.append({"t": "Space"})
        inlines.append({
            "t": "Link",
            "c": [
                ["", [], []],
                [{"t": "Str", "c": link_text}],
                [link_target, ""],
            ],
        })

    return {"t": "Para", "c": inlines}
