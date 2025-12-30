"""Emitter for table.pandoc.json@v1 payloads."""

from __future__ import annotations

from typing import Any


def emit_pandoc_table(payload: dict[str, Any]) -> dict:
    """
    Emit a table.pandoc.json@v1 payload.

    The payload is already a Pandoc Table block, so this is
    essentially a pass-through. The loader and validator have
    already ensured the payload is valid.

    Args:
        payload: Validated Pandoc Table block.

    Returns:
        The same Pandoc Table block dict.
    """
    # The payload is already a valid Pandoc Table block
    return payload
