"""Render result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RenderWarning:
    """A warning generated during rendering."""

    code: str
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class RenderError:
    """An error encountered during rendering."""

    code: str
    message: str
    stage: str  # "pandoc", "latex", "assets", etc.
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"code": self.code, "message": self.message, "stage": self.stage}
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class RenderResult:
    """
    Result of a render operation.

    Attributes:
        success: Whether rendering completed successfully
        output_files: List of generated output files
        warnings: List of warnings generated
        errors: List of errors encountered
        report: Render report data (for render_report.json)
    """

    success: bool
    output_files: list[Path] = field(default_factory=list)
    warnings: list[RenderWarning] = field(default_factory=list)
    errors: list[RenderError] = field(default_factory=list)
    report: dict[str, Any] = field(default_factory=dict)

    def add_warning(
        self, code: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """Add a warning to the result."""
        self.warnings.append(RenderWarning(code=code, message=message, details=details))

    def add_error(
        self,
        code: str,
        message: str,
        stage: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add an error to the result."""
        self.errors.append(
            RenderError(code=code, message=message, stage=stage, details=details)
        )
        self.success = False

    def add_output_file(self, path: Path) -> None:
        """Add an output file to the result."""
        self.output_files.append(path)

    @property
    def primary_output(self) -> Path | None:
        """Get the primary output file (first in list)."""
        return self.output_files[0] if self.output_files else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "output_files": [str(p) for p in self.output_files],
            "warnings": [w.to_dict() for w in self.warnings],
            "errors": [e.to_dict() for e in self.errors],
            "report": self.report,
        }
