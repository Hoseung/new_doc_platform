"""Loader for figure.binary@v1 and figure.meta.json@v1 payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..registry import RegistrySnapshot, RegistryEntry
from ..errors import PayloadError
from .base import verify_hash, load_json_file


# Allowed figure formats
ALLOWED_FORMATS = {
    "image.png",
    "image.jpg",
    "image.jpeg",
    "image.webp",
    "image.svg",
    "image.pdf",
}


def load_figure_v1(
    registry: RegistrySnapshot,
    entry: RegistryEntry,
    verify: bool = True,
) -> Path:
    """
    Load a figure.binary@v1 payload.

    Args:
        registry: Registry for path resolution.
        entry: Registry entry for this figure.
        verify: Whether to verify hash (default True).

    Returns:
        Path to the figure file (verified to exist).

    Raises:
        PayloadError: If file cannot be found or format not allowed.
        HashMismatchError: If hash verification fails.
    """
    if entry.spec != "figure.binary@v1":
        raise PayloadError(
            f"Expected spec 'figure.binary@v1', got '{entry.spec}'",
            semantic_id=entry.id,
        )

    # Check format is allowed
    if entry.format not in ALLOWED_FORMATS:
        raise PayloadError(
            f"Figure format '{entry.format}' not allowed",
            semantic_id=entry.id,
        )

    path = registry.resolve_entry_path(entry)

    if not path.exists():
        raise PayloadError(
            f"Figure file not found: {path}",
            semantic_id=entry.id,
            path=str(path),
        )

    if verify:
        verify_hash(path, entry.sha256, entry.id)

    return path


def load_figure_meta_v1(
    registry: RegistrySnapshot,
    entry: RegistryEntry,
    verify: bool = True,
) -> dict[str, Any] | None:
    """
    Load figure.meta.json@v1 sidecar metadata if present.

    Args:
        registry: Registry for path resolution.
        entry: Registry entry for the figure.
        verify: Whether to verify hash (default True).

    Returns:
        Parsed metadata dict, or None if no sidecar.

    Raises:
        PayloadError: If sidecar file cannot be loaded.
        HashMismatchError: If hash verification fails.
    """
    if not entry.meta_uri:
        return None

    if entry.meta_spec != "figure.meta.json@v1":
        raise PayloadError(
            f"Expected meta_spec 'figure.meta.json@v1', got '{entry.meta_spec}'",
            semantic_id=entry.id,
        )

    path = registry.resolve_meta_path(entry)
    if path is None or not path.exists():
        raise PayloadError(
            f"Figure metadata file not found: {path}",
            semantic_id=entry.id,
            path=str(path) if path else None,
        )

    if verify and entry.meta_sha256:
        verify_hash(path, entry.meta_sha256, entry.id)

    return load_json_file(path, entry.id)
