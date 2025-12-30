"""Resolution configuration."""

from dataclasses import dataclass, field
from typing import Literal

BuildTarget = Literal["internal", "external", "dossier"]


@dataclass(frozen=True)
class ResolutionLimits:
    """Size limits for resolved content."""

    max_table_cells: int = 200_000
    max_table_rows: int = 10_000
    max_table_cols: int = 100
    max_text_len: int = 5_000_000
    max_image_bytes: int = 50_000_000


@dataclass(frozen=True)
class ResolutionConfig:
    """Configuration for the resolution stage."""

    target: BuildTarget = "internal"
    strict: bool = True
    allow_raw_pandoc: bool = False
    limits: ResolutionLimits = field(default_factory=ResolutionLimits)

    def is_strict_target(self) -> bool:
        """Check if target requires strict validation."""
        return self.target in ("external", "dossier")
