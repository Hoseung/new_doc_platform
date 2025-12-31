"""Metadata strip filter - removes provenance/internal metadata for external outputs."""

from __future__ import annotations

from typing import Any
import copy

from .context import BuildContext
from .config import FilterConfig
from .report import FilterReport
from .utils.wrappers import (
    iter_wrappers,
    get_wrapper_id,
    get_wrapper_attrs_dict,
    del_wrapper_attr,
)


def filter_metadata_strip(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    Strip provenance/internal metadata from wrappers for external/dossier outputs.

    For internal builds: no stripping
    For external/dossier: strips configured keys while preserving protected keys.

    Protected keys (never stripped): id, role, kind, visibility, policies

    Args:
        ast: Pandoc AST
        config: Filter configuration
        context: Build context

    Returns:
        Tuple of (modified AST, report)
    """
    report = FilterReport()
    strip_keys = config.get_strip_attrs(context.build_target)

    if not strip_keys:
        # No stripping for internal target
        return copy.deepcopy(ast), report

    # Deep copy AST for modification
    result_ast = copy.deepcopy(ast)

    # Track stripped keys per wrapper for reporting
    for div, path, idx in iter_wrappers(result_ast):
        wrapper_id = get_wrapper_id(div)
        if not wrapper_id:
            continue

        attrs = get_wrapper_attrs_dict(div)
        stripped_keys: list[str] = []

        for key in sorted(attrs.keys()):  # Sorted for determinism
            if key in strip_keys and key not in config.protected_attrs:
                if del_wrapper_attr(div, key):
                    stripped_keys.append(key)

        if stripped_keys:
            report.add(
                semantic_id=wrapper_id,
                action="stripped",
                reason_code="META_STRIP_ATTRS",
                message=f"Stripped {len(stripped_keys)} attribute(s) from '{wrapper_id}'",
                path=path,
                details={
                    "stripped_keys": stripped_keys,
                    "target": context.build_target,
                },
            )

    return result_ast, report
