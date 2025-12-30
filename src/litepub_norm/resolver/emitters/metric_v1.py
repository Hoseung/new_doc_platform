"""Emitter for metric.json@v1 payloads."""

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


def _format_metric_value(payload: dict[str, Any]) -> str:
    """
    Format the metric value as a string.

    Uses the format string if provided, otherwise constructs
    a default representation.
    """
    value = payload["value"]
    unit = payload.get("unit", "")
    fmt = payload.get("format")

    # Deterministic value formatting
    if isinstance(value, int):
        value_str = str(value)
    else:
        # Use .15g for stable float formatting
        value_str = format(value, ".15g")

    if fmt:
        # Only substitute {value} and {unit}
        result = fmt.replace("{value}", value_str)
        result = result.replace("{unit}", unit)
        return result.strip()

    if unit:
        return f"{value_str} {unit}"
    return value_str


def emit_metric_as_table(payload: dict[str, Any]) -> dict:
    """
    Emit a metric payload as a 2-column, 1-row Pandoc Table.

    Args:
        payload: Validated metric payload.

    Returns:
        Pandoc Table block dict.
    """
    label = payload["label"]
    value_str = _format_metric_value(payload)

    # Create table structure:
    # | Label | Value |
    # |-------|-------|
    # | <label> | <value_str> |

    col_specs = [
        make_col_spec("AlignLeft"),
        make_col_spec("AlignRight"),
    ]

    # Header row
    header_row = make_row([
        make_table_cell([make_plain(make_inlines_from_text("Metric"))]),
        make_table_cell([make_plain(make_inlines_from_text("Value"))]),
    ])

    # Data row
    data_row = make_row([
        make_table_cell([make_plain(make_inlines_from_text(label))]),
        make_table_cell([make_plain(make_inlines_from_text(value_str))]),
    ])

    return make_table(
        col_specs=col_specs,
        head_rows=[header_row],
        body_rows=[data_row],
        caption_text=None,  # Don't duplicate caption if wrapper has prose
    )
