"""Filter configuration with defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

BuildTarget = Literal["internal", "external", "dossier"]


@dataclass(frozen=True)
class PresentationThresholds:
    """Thresholds for presentation transformations."""

    # PDF code block thresholds
    pdf_code_max_lines: int = 50
    pdf_code_max_chars: int = 3000
    pdf_code_preview_lines: int = 5

    # Appendix thresholds for additional content
    appendix_threshold_blocks: int = 5
    appendix_threshold_chars: int = 2000

    # HTML fold thresholds
    html_fold_threshold_blocks: int = 5
    html_fold_threshold_chars: int = 2000


@dataclass(frozen=True)
class AppendixOptions:
    """Options for appendix generation."""

    title: str = "Appendix"
    anchor_prefix: str = "appendix"


@dataclass(frozen=True)
class FilterConfig:
    """
    Configuration for the filter pipeline.

    All settings are deterministic - no callables with randomness/time.
    """

    # Visibility ordering (lower number = more restricted)
    visibility_order: dict[str, int] = field(
        default_factory=lambda: {"internal": 0, "external": 1, "dossier": 2}
    )

    # Forbidden policies per build target
    forbidden_policies: dict[BuildTarget, frozenset[str]] = field(
        default_factory=lambda: {
            "internal": frozenset(),
            "external": frozenset({"internal-only", "draft", "wip"}),
            "dossier": frozenset({"internal-only", "draft", "wip", "verbose"}),
        }
    )

    # Metadata keys to strip per build target
    # Protected keys that are never stripped: id, role, kind, visibility, policies
    strip_attrs_external: frozenset[str] = field(
        default_factory=lambda: frozenset({
            "producer",
            "run_id",
            "dataset_fingerprint",
            "config_fingerprint",
            "artifact_uri",
            "sha256",
            "source",
            "schema",
        })
    )

    strip_attrs_dossier: frozenset[str] = field(
        default_factory=lambda: frozenset({
            "producer",
            "run_id",
            "dataset_fingerprint",
            "config_fingerprint",
            "artifact_uri",
            "sha256",
            "source",
            "schema",
            "lock",
            "bind-to",
        })
    )

    # Presentation thresholds
    thresholds: PresentationThresholds = field(
        default_factory=PresentationThresholds
    )

    # Appendix options
    appendix: AppendixOptions = field(default_factory=AppendixOptions)

    # Protected attribute keys (never stripped)
    protected_attrs: frozenset[str] = field(
        default_factory=lambda: frozenset({
            "id", "role", "kind", "visibility", "policies"
        })
    )

    def get_forbidden_policies(self, target: BuildTarget) -> frozenset[str]:
        """Get forbidden policies for a build target."""
        return self.forbidden_policies.get(target, frozenset())

    def get_strip_attrs(self, target: BuildTarget) -> frozenset[str]:
        """Get attributes to strip for a build target."""
        if target == "internal":
            return frozenset()
        elif target == "external":
            return self.strip_attrs_external
        else:  # dossier
            return self.strip_attrs_dossier

    def get_allowed_visibility_level(self, target: BuildTarget) -> int:
        """
        Get minimum visibility level for a build target.

        Returns the visibility level that content must have to be included.
        - internal: allows all (level >= 0)
        - external: allows external + dossier (level >= 1)
        - dossier: allows dossier only (level >= 2)
        """
        return self.visibility_order.get(target, 0)
