"""Base utilities for payload loading."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..errors import HashMismatchError, PayloadError


def compute_sha256(path: Path) -> str:
    """
    Compute SHA256 hash of a file.

    Returns:
        Hash string in format "sha256:<hex>".
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def verify_hash(
    path: Path,
    expected: str,
    semantic_id: str,
) -> None:
    """
    Verify file hash matches expected value.

    Args:
        path: Path to file.
        expected: Expected hash (format: "sha256:<hex>").
        semantic_id: For error messages.

    Raises:
        HashMismatchError: If hash doesn't match.
    """
    actual = compute_sha256(path)
    if actual != expected:
        raise HashMismatchError(
            semantic_id=semantic_id,
            expected=expected,
            actual=actual,
            path=str(path),
        )


def load_json_file(path: Path, semantic_id: str) -> dict:
    """
    Load and parse a JSON file.

    Args:
        path: Path to JSON file.
        semantic_id: For error messages.

    Returns:
        Parsed JSON as dict.

    Raises:
        PayloadError: If file cannot be read or parsed.
    """
    import json

    if not path.exists():
        raise PayloadError(
            f"Payload file not found: {path}",
            semantic_id=semantic_id,
            path=str(path),
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise PayloadError(
            f"Invalid JSON in payload: {e}",
            semantic_id=semantic_id,
            path=str(path),
        )
    except Exception as e:
        raise PayloadError(
            f"Failed to read payload: {e}",
            semantic_id=semantic_id,
            path=str(path),
        )
