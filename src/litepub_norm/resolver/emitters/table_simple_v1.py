"""Emitter for table.simple.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from .pandoc_builders import (
    make_plain,
    make_inlines_from_text,
    make_table_cell,
    make_row,
    make_col_spec,
    make_table,
)


def _format_cell_value(value: Any) -> str:
    """Format a cell value as a string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".15g")
    return str(value)


def emit_simple_table(payload: dict[str, Any]) -> dict:
    """
    Emit a table.simple.json@v1 payload as a Pandoc Table.

    Args:
        payload: Validated table payload.

    Returns:
        Pandoc Table block dict.
    """
    columns = payload["columns"]
    rows = payload["rows"]
    caption = payload.get("caption")

    # Build column specs (all default alignment/width)
    col_specs = [make_col_spec() for _ in columns]

    # Build header row using column labels (or keys as fallback)
    header_cells = []
    for col in columns:
        label = col.get("label", col["key"])
        unit = col.get("unit")
        if unit:
            label = f"{label} ({unit})"
        header_cells.append(
            make_table_cell([make_plain(make_inlines_from_text(label))])
        )
    header_row = make_row(header_cells)

    # Build body rows
    body_rows = []
    for row_data in rows:
        cells = []
        for col in columns:
            key = col["key"]
            value = row_data.get(key)
            value_str = _format_cell_value(value)
            cells.append(
                make_table_cell([make_plain(make_inlines_from_text(value_str))])
            )
        body_rows.append(make_row(cells))

    return make_table(
        col_specs=col_specs,
        head_rows=[header_row],
        body_rows=body_rows,
        caption_text=caption,
    )
