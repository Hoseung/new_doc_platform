"""Loader for table.simple.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from ..registry import RegistrySnapshot, RegistryEntry
from ..errors import PayloadError
from .base import verify_hash, load_json_file


def load_table_simple_v1(
    registry: RegistrySnapshot,
    entry: RegistryEntry,
    verify: bool = True,
) -> dict[str, Any]:
    """
    Load a table.simple.json@v1 payload.

    Args:
        registry: Registry for path resolution.
        entry: Registry entry for this table.
        verify: Whether to verify hash (default True).

    Returns:
        Parsed table payload dict.

    Raises:
        PayloadError: If file cannot be loaded.
        HashMismatchError: If hash verification fails.
    """
    if entry.spec != "table.simple.json@v1":
        raise PayloadError(
            f"Expected spec 'table.simple.json@v1', got '{entry.spec}'",
            semantic_id=entry.id,
        )

    path = registry.resolve_entry_path(entry)

    if verify:
        verify_hash(path, entry.sha256, entry.id)

    return load_json_file(path, entry.id)
