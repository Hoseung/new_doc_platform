"""
DOM Contract for HTML Theming.

Defines the stable hook points (IDs and classes) that all themes
must preserve and can style. This ensures themes are interchangeable
without breaking the semantic structure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


# =============================================================================
# Required DOM Hook Points
# =============================================================================

REQUIRED_IDS: frozenset[str] = frozenset({
    "lp-header",    # Page header (title block)
    "lp-nav",       # Top navigation (can be empty)
    "lp-sidebar",   # Sidebar container (can be empty)
    "lp-toc",       # Table of contents (optional, often inside sidebar)
    "lp-content",   # Main content container (MUST NOT be removed)
    "lp-footer",    # Page footer
})

REQUIRED_CLASSES: frozenset[str] = frozenset({
    "computed-figure",   # Semantic figure wrapper
    "computed-table",    # Semantic table wrapper
    "computed-metric",   # Semantic metric wrapper
    "foldable",          # Foldable/collapsible section
    "foldable-header",   # Foldable header (click target)
    "foldable-content",  # Foldable content (toggleable)
})

# IDs that must always be present (non-optional)
MANDATORY_IDS: frozenset[str] = frozenset({
    "lp-content",  # Content is always required
})

# IDs that can be empty but should still exist for styling hooks
OPTIONAL_IDS: frozenset[str] = REQUIRED_IDS - MANDATORY_IDS


# =============================================================================
# Validation
# =============================================================================

@dataclass
class ValidationResult:
    """Result of template hook validation."""
    valid: bool
    missing_mandatory: list[str]
    missing_optional: list[str]
    warnings: list[str]


def validate_template_hooks(
    template_content: str,
    mode: Literal["strict", "lenient"] = "lenient",
) -> ValidationResult:
    """
    Validate that a template contains required hook points.

    Args:
        template_content: HTML template content as string
        mode: "strict" requires all hooks, "lenient" only checks mandatory

    Returns:
        ValidationResult with missing hooks and warnings
    """
    missing_mandatory = []
    missing_optional = []
    warnings = []

    # Check mandatory IDs (must be present)
    for hook_id in MANDATORY_IDS:
        pattern = rf'id\s*=\s*["\']?{re.escape(hook_id)}["\']?'
        if not re.search(pattern, template_content, re.IGNORECASE):
            missing_mandatory.append(hook_id)

    # Check optional IDs (should be present but template can choose to omit)
    for hook_id in OPTIONAL_IDS:
        pattern = rf'id\s*=\s*["\']?{re.escape(hook_id)}["\']?'
        if not re.search(pattern, template_content, re.IGNORECASE):
            missing_optional.append(hook_id)
            if mode == "strict":
                warnings.append(f"Optional hook '{hook_id}' not found in template")

    # Check for UTF-8 charset declaration
    if 'charset="utf-8"' not in template_content.lower() and "charset=utf-8" not in template_content.lower():
        warnings.append("Template should include <meta charset=\"utf-8\">")

    # Check for $body$ variable (required for Pandoc)
    if "$body$" not in template_content:
        missing_mandatory.append("$body$ (Pandoc variable)")

    valid = len(missing_mandatory) == 0

    return ValidationResult(
        valid=valid,
        missing_mandatory=missing_mandatory,
        missing_optional=missing_optional,
        warnings=warnings,
    )


def validate_template_file(
    template_path: Path,
    mode: Literal["strict", "lenient"] = "lenient",
) -> ValidationResult:
    """
    Validate a template file for required hook points.

    Args:
        template_path: Path to template.html file
        mode: Validation strictness

    Returns:
        ValidationResult

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    content = template_path.read_text(encoding="utf-8")
    return validate_template_hooks(content, mode)
