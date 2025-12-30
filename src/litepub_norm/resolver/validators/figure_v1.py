"""Validator for figure.meta.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from ..errors import ValidationError


def validate_figure_meta_v1(
    payload: dict[str, Any] | None,
    semantic_id: str,
) -> None:
    """
    Validate a figure.meta.json@v1 payload.

    Args:
        payload: Parsed metadata JSON (or None if no sidecar).
        semantic_id: For error messages.

    Raises:
        ValidationError: If payload is invalid.
    """
    if payload is None:
        return

    if not isinstance(payload, dict):
        raise ValidationError(
            "Figure metadata must be an object",
            semantic_id=semantic_id,
        )

    # Optional: caption (string)
    caption = payload.get("caption")
    if caption is not None and not isinstance(caption, str):
        raise ValidationError(
            "Figure.caption must be a string when present",
            semantic_id=semantic_id,
        )

    # Optional: alt (string)
    alt = payload.get("alt")
    if alt is not None and not isinstance(alt, str):
        raise ValidationError(
            "Figure.alt must be a string when present",
            semantic_id=semantic_id,
        )

    # Optional: notes (array of strings)
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise ValidationError(
                "Figure.notes must be an array when present",
                semantic_id=semantic_id,
            )
        if not all(isinstance(n, str) for n in notes):
            raise ValidationError(
                "Figure.notes must be an array of strings",
                semantic_id=semantic_id,
            )

    # Optional: meta (object)
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise ValidationError(
            "Figure.meta must be an object when present",
            semantic_id=semantic_id,
        )
