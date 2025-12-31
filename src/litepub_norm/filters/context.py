"""Build context for filter operations."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal
import json

BuildTarget = Literal["internal", "external", "dossier"]
RenderTarget = Literal["pdf", "html", "md", "rst"]


@dataclass(frozen=True)
class BuildContext:
    """
    Immutable context for filter operations.

    Attributes:
        build_target: Visibility target (internal, external, dossier)
        render_target: Output format (pdf, html, md, rst)
        strict: If True, strict validation (forced True for external/dossier)
        project_root: Root path for relative link generation
        artifact_base_url: Optional base URL for externalized artifacts
    """

    build_target: BuildTarget = "internal"
    render_target: RenderTarget = "pdf"
    strict: bool = True
    project_root: str = "."
    artifact_base_url: str | None = None

    def __post_init__(self) -> None:
        """Enforce strict mode for external/dossier targets."""
        if self.build_target in ("external", "dossier") and not self.strict:
            # Use object.__setattr__ since frozen=True
            object.__setattr__(self, "strict", True)

    def to_dict(self) -> dict:
        """Serialize context for debugging."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize context to JSON."""
        return json.dumps(self.to_dict(), indent=2)
