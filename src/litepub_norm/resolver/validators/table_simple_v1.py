"""Validator for table.simple.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from ..errors import ValidationError
from ..config import ResolutionLimits


def validate_table_simple_v1(
    payload: dict[str, Any],
    semantic_id: str,
    limits: ResolutionLimits | None = None,
) -> None:
    """
    Validate a table.simple.json@v1 payload.

    Args:
        payload: Parsed table JSON.
        semantic_id: For error messages.
        limits: Size limits (optional).

    Raises:
        ValidationError: If payload is invalid.
    """
    if not isinstance(payload, dict):
        raise ValidationError(
            "Table payload must be an object",
            semantic_id=semantic_id,
        )

    # Required: columns (non-empty array)
    columns = payload.get("columns")
    if not isinstance(columns, list) or len(columns) == 0:
        raise ValidationError(
            "Table.columns must be a non-empty array",
            semantic_id=semantic_id,
        )

    # Validate columns and collect keys
    column_keys: list[str] = []
    for i, col in enumerate(columns):
        if not isinstance(col, dict):
            raise ValidationError(
                f"Table.columns[{i}] must be an object",
                semantic_id=semantic_id,
            )

        key = col.get("key")
        if not isinstance(key, str) or not key:
            raise ValidationError(
                f"Table.columns[{i}].key must be a non-empty string",
                semantic_id=semantic_id,
            )

        if key in column_keys:
            raise ValidationError(
                f"Duplicate column key: '{key}'",
                semantic_id=semantic_id,
            )
        column_keys.append(key)

        # Optional: label (string)
        label = col.get("label")
        if label is not None and not isinstance(label, str):
            raise ValidationError(
                f"Table.columns[{i}].label must be a string",
                semantic_id=semantic_id,
            )

        # Optional: unit (string)
        unit = col.get("unit")
        if unit is not None and not isinstance(unit, str):
            raise ValidationError(
                f"Table.columns[{i}].unit must be a string",
                semantic_id=semantic_id,
            )

        # Optional: dtype
        dtype = col.get("dtype")
        if dtype is not None and dtype not in ("string", "int", "float", "bool"):
            raise ValidationError(
                f"Table.columns[{i}].dtype must be one of: string, int, float, bool",
                semantic_id=semantic_id,
            )

    # Required: rows (array)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValidationError(
            "Table.rows must be an array",
            semantic_id=semantic_id,
        )

    # Apply limits
    if limits:
        if len(columns) > limits.max_table_cols:
            raise ValidationError(
                f"Table exceeds max columns ({len(columns)} > {limits.max_table_cols})",
                semantic_id=semantic_id,
            )
        if len(rows) > limits.max_table_rows:
            raise ValidationError(
                f"Table exceeds max rows ({len(rows)} > {limits.max_table_rows})",
                semantic_id=semantic_id,
            )
        total_cells = len(columns) * len(rows)
        if total_cells > limits.max_table_cells:
            raise ValidationError(
                f"Table exceeds max cells ({total_cells} > {limits.max_table_cells})",
                semantic_id=semantic_id,
            )

    # Validate rows
    column_key_set = set(column_keys)
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValidationError(
                f"Table.rows[{i}] must be an object",
                semantic_id=semantic_id,
            )

        row_keys = set(row.keys())

        # Check for extra keys (not in columns)
        extra_keys = row_keys - column_key_set
        if extra_keys:
            raise ValidationError(
                f"Table.rows[{i}] has unknown keys: {extra_keys}",
                semantic_id=semantic_id,
            )

        # Validate cell values
        for key, value in row.items():
            if value is not None and not isinstance(value, (str, int, float, bool)):
                raise ValidationError(
                    f"Table.rows[{i}].{key} must be string|number|boolean|null",
                    semantic_id=semantic_id,
                )

    # Optional: caption (string)
    caption = payload.get("caption")
    if caption is not None and not isinstance(caption, str):
        raise ValidationError(
            "Table.caption must be a string when present",
            semantic_id=semantic_id,
        )

    # Optional: notes (array of strings)
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise ValidationError(
                "Table.notes must be an array when present",
                semantic_id=semantic_id,
            )
        if not all(isinstance(n, str) for n in notes):
            raise ValidationError(
                "Table.notes must be an array of strings",
                semantic_id=semantic_id,
            )

    # Optional: meta (object)
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise ValidationError(
            "Table.meta must be an object when present",
            semantic_id=semantic_id,
        )
