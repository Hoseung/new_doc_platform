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
    spec = "figure.meta.json@v1"

    if payload is None:
        return

    if not isinstance(payload, dict):
        raise ValidationError(
            "Figure metadata must be an object",
            code="VAL_FIGURE_NOT_OBJECT",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Optional: caption (string)
    caption = payload.get("caption")
    if caption is not None and not isinstance(caption, str):
        raise ValidationError(
            "Figure.caption must be a string when present",
            code="VAL_FIGURE_CAPTION_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Optional: alt (string)
    alt = payload.get("alt")
    if alt is not None and not isinstance(alt, str):
        raise ValidationError(
            "Figure.alt must be a string when present",
            code="VAL_FIGURE_ALT_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Optional: notes (array of strings)
    notes = payload.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise ValidationError(
                "Figure.notes must be an array when present",
                code="VAL_FIGURE_NOTES_TYPE",
                semantic_id=semantic_id,
                spec=spec,
            )
        for i, note in enumerate(notes):
            if not isinstance(note, str):
                raise ValidationError(
                    f"Figure.notes[{i}] must be a string",
                    code="VAL_FIGURE_NOTES_ITEM_TYPE",
                    semantic_id=semantic_id,
                    spec=spec,
                    hint="All items in notes array must be strings",
                )

    # Optional: meta (object)
    meta = payload.get("meta")
    if meta is not None and not isinstance(meta, dict):
        raise ValidationError(
            "Figure.meta must be an object when present",
            code="VAL_FIGURE_META_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )
