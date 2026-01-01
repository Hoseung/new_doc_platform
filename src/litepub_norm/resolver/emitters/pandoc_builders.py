"""Pandoc AST node builders."""

from __future__ import annotations

from typing import Any


def make_str(text: str) -> dict:
    """Create a Str inline node."""
    return {"t": "Str", "c": text}


def make_space() -> dict:
    """Create a Space inline node."""
    return {"t": "Space"}


def make_inlines_from_text(text: str) -> list[dict]:
    """
    Convert text string to a list of inline nodes.

    Words are separated by Space nodes.
    """
    words = text.split()
    if not words:
        return []

    inlines = []
    for i, word in enumerate(words):
        if i > 0:
            inlines.append(make_space())
        inlines.append(make_str(word))
    return inlines


def make_para(inlines: list[dict]) -> dict:
    """Create a Para block node."""
    return {"t": "Para", "c": inlines}


def make_plain(inlines: list[dict]) -> dict:
    """Create a Plain block node."""
    return {"t": "Plain", "c": inlines}


def make_attr(identifier: str = "", classes: list[str] | None = None,
              attrs: list[list[str]] | None = None) -> list:
    """Create an Attr structure: [id, [classes], [[key, val], ...]]."""
    return [identifier, classes or [], attrs or []]


def make_table_cell(
    content: list[dict],
    align: str = "AlignDefault",
    row_span: int = 1,
    col_span: int = 1,
) -> list:
    """
    Create a Cell node for Pandoc tables.

    In Pandoc 3.x JSON format, Cell is an array:
    [Attr, Alignment, RowSpan, ColSpan, [Block]]

    Args:
        content: List of block nodes for cell content.
        align: Alignment ("AlignDefault", "AlignLeft", "AlignCenter", "AlignRight").
        row_span: Number of rows this cell spans.
        col_span: Number of columns this cell spans.

    Returns:
        Cell as an array.
    """
    return [
        make_attr(),  # Attr
        {"t": align},  # Alignment
        row_span,
        col_span,
        content,
    ]


def make_row(cells: list) -> list:
    """
    Create a Row node.

    In Pandoc 3.x JSON format, Row is an array: [Attr, [Cell]]
    """
    return [make_attr(), cells]


def make_table_head(rows: list) -> list:
    """
    Create a TableHead node.

    In Pandoc 3.x JSON format, TableHead is an array: [Attr, [Row]]
    """
    return [make_attr(), rows]


def make_table_body(rows: list) -> list:
    """
    Create a TableBody node.

    In Pandoc 3.x JSON format, TableBody is an array:
    [Attr, RowHeadColumns, [Row], [Row]]
    (Attr, number of row header columns, intermediate head rows, body rows)
    """
    return [
        make_attr(),
        0,  # RowHeadColumns
        [],  # Intermediate head (empty)
        rows,
    ]


def make_table_foot() -> list:
    """
    Create an empty TableFoot node.

    In Pandoc 3.x JSON format, TableFoot is an array: [Attr, [Row]]
    """
    return [make_attr(), []]


def make_col_spec(align: str = "AlignDefault", width: str = "ColWidthDefault") -> list:
    """Create a ColSpec: [Alignment, ColWidth]."""
    return [{"t": align}, {"t": width}]


def make_caption(text: str | None = None) -> list:
    """
    Create a Caption structure.

    Caption is: [ShortCaption, [Block]]
    ShortCaption is null or [Inline]
    """
    if text:
        return [None, [make_para(make_inlines_from_text(text))]]
    return [None, []]


def make_table(
    col_specs: list[list],
    head_rows: list[dict],
    body_rows: list[dict],
    caption_text: str | None = None,
) -> dict:
    """
    Create a complete Table block.

    Args:
        col_specs: List of [Alignment, ColWidth] for each column.
        head_rows: List of Row nodes for the header.
        body_rows: List of Row nodes for the body.
        caption_text: Optional caption text.

    Returns:
        Table block dict.
    """
    return {
        "t": "Table",
        "c": [
            make_attr(),  # Attr
            make_caption(caption_text),  # Caption
            col_specs,  # [ColSpec]
            make_table_head(head_rows),  # TableHead
            [make_table_body(body_rows)],  # [TableBody]
            make_table_foot(),  # TableFoot
        ],
    }
