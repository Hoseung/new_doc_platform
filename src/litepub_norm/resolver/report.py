"""Resolution report generation for debugging and auditing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ResolutionConfig
from .registry import RegistrySnapshot, RegistryEntry
from .plan import ResolutionPlan, ResolutionItem


@dataclass
class ItemReport:
    """Report for a single resolution item."""

    semantic_id: str
    artifact_type: str
    spec: str
    uri: str
    resolved_path: str

    # Hash verification
    expected_hash: str
    actual_hash: str | None = None
    hash_verified: bool | None = None
    hash_match: bool | None = None

    # Validation
    validation_passed: bool = True
    validation_errors: list[str] = field(default_factory=list)

    # Payload info
    payload_size_bytes: int | None = None
    payload_summary: dict[str, Any] = field(default_factory=dict)

    # Timing
    load_time_ms: float | None = None
    validate_time_ms: float | None = None
    emit_time_ms: float | None = None

    # Status
    status: str = "pending"  # "pending", "success", "failed", "skipped"
    error_message: str | None = None


@dataclass
class ResolutionReport:
    """Complete resolution report."""

    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    config_target: str = ""
    config_strict: bool = True

    # Registry info
    registry_version: str = ""
    registry_run_id: str = ""
    registry_entries_total: int = 0

    # Plan info
    plan_items_total: int = 0
    items_resolved: int = 0
    items_failed: int = 0
    items_skipped: int = 0

    # Item reports
    items: list[ItemReport] = field(default_factory=list)

    # Summary
    all_hashes_verified: bool = False
    all_validations_passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "generated_at": self.generated_at,
            "config": {
                "target": self.config_target,
                "strict": self.config_strict,
            },
            "registry": {
                "version": self.registry_version,
                "run_id": self.registry_run_id,
                "entries_total": self.registry_entries_total,
            },
            "summary": {
                "plan_items_total": self.plan_items_total,
                "items_resolved": self.items_resolved,
                "items_failed": self.items_failed,
                "items_skipped": self.items_skipped,
                "all_hashes_verified": self.all_hashes_verified,
                "all_validations_passed": self.all_validations_passed,
            },
            "items": [
                {
                    "semantic_id": item.semantic_id,
                    "artifact_type": item.artifact_type,
                    "spec": item.spec,
                    "uri": item.uri,
                    "resolved_path": item.resolved_path,
                    "hash": {
                        "expected": item.expected_hash,
                        "actual": item.actual_hash,
                        "verified": item.hash_verified,
                        "match": item.hash_match,
                    },
                    "validation": {
                        "passed": item.validation_passed,
                        "errors": item.validation_errors,
                    },
                    "payload": {
                        "size_bytes": item.payload_size_bytes,
                        "summary": item.payload_summary,
                    },
                    "timing_ms": {
                        "load": item.load_time_ms,
                        "validate": item.validate_time_ms,
                        "emit": item.emit_time_ms,
                    },
                    "status": item.status,
                    "error": item.error_message,
                }
                for item in self.items
            ],
        }


def _compute_file_hash(path: Path) -> str | None:
    """Compute SHA256 hash of a file."""
    if not path.exists():
        return None
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return f"sha256:{sha.hexdigest()}"


def _summarize_metric_payload(payload: dict) -> dict:
    """Extract summary info from metric payload."""
    return {
        "label": payload.get("label", ""),
        "value": payload.get("value"),
        "unit": payload.get("unit", ""),
        "has_notes": "notes" in payload,
    }


def _summarize_simple_table_payload(payload: dict) -> dict:
    """Extract summary info from simple table payload."""
    columns = payload.get("columns", [])
    rows = payload.get("rows", [])
    return {
        "num_columns": len(columns),
        "num_rows": len(rows),
        "column_keys": [c.get("key") for c in columns],
        "has_caption": "caption" in payload,
    }


def _summarize_pandoc_table_payload(payload: dict) -> dict:
    """Extract summary info from Pandoc table payload."""
    c = payload.get("c", [])
    if len(c) >= 6:
        col_specs = c[2] if len(c) > 2 else []
        table_head = c[3] if len(c) > 3 else {}
        table_bodies = c[4] if len(c) > 4 else []

        # Count rows
        head_rows = 0
        if isinstance(table_head, dict):
            head_c = table_head.get("c", [])
            if len(head_c) >= 2:
                head_rows = len(head_c[1])

        body_rows = 0
        for body in table_bodies:
            if isinstance(body, dict):
                body_c = body.get("c", [])
                if len(body_c) >= 4:
                    body_rows += len(body_c[3])

        return {
            "num_columns": len(col_specs),
            "num_head_rows": head_rows,
            "num_body_rows": body_rows,
        }
    return {"type": payload.get("t")}


def _summarize_figure_meta(meta: dict | None, image_path: Path) -> dict:
    """Extract summary info from figure metadata."""
    summary = {
        "image_exists": image_path.exists() if image_path else False,
        "image_format": image_path.suffix if image_path else None,
    }
    if image_path and image_path.exists():
        summary["image_size_bytes"] = image_path.stat().st_size

    if meta:
        summary["has_caption"] = "caption" in meta
        summary["has_alt"] = "alt" in meta
        summary["num_notes"] = len(meta.get("notes", []))

    return summary


def build_item_report(
    item: ResolutionItem,
    registry: RegistrySnapshot,
    config: ResolutionConfig,
    load_payloads: bool = True,
) -> ItemReport:
    """Build a report for a single resolution item."""
    import json

    entry = item.entry
    path = registry.resolve_entry_path(entry)

    report = ItemReport(
        semantic_id=item.semantic_id,
        artifact_type=entry.artifact_type,
        spec=entry.spec,
        uri=entry.uri,
        resolved_path=str(path),
        expected_hash=entry.sha256,
    )

    # Compute actual hash
    if path.exists():
        report.actual_hash = _compute_file_hash(path)
        report.hash_verified = True
        report.hash_match = report.actual_hash == report.expected_hash
        report.payload_size_bytes = path.stat().st_size

        # Load and summarize payload
        if load_payloads:
            try:
                if entry.spec == "metric.json@v1":
                    with open(path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    report.payload_summary = _summarize_metric_payload(payload)
                elif entry.spec == "table.simple.json@v1":
                    with open(path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    report.payload_summary = _summarize_simple_table_payload(payload)
                elif entry.spec == "table.pandoc.json@v1":
                    with open(path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    report.payload_summary = _summarize_pandoc_table_payload(payload)
                elif entry.spec == "figure.binary@v1":
                    # Load sidecar meta if exists
                    meta = None
                    meta_path = registry.resolve_meta_path(entry)
                    if meta_path and meta_path.exists():
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                    report.payload_summary = _summarize_figure_meta(meta, path)
            except Exception as e:
                report.payload_summary = {"error": str(e)}
    else:
        report.hash_verified = False
        report.hash_match = False

    return report


def build_resolution_report(
    plan: ResolutionPlan,
    registry: RegistrySnapshot,
    config: ResolutionConfig,
) -> ResolutionReport:
    """
    Build a resolution report from a plan.

    This creates a report without actually applying resolution,
    useful for pre-flight checks.
    """
    report = ResolutionReport(
        config_target=config.target,
        config_strict=config.strict,
        registry_version=registry.registry_version,
        registry_run_id=registry.run.run_id,
        registry_entries_total=len(registry.entries),
        plan_items_total=len(plan),
    )

    all_hashes_match = True
    all_valid = True

    for item in plan:
        item_report = build_item_report(item, registry, config)
        report.items.append(item_report)

        if not item_report.hash_match:
            all_hashes_match = False

    report.all_hashes_verified = all_hashes_match
    report.all_validations_passed = all_valid  # Updated during actual resolution

    return report
