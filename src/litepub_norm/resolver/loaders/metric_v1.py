"""Loader for metric.json@v1 payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..registry import RegistrySnapshot, RegistryEntry
from ..errors import PayloadError
from .base import verify_hash, load_json_file


def load_metric_v1(
    registry: RegistrySnapshot,
    entry: RegistryEntry,
    verify: bool = True,
) -> dict[str, Any]:
    """
    Load a metric.json@v1 payload.

    Args:
        registry: Registry for path resolution.
        entry: Registry entry for this metric.
        verify: Whether to verify hash (default True).

    Returns:
        Parsed metric payload dict.

    Raises:
        PayloadError: If file cannot be loaded.
        HashMismatchError: If hash verification fails.
    """
    if entry.spec != "metric.json@v1":
        raise PayloadError(
            f"Expected spec 'metric.json@v1', got '{entry.spec}'",
            semantic_id=entry.id,
        )

    path = registry.resolve_entry_path(entry)

    if verify:
        verify_hash(path, entry.sha256, entry.id)

    return load_json_file(path, entry.id)
