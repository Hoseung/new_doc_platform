"""Validator for table.pandoc.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from ..errors import ValidationError
from ..config import ResolutionConfig


# Inline types that are allowed in safe mode
SAFE_INLINE_TYPES = {
    "Str",
    "Space",
    "SoftBreak",
    "LineBreak",
    "Emph",
    "Strong",
    "Strikeout",
    "Superscript",
    "Subscript",
    "SmallCaps",
    "Code",
    "Math",
    "Link",
    "Image",
    "Span",
    "Quoted",
    "Note",
}

# Block types that are allowed in table cells
SAFE_BLOCK_TYPES = {
    "Plain",
    "Para",
    "BulletList",
    "OrderedList",
    "DefinitionList",
    "Header",
    "HorizontalRule",
    "LineBlock",
}

# Disallowed types
UNSAFE_TYPES = {"RawInline", "RawBlock", "Div"}


def _validate_inlines(
    inlines: list[dict],
    semantic_id: str,
    allow_raw: bool,
) -> None:
    """Validate inline content for safety."""
    for inline in inlines:
        t = inline.get("t", "")

        if t in UNSAFE_TYPES and not allow_raw:
            if t == "Div":
                raise ValidationError(
                    f"Div blocks not allowed in table payload",
                    semantic_id=semantic_id,
                )
            raise ValidationError(
                f"Raw content ({t}) not allowed in table payload",
                semantic_id=semantic_id,
            )

        # Recursively check nested content
        c = inline.get("c")
        if isinstance(c, list):
            # Some inline types have nested inlines
            if t in ("Emph", "Strong", "Strikeout", "Superscript", "Subscript",
                     "SmallCaps", "Span", "Quoted"):
                if t == "Span":
                    # Span: [Attr, [Inline]]
                    if len(c) >= 2 and isinstance(c[1], list):
                        _validate_inlines(c[1], semantic_id, allow_raw)
                elif t == "Quoted":
                    # Quoted: [QuoteType, [Inline]]
                    if len(c) >= 2 and isinstance(c[1], list):
                        _validate_inlines(c[1], semantic_id, allow_raw)
                else:
                    _validate_inlines(c, semantic_id, allow_raw)
            elif t == "Link" or t == "Image":
                # Link/Image: [Attr, [Inline], Target]
                if len(c) >= 2 and isinstance(c[1], list):
                    _validate_inlines(c[1], semantic_id, allow_raw)


def _validate_blocks(
    blocks: list[dict],
    semantic_id: str,
    allow_raw: bool,
) -> None:
    """Validate block content for safety."""
    for block in blocks:
        t = block.get("t", "")

        if t in UNSAFE_TYPES and not allow_raw:
            if t == "Div":
                raise ValidationError(
                    f"Div blocks not allowed in table payload",
                    semantic_id=semantic_id,
                )
            raise ValidationError(
                f"Raw content ({t}) not allowed in table payload",
                semantic_id=semantic_id,
            )

        # Check inline content within blocks
        c = block.get("c")
        if t in ("Plain", "Para") and isinstance(c, list):
            _validate_inlines(c, semantic_id, allow_raw)


def _validate_cell(
    cell: dict,
    semantic_id: str,
    allow_raw: bool,
) -> None:
    """Validate a table cell."""
    if cell.get("t") != "Cell":
        raise ValidationError(
            f"Expected Cell, got {cell.get('t')}",
            semantic_id=semantic_id,
        )

    c = cell.get("c", [])
    if len(c) < 5:
        raise ValidationError(
            "Invalid Cell structure",
            semantic_id=semantic_id,
        )

    # c[0]: Attr
    # c[1]: Alignment
    # c[2]: RowSpan (int)
    # c[3]: ColSpan (int)
    # c[4]: [Block]

    row_span = c[2]
    col_span = c[3]
    blocks = c[4]

    if not isinstance(row_span, int) or row_span < 1:
        raise ValidationError(
            f"Invalid RowSpan: {row_span}",
            semantic_id=semantic_id,
        )

    if not isinstance(col_span, int) or col_span < 1:
        raise ValidationError(
            f"Invalid ColSpan: {col_span}",
            semantic_id=semantic_id,
        )

    if isinstance(blocks, list):
        _validate_blocks(blocks, semantic_id, allow_raw)


def _validate_row(
    row: dict,
    semantic_id: str,
    allow_raw: bool,
) -> None:
    """Validate a table row."""
    if row.get("t") != "Row":
        raise ValidationError(
            f"Expected Row, got {row.get('t')}",
            semantic_id=semantic_id,
        )

    c = row.get("c", [])
    if len(c) < 2:
        raise ValidationError(
            "Invalid Row structure",
            semantic_id=semantic_id,
        )

    # c[0]: Attr
    # c[1]: [Cell]
    cells = c[1]
    if isinstance(cells, list):
        for cell in cells:
            _validate_cell(cell, semantic_id, allow_raw)


def validate_table_pandoc_v1(
    payload: dict[str, Any],
    semantic_id: str,
    config: ResolutionConfig | None = None,
) -> None:
    """
    Validate a table.pandoc.json@v1 payload.

    Args:
        payload: Parsed Pandoc Table block.
        semantic_id: For error messages.
        config: Resolution config for safety settings.

    Raises:
        ValidationError: If payload is invalid.
    """
    allow_raw = config.allow_raw_pandoc if config else False

    if not isinstance(payload, dict):
        raise ValidationError(
            "Pandoc table payload must be an object",
            semantic_id=semantic_id,
        )

    if payload.get("t") != "Table":
        raise ValidationError(
            f"Expected Table block, got {payload.get('t')}",
            semantic_id=semantic_id,
        )

    c = payload.get("c", [])
    if len(c) < 6:
        raise ValidationError(
            "Invalid Table structure",
            semantic_id=semantic_id,
        )

    # c[0]: Attr
    # c[1]: Caption
    # c[2]: [ColSpec]
    # c[3]: TableHead
    # c[4]: [TableBody]
    # c[5]: TableFoot

    # Validate TableHead
    table_head = c[3]
    if isinstance(table_head, dict) and table_head.get("t") == "TableHead":
        head_c = table_head.get("c", [])
        if len(head_c) >= 2:
            rows = head_c[1]
            if isinstance(rows, list):
                for row in rows:
                    _validate_row(row, semantic_id, allow_raw)

    # Validate TableBody sections
    table_bodies = c[4]
    if isinstance(table_bodies, list):
        for body in table_bodies:
            if isinstance(body, dict) and body.get("t") == "TableBody":
                body_c = body.get("c", [])
                if len(body_c) >= 4:
                    # body_c[3] is the main rows list
                    rows = body_c[3]
                    if isinstance(rows, list):
                        for row in rows:
                            _validate_row(row, semantic_id, allow_raw)

    # Validate TableFoot
    table_foot = c[5]
    if isinstance(table_foot, dict) and table_foot.get("t") == "TableFoot":
        foot_c = table_foot.get("c", [])
        if len(foot_c) >= 2:
            rows = foot_c[1]
            if isinstance(rows, list):
                for row in rows:
                    _validate_row(row, semantic_id, allow_raw)
