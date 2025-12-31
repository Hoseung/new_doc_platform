"""Filter report model for tracking filter actions."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import json


@dataclass
class FilterReportEntry:
    """
    Single entry in a filter report.

    Attributes:
        semantic_id: The semantic ID of the affected wrapper
        action: The action taken (e.g., "removed", "stripped", "folded")
        reason_code: Stable code for test assertions
        message: Optional human-readable message
        path: Optional AST path to the node
        details: Optional additional details (e.g., stripped keys)
    """

    semantic_id: str
    action: str
    reason_code: str
    message: str | None = None
    path: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {
            "semantic_id": self.semantic_id,
            "action": self.action,
            "reason_code": self.reason_code,
        }
        if self.message is not None:
            result["message"] = self.message
        if self.path is not None:
            result["path"] = self.path
        if self.details is not None:
            result["details"] = self.details
        return result


@dataclass
class FilterReport:
    """
    Report of all filter actions taken during a filter pass.

    Entries are stored in application order for deterministic output.
    """

    entries: list[FilterReportEntry] = field(default_factory=list)

    def add(
        self,
        semantic_id: str,
        action: str,
        reason_code: str,
        message: str | None = None,
        path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add an entry to the report."""
        self.entries.append(
            FilterReportEntry(
                semantic_id=semantic_id,
                action=action,
                reason_code=reason_code,
                message=message,
                path=path,
                details=details,
            )
        )

    def merge(self, other: FilterReport) -> FilterReport:
        """
        Merge another report into this one, maintaining order.

        Returns a new report with combined entries.
        """
        return FilterReport(entries=self.entries + other.entries)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entries": [e.to_dict() for e in self.entries],
            "total_actions": len(self.entries),
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)

    def filter_by_action(self, action: str) -> list[FilterReportEntry]:
        """Get entries with a specific action."""
        return [e for e in self.entries if e.action == action]

    def filter_by_reason_code(self, code: str) -> list[FilterReportEntry]:
        """Get entries with a specific reason code."""
        return [e for e in self.entries if e.reason_code == code]
