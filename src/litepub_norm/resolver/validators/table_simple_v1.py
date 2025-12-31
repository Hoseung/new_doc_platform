"""Validator for table.simple.json@v1 payloads."""

from __future__ import annotations

import math
import re
from typing import Any

from ..errors import ValidationError
from ..config import ResolutionLimits

# Column key identifier pattern: alphanumeric + underscore, not starting with digit
_KEY_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_table_simple_v1(
    payload: dict[str, Any],
    semantic_id: str,
    limits: ResolutionLimits | None = None,
    *,
    strict_keys: bool = True,
) -> None:
    """
    Validate a table.simple.json@v1 payload.

    Args:
        payload: Parsed table JSON.
        semantic_id: For error messages.
        limits: Size limits (optional).
        strict_keys: If True, require all rows to have exactly the column keys
                     (Policy S: strict rectangular). If False, allow missing keys
                     (Policy P: permissive, missing treated as null).

    Raises:
        ValidationError: If payload is invalid.
    """
    spec = "table.simple.json@v1"

    if not isinstance(payload, dict):
        raise ValidationError(
            "Table payload must be an object",
            code="VAL_TABLE_NOT_OBJECT",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Required: columns (non-empty array)
    columns = payload.get("columns")
    if not isinstance(columns, list):
        raise ValidationError(
            "Table.columns must be an array",
            code="VAL_TABLE_COLUMNS_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )
    if len(columns) == 0:
        raise ValidationError(
            "Table.columns must be a non-empty array",
            code="VAL_TABLE_COLUMNS_EMPTY",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Validate columns and collect keys with their dtypes
    column_keys: list[str] = []
    column_dtypes: dict[str, str | None] = {}

    for i, col in enumerate(columns):
        if not isinstance(col, dict):
            raise ValidationError(
                f"Table.columns[{i}] must be an object",
                code="VAL_TABLE_COLUMN_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )

        key = col.get("key")
        if not isinstance(key, str):
            raise ValidationError(
                f"Table.columns[{i}].key must be a string",
                code="VAL_TABLE_COLUMN_KEY_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )

        if not key:
            raise ValidationError(
                f"Table.columns[{i}].key must be non-empty",
                code="VAL_TABLE_COLUMN_KEY_EMPTY",
                semantic_id=semantic_id,
                spec=spec,
            )

        # Validate key matches identifier pattern
        if not _KEY_PATTERN.match(key):
            raise ValidationError(
                f"Table.columns[{i}].key '{key}' must be a valid identifier "
                "(alphanumeric + underscore, not starting with digit)",
                code="VAL_TABLE_COLUMN_KEY_INVALID",
                semantic_id=semantic_id,
                spec=spec,
                hint="Use keys like 'name', 'value_1', '_id'",
            )

        if key in column_keys:
            raise ValidationError(
                f"Duplicate column key: '{key}'",
                code="VAL_TABLE_COLUMN_KEY_DUPLICATE",
                semantic_id=semantic_id,
                spec=spec,
            )
        column_keys.append(key)

        # Optional: label (string)
        label = col.get("label")
        if label is not None and not isinstance(label, str):
            raise ValidationError(
                f"Table.columns[{i}].label must be a string",
                code="VAL_TABLE_COLUMN_LABEL_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )

        # Optional: unit (string)
        unit = col.get("unit")
        if unit is not None and not isinstance(unit, str):
            raise ValidationError(
                f"Table.columns[{i}].unit must be a string",
                code="VAL_TABLE_COLUMN_UNIT_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )

        # Optional: dtype
        dtype = col.get("dtype")
        if dtype is not None:
            if dtype not in ("string", "int", "float", "bool"):
                raise ValidationError(
                    f"Table.columns[{i}].dtype must be one of: string, int, float, bool",
                    code="VAL_TABLE_COLUMN_DTYPE_INVALID",
                    semantic_id=semantic_id,
                    spec=spec,
                )
            column_dtypes[key] = dtype
        else:
            column_dtypes[key] = None

    # Required: rows (array)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValidationError(
            "Table.rows must be an array",
            code="VAL_TABLE_ROWS_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Apply limits
    if limits:
        if len(columns) > limits.max_table_cols:
            raise ValidationError(
                f"Table exceeds max columns ({len(columns)} > {limits.max_table_cols})",
                code="VAL_TABLE_EXCEEDS_MAX_COLS",
                semantic_id=semantic_id,
                spec=spec,
            )
        if len(rows) > limits.max_table_rows:
            raise ValidationError(
                f"Table exceeds max rows ({len(rows)} > {limits.max_table_rows})",
                code="VAL_TABLE_EXCEEDS_MAX_ROWS",
                semantic_id=semantic_id,
                spec=spec,
            )
        total_cells = len(columns) * len(rows)
        if total_cells > limits.max_table_cells:
            raise ValidationError(
                f"Table exceeds max cells ({total_cells} > {limits.max_table_cells})",
                code="VAL_TABLE_EXCEEDS_MAX_CELLS",
                semantic_id=semantic_id,
                spec=spec,
            )

    # Validate rows
    column_key_set = set(column_keys)

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValidationError(
                f"Table.rows[{i}] must be an object",
                code="VAL_TABLE_ROW_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )

        row_keys = set(row.keys())

        # Check for extra keys (not in columns) - always forbidden
        extra_keys = row_keys - column_key_set
        if extra_keys:
            raise ValidationError(
                f"Table.rows[{i}] has unknown keys: {extra_keys}",
                code="VAL_TABLE_ROW_EXTRA_KEYS",
                semantic_id=semantic_id,
                spec=spec,
                hint="Row keys must match column definitions",
            )

        # Check for missing keys based on policy
        if strict_keys:
            missing_keys = column_key_set - row_keys
            if missing_keys:
                raise ValidationError(
                    f"Table.rows[{i}] is missing keys: {missing_keys}",
                    code="VAL_TABLE_ROW_MISSING_KEYS",
                    semantic_id=semantic_id,
                    spec=spec,
                    hint="All rows must have all column keys (strict rectangular policy)",
                )

        # Validate cell values and dtype enforcement
        for key, value in row.items():
            dtype = column_dtypes.get(key)

            # Null is always allowed
            if value is None:
                continue

            # Check base type is valid
            if not isinstance(value, (str, int, float, bool)):
                raise ValidationError(
                    f"Table.rows[{i}].{key} must be string|number|boolean|null",
                    code="VAL_TABLE_CELL_TYPE",
                    semantic_id=semantic_id,
                    spec=spec,
                )

            # Enforce dtype if specified
            if dtype is not None:
                _validate_cell_dtype(value, dtype, i, key, semantic_id, spec)


def _validate_cell_dtype(
    value: Any,
    dtype: str,
    row_idx: int,
    key: str,
    semantic_id: str,
    spec: str,
) -> None:
    """Validate a cell value matches the declared dtype."""

    if dtype == "string":
        if not isinstance(value, str):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: expected string, got {type(value).__name__}",
                code="VAL_TABLE_DTYPE_MISMATCH",
                semantic_id=semantic_id,
                spec=spec,
            )

    elif dtype == "int":
        # CRITICAL: Check bool BEFORE int (bool is subclass of int)
        if isinstance(value, bool):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: expected int, got bool",
                code="VAL_TABLE_DTYPE_BOOL_AS_INT",
                semantic_id=semantic_id,
                spec=spec,
                hint="Use integer value, not True/False",
            )
        if not isinstance(value, int):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: expected int, got {type(value).__name__}",
                code="VAL_TABLE_DTYPE_MISMATCH",
                semantic_id=semantic_id,
                spec=spec,
            )

    elif dtype == "float":
        # CRITICAL: Check bool BEFORE number
        if isinstance(value, bool):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: expected float, got bool",
                code="VAL_TABLE_DTYPE_BOOL_AS_FLOAT",
                semantic_id=semantic_id,
                spec=spec,
                hint="Use numeric value, not True/False",
            )
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: expected float, got {type(value).__name__}",
                code="VAL_TABLE_DTYPE_MISMATCH",
                semantic_id=semantic_id,
                spec=spec,
            )
        # Reject NaN/Inf for float dtype
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: float value must be finite (not NaN/Inf)",
                code="VAL_TABLE_DTYPE_FLOAT_NONFINITE",
                semantic_id=semantic_id,
                spec=spec,
            )

    elif dtype == "bool":
        if not isinstance(value, bool):
            raise ValidationError(
                f"Table.rows[{row_idx}].{key}: expected bool, got {type(value).__name__}",
                code="VAL_TABLE_DTYPE_MISMATCH",
                semantic_id=semantic_id,
                spec=spec,
            )


def validate_table_simple_optional_fields(
    payload: dict[str, Any],
    semantic_id: str,
) -> None:
    """
    Validate optional fields in table payload.

    Separated for profile-based strictness control.
    """
    spec = "table.simple.json@v1"

    # Optional: caption (string)
    caption = payload.get("caption")
    if caption is not None and not isinstance(caption, str):
        raise ValidationError(
            "Table.caption must be a string when present",
            code="VAL_TABLE_CAPTION_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Optional: notes (array of strings)
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise ValidationError(
                "Table.notes must be an array when present",
                code="VAL_TABLE_NOTES_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )
        for i, note in enumerate(notes):
            if not isinstance(note, str):
                raise ValidationError(
                    f"Table.notes[{i}] must be a string",
                    code="VAL_TABLE_NOTES_ITEM_TYPE",
                    semantic_id=semantic_id,
                    spec=spec,
                )

    # Optional: meta (object)
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise ValidationError(
            "Table.meta must be an object when present",
            code="VAL_TABLE_META_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )
