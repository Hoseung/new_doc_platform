"""Filter pipeline API."""

from __future__ import annotations

from typing import Any

from .context import BuildContext
from .config import FilterConfig
from .report import FilterReport
from .visibility import filter_visibility
from .policy import filter_policy
from .metadata_strip import filter_metadata_strip
from .presentation import filter_presentation


def apply_filters(
    ast: dict[str, Any],
    config: FilterConfig | None = None,
    context: BuildContext | None = None,
) -> tuple[dict[str, Any], FilterReport]:
    """
    Apply the full filter pipeline to a resolved AST.

    Pipeline order (fixed):
    1. Visibility filter - remove wrappers by visibility level
    2. Policy filter - remove wrappers by forbidden policy tags
    3. Metadata strip filter - strip provenance attributes
    4. Presentation filter - transform for PDF/HTML output

    Args:
        ast: Resolved Pandoc AST
        config: Filter configuration (uses defaults if not provided)
        context: Build context (uses defaults if not provided)

    Returns:
        Tuple of (filtered AST, merged report)
    """
    config = config or FilterConfig()
    context = context or BuildContext()

    combined_report = FilterReport()

    # Step 1: Visibility filter
    ast, vis_report = filter_visibility(ast, config, context)
    combined_report = combined_report.merge(vis_report)

    # Step 2: Policy filter
    ast, pol_report = filter_policy(ast, config, context)
    combined_report = combined_report.merge(pol_report)

    # Step 3: Metadata strip filter
    ast, meta_report = filter_metadata_strip(ast, config, context)
    combined_report = combined_report.merge(meta_report)

    # Step 4: Presentation filter
    ast, pres_report = filter_presentation(ast, config, context)
    combined_report = combined_report.merge(pres_report)

    return ast, combined_report


def apply_filter(
    ast: dict[str, Any],
    filter_name: str,
    config: FilterConfig | None = None,
    context: BuildContext | None = None,
) -> tuple[dict[str, Any], FilterReport]:
    """
    Apply a single named filter.

    Args:
        ast: Pandoc AST
        filter_name: One of "visibility", "policy", "metadata_strip", "presentation"
        config: Filter configuration
        context: Build context

    Returns:
        Tuple of (filtered AST, report)

    Raises:
        ValueError: If filter_name is unknown
    """
    config = config or FilterConfig()
    context = context or BuildContext()

    filters = {
        "visibility": filter_visibility,
        "policy": filter_policy,
        "metadata_strip": filter_metadata_strip,
        "presentation": filter_presentation,
    }

    if filter_name not in filters:
        raise ValueError(f"Unknown filter: {filter_name}. Available: {list(filters.keys())}")

    return filters[filter_name](ast, config, context)
