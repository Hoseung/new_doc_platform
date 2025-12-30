"""AARC v1.1 Registry loader and model."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .errors import RegistryError

ArtifactType = Literal["table", "metric", "figure"]


@dataclass(frozen=True)
class RegistryRun:
    """Run-level provenance information."""

    run_id: str
    test_id: str
    pipeline_name: str
    pipeline_version: str
    code_commit: str
    code_dirty: bool
    dataset_fingerprint: str
    config_fingerprint: str


@dataclass(frozen=True)
class RegistryEntry:
    """Single artifact entry in the registry."""

    id: str
    artifact_type: ArtifactType
    format: str
    spec: str
    uri: str
    sha256: str
    origin_producer: str
    # Optional fields
    meta_uri: str | None = None
    meta_sha256: str | None = None
    meta_spec: str | None = None
    related: list[dict[str, Any]] | None = None
    meta: dict[str, Any] | None = None


@dataclass
class RegistrySnapshot:
    """Complete registry snapshot (aarc-1.1)."""

    registry_version: str
    generated_at: str
    artifact_root: str
    run: RegistryRun
    entries: dict[str, RegistryEntry] = field(default_factory=dict)
    # Base path for resolving relative artifact_root
    _base_path: Path = field(default_factory=Path.cwd, repr=False)

    def get(self, semantic_id: str) -> RegistryEntry:
        """
        Get entry by semantic ID.

        Raises:
            RegistryError: If ID not found.
        """
        if semantic_id not in self.entries:
            raise RegistryError(
                f"Missing registry entry for '{semantic_id}'",
                semantic_id=semantic_id,
            )
        return self.entries[semantic_id]

    def has(self, semantic_id: str) -> bool:
        """Check if semantic ID exists in registry."""
        return semantic_id in self.entries

    def resolve_uri(self, uri: str) -> Path:
        """
        Resolve a URI to an absolute path.

        Args:
            uri: Relative or absolute URI from entry.

        Returns:
            Absolute path to the artifact.
        """
        # Check if absolute
        if uri.startswith("/") or "://" in uri:
            return Path(uri)

        # Resolve relative to artifact_root
        if self.artifact_root.startswith("/"):
            root = Path(self.artifact_root)
        else:
            root = self._base_path / self.artifact_root

        return root / uri

    def resolve_entry_path(self, entry: RegistryEntry) -> Path:
        """Resolve the main payload path for an entry."""
        return self.resolve_uri(entry.uri)

    def resolve_meta_path(self, entry: RegistryEntry) -> Path | None:
        """Resolve the metadata sidecar path for an entry, if present."""
        if entry.meta_uri:
            return self.resolve_uri(entry.meta_uri)
        return None


def load_registry(path: str | Path) -> RegistrySnapshot:
    """
    Load an AARC v1.1 registry from JSON file.

    Args:
        path: Path to registry JSON file.

    Returns:
        RegistrySnapshot instance.

    Raises:
        RegistryError: If file cannot be loaded or is invalid.
    """
    path = Path(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise RegistryError(f"Registry file not found: {path}")
    except json.JSONDecodeError as e:
        raise RegistryError(f"Invalid JSON in registry: {e}")

    # Validate version
    version = data.get("registry_version")
    if version != "aarc-1.1":
        raise RegistryError(f"Unsupported registry_version: {version} (expected aarc-1.1)")

    # Parse run provenance
    run_data = data.get("run")
    if not run_data:
        raise RegistryError("Missing 'run' section in registry")

    try:
        pipeline = run_data.get("pipeline", {})
        code = run_data.get("code", {})
        inputs = run_data.get("inputs", {})

        run = RegistryRun(
            run_id=run_data["run_id"],
            test_id=run_data["test_id"],
            pipeline_name=pipeline["name"],
            pipeline_version=pipeline["version"],
            code_commit=code["commit"],
            code_dirty=code.get("dirty", False),
            dataset_fingerprint=inputs["dataset_fingerprint"],
            config_fingerprint=inputs["config_fingerprint"],
        )
    except KeyError as e:
        raise RegistryError(f"Missing required field in run section: {e}")

    # Parse entries
    entries_map: dict[str, RegistryEntry] = {}
    for e in data.get("entries", []):
        try:
            origin = e.get("origin", {})
            producer = origin.get("producer")
            if not producer:
                raise RegistryError(
                    f"Entry '{e.get('id')}' missing origin.producer",
                    semantic_id=e.get("id"),
                )

            entry = RegistryEntry(
                id=e["id"],
                artifact_type=e["artifact_type"],
                format=e["format"],
                spec=e["spec"],
                uri=e["uri"],
                sha256=e["sha256"],
                origin_producer=producer,
                meta_uri=e.get("meta_uri"),
                meta_sha256=e.get("meta_sha256"),
                meta_spec=e.get("meta_spec"),
                related=e.get("related"),
                meta=e.get("meta"),
            )

            if entry.id in entries_map:
                raise RegistryError(
                    f"Duplicate entry id in registry: {entry.id}",
                    semantic_id=entry.id,
                )
            entries_map[entry.id] = entry

        except KeyError as err:
            raise RegistryError(
                f"Missing required field in entry: {err}",
                semantic_id=e.get("id"),
            )

    return RegistrySnapshot(
        registry_version=data["registry_version"],
        generated_at=data["generated_at"],
        artifact_root=data["artifact_root"],
        run=run,
        entries=entries_map,
        _base_path=path.parent,
    )
