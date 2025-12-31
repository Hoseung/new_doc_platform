"""Registry for semantic ID metadata resolution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..errors import UnknownSemanticIdError, RegistryIncompleteError


# Required fields for computed blocks
COMPUTED_REQUIRED_FIELDS = {"role", "kind", "source", "schema"}
# Required fields for hybrid/annotation blocks
HYBRID_REQUIRED_FIELDS = {"role", "kind"}


class Registry:
    """
    Registry for resolving semantic IDs to metadata.

    The registry maps semantic IDs to their metadata including:
    - role: computed, hybrid, authored
    - kind: table, figure, metric, annotation
    - source: path to analysis artifact
    - schema: schema version for tables/metrics
    - visibility: internal, external, dossier
    - bind-to: binding target for annotations
    """

    def __init__(self, data: dict[str, dict[str, Any]], strict: bool = True):
        """
        Initialize registry with data.

        Args:
            data: Mapping of semantic IDs to metadata dicts.
            strict: If True, raise errors for unknown IDs and incomplete entries.
                    If False (draft mode), return partial data with warnings.
        """
        self._data = data
        self._strict = strict

    @classmethod
    def from_file(cls, path: str | Path, strict: bool = True) -> Registry:
        """Load registry from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data, strict=strict)

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, Any]], strict: bool = True) -> Registry:
        """Create registry from a dictionary."""
        return cls(data, strict=strict)

    def resolve(self, semantic_id: str) -> dict[str, Any]:
        """
        Resolve a semantic ID to its metadata.

        Args:
            semantic_id: The semantic ID to look up.

        Returns:
            A dict containing metadata for the ID.

        Raises:
            UnknownSemanticIdError: If ID not found and strict mode is on.
            RegistryIncompleteError: If required fields missing and strict mode is on.
        """
        if semantic_id not in self._data:
            if self._strict:
                raise UnknownSemanticIdError(semantic_id)
            return {}

        entry = self._data[semantic_id].copy()

        # Validate required fields based on role
        if self._strict:
            role = entry.get("role", "")
            if role == "computed":
                missing = COMPUTED_REQUIRED_FIELDS - set(entry.keys())
                # schema may be optional for figures
                if entry.get("kind") == "figure":
                    missing.discard("schema")
                if missing:
                    raise RegistryIncompleteError(semantic_id, list(missing))
            elif role == "hybrid":
                missing = HYBRID_REQUIRED_FIELDS - set(entry.keys())
                if missing:
                    raise RegistryIncompleteError(semantic_id, list(missing))

        return entry

    def has_id(self, semantic_id: str) -> bool:
        """Check if a semantic ID exists in the registry."""
        return semantic_id in self._data

    def all_ids(self) -> set[str]:
        """Return all semantic IDs in the registry."""
        return set(self._data.keys())
