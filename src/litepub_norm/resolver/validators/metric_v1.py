"""Validator for metric.json@v1 payloads."""

from __future__ import annotations

import math
import re
from typing import Any

from ..errors import ValidationError

# Allowed tokens in format string
_FORMAT_TOKENS = frozenset(["value", "unit"])
_FORMAT_PATTERN = re.compile(r"\{(\w+)\}")
_MAX_FORMAT_LEN = 200


def validate_metric_v1(
    payload: dict[str, Any],
    semantic_id: str,
    *,
    strict_format: bool = True,
) -> None:
    """
    Validate a metric.json@v1 payload.

    Args:
        payload: Parsed metric JSON.
        semantic_id: For error messages.
        strict_format: If True, restrict format string to {value} and {unit} only.

    Raises:
        ValidationError: If payload is invalid.
    """
    spec = "metric.json@v1"

    if not isinstance(payload, dict):
        raise ValidationError(
            "Metric payload must be an object",
            code="VAL_METRIC_NOT_OBJECT",
            semantic_id=semantic_id,
            spec=spec,
            hint="Payload should be a JSON object with 'label' and 'value' fields",
        )

    # Required: label (non-empty string)
    label = payload.get("label")
    if not isinstance(label, str):
        raise ValidationError(
            "Metric.label must be a string",
            code="VAL_METRIC_LABEL_TYPE",
            semantic_id=semantic_id,
            spec=spec,
            hint="Provide a non-empty string for 'label'",
        )
    if not label.strip():
        raise ValidationError(
            "Metric.label must be a non-empty string",
            code="VAL_METRIC_LABEL_EMPTY",
            semantic_id=semantic_id,
            spec=spec,
            hint="Label cannot be empty or whitespace-only",
        )

    # Required: value (finite number, NOT bool)
    value = payload.get("value")

    # CRITICAL: Check bool BEFORE number, since bool is subclass of int
    if isinstance(value, bool):
        raise ValidationError(
            "Metric.value must be a number, not a boolean",
            code="VAL_METRIC_VALUE_BOOL",
            semantic_id=semantic_id,
            spec=spec,
            hint="Use a numeric value (int or float), not True/False",
        )

    if not isinstance(value, (int, float)):
        raise ValidationError(
            "Metric.value must be a number",
            code="VAL_METRIC_VALUE_TYPE",
            semantic_id=semantic_id,
            spec=spec,
            hint="Provide a numeric value for 'value'",
        )

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise ValidationError(
            "Metric.value must be a finite number (not NaN or Inf)",
            code="VAL_METRIC_VALUE_NONFINITE",
            semantic_id=semantic_id,
            spec=spec,
            hint="Replace NaN/Infinity with a finite value or handle upstream",
        )

    # Optional: unit (string if present, can be empty for dimensionless values)
    unit = payload.get("unit")
    if unit is not None and not isinstance(unit, str):
        raise ValidationError(
            "Metric.unit must be a string when present",
            code="VAL_METRIC_UNIT_TYPE",
            semantic_id=semantic_id,
            spec=spec,
            hint="Unit should be a string (empty string allowed for dimensionless)",
        )

    # Optional: format (string if present, with token restrictions)
    fmt = payload.get("format")
    if fmt is not None:
        if not isinstance(fmt, str):
            raise ValidationError(
                "Metric.format must be a string when present",
                code="VAL_METRIC_FORMAT_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )

        if len(fmt) > _MAX_FORMAT_LEN:
            raise ValidationError(
                f"Metric.format exceeds max length ({len(fmt)} > {_MAX_FORMAT_LEN})",
                code="VAL_METRIC_FORMAT_TOO_LONG",
                semantic_id=semantic_id,
                spec=spec,
            )

        if strict_format:
            # Check for allowed tokens only
            tokens = _FORMAT_PATTERN.findall(fmt)
            invalid_tokens = set(tokens) - _FORMAT_TOKENS
            if invalid_tokens:
                raise ValidationError(
                    f"Metric.format contains disallowed tokens: {invalid_tokens}",
                    code="VAL_METRIC_FORMAT_INVALID_TOKEN",
                    semantic_id=semantic_id,
                    spec=spec,
                    hint="Only {value} and {unit} tokens are allowed in format string",
                )

            # Forbid newlines in format
            if "\n" in fmt or "\r" in fmt:
                raise ValidationError(
                    "Metric.format must not contain newlines",
                    code="VAL_METRIC_FORMAT_NEWLINE",
                    semantic_id=semantic_id,
                    spec=spec,
                )

    # Optional: lower_is_better (boolean if present)
    lower_is_better = payload.get("lower_is_better")
    if lower_is_better is not None and not isinstance(lower_is_better, bool):
        raise ValidationError(
            "Metric.lower_is_better must be a boolean when present",
            code="VAL_METRIC_LOWER_IS_BETTER_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Optional: notes (array of strings if present)
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise ValidationError(
                "Metric.notes must be an array when present",
                code="VAL_METRIC_NOTES_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )
        for i, note in enumerate(notes):
            if not isinstance(note, str):
                raise ValidationError(
                    f"Metric.notes[{i}] must be a string",
                    code="VAL_METRIC_NOTES_ITEM_TYPE",
                    semantic_id=semantic_id,
                    spec=spec,
                    hint="All items in notes array must be strings",
                )

    # Optional: meta (object if present)
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise ValidationError(
            "Metric.meta must be an object when present",
            code="VAL_METRIC_META_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )
