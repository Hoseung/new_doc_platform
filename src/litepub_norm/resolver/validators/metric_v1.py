"""Validator for metric.json@v1 payloads."""

from __future__ import annotations

from typing import Any
import math

from ..errors import ValidationError


def validate_metric_v1(payload: dict[str, Any], semantic_id: str) -> None:
    """
    Validate a metric.json@v1 payload.

    Args:
        payload: Parsed metric JSON.
        semantic_id: For error messages.

    Raises:
        ValidationError: If payload is invalid.
    """
    if not isinstance(payload, dict):
        raise ValidationError(
            "Metric payload must be an object",
            semantic_id=semantic_id,
        )

    # Required: label (non-empty string)
    label = payload.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValidationError(
            "Metric.label must be a non-empty string",
            semantic_id=semantic_id,
        )

    # Required: value (finite number)
    value = payload.get("value")
    if not isinstance(value, (int, float)):
        raise ValidationError(
            "Metric.value must be a number",
            semantic_id=semantic_id,
        )
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise ValidationError(
            "Metric.value must be a finite number (not NaN or Inf)",
            semantic_id=semantic_id,
        )

    # Optional: unit (non-empty string if present)
    unit = payload.get("unit")
    if unit is not None:
        if not isinstance(unit, str) or not unit.strip():
            raise ValidationError(
                "Metric.unit must be a non-empty string when present",
                semantic_id=semantic_id,
            )

    # Optional: format (string if present)
    fmt = payload.get("format")
    if fmt is not None and not isinstance(fmt, str):
        raise ValidationError(
            "Metric.format must be a string when present",
            semantic_id=semantic_id,
        )

    # Optional: lower_is_better (boolean if present)
    lower_is_better = payload.get("lower_is_better")
    if lower_is_better is not None and not isinstance(lower_is_better, bool):
        raise ValidationError(
            "Metric.lower_is_better must be a boolean when present",
            semantic_id=semantic_id,
        )

    # Optional: notes (array of strings if present)
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise ValidationError(
                "Metric.notes must be an array when present",
                semantic_id=semantic_id,
            )
        if not all(isinstance(n, str) for n in notes):
            raise ValidationError(
                "Metric.notes must be an array of strings",
                semantic_id=semantic_id,
            )

    # Optional: meta (object if present)
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise ValidationError(
            "Metric.meta must be an object when present",
            semantic_id=semantic_id,
        )
