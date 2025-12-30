"""Loader for table.pandoc.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from ..registry import RegistrySnapshot, RegistryEntry
from ..errors import PayloadError
from .base import verify_hash, load_json_file


def load_table_pandoc_v1(
    registry: RegistrySnapshot,
    entry: RegistryEntry,
    verify: bool = True,
) -> dict[str, Any]:
    """
    Load a table.pandoc.json@v1 payload.

    The payload is a single Pandoc Table block as JSON.

    Args:
        registry: Registry for path resolution.
        entry: Registry entry for this table.
        verify: Whether to verify hash (default True).

    Returns:
        Parsed Pandoc Table block dict.

    Raises:
        PayloadError: If file cannot be loaded or is not a Table block.
        HashMismatchError: If hash verification fails.
    """
    if entry.spec != "table.pandoc.json@v1":
        raise PayloadError(
            f"Expected spec 'table.pandoc.json@v1', got '{entry.spec}'",
            semantic_id=entry.id,
        )

    path = registry.resolve_entry_path(entry)

    if verify:
        verify_hash(path, entry.sha256, entry.id)

    data = load_json_file(path, entry.id)

    # Validate it's a Table block
    if data.get("t") != "Table":
        raise PayloadError(
            f"Expected Pandoc Table block, got type '{data.get('t')}'",
            semantic_id=entry.id,
            path=str(path),
        )

    return data
