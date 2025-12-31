"""Policy filter - removes wrappers with forbidden policy tags."""

from __future__ import annotations

from typing import Any
import copy

from .context import BuildContext
from .config import FilterConfig
from .report import FilterReport
from .utils.wrappers import iter_wrappers, get_wrapper_id, get_policies
from .utils.ast_walk import remove_blocks_by_ids


def filter_policy(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    Remove wrappers tagged with forbidden policy labels.

    Args:
        ast: Pandoc AST (may have been visibility-filtered)
        config: Filter configuration
        context: Build context

    Returns:
        Tuple of (filtered AST, report)
    """
    report = FilterReport()
    forbidden = config.get_forbidden_policies(context.build_target)

    if not forbidden:
        # No forbidden policies for this target
        return copy.deepcopy(ast), report

    # Collect IDs to remove
    ids_to_remove: set[str] = set()

    for div, path, idx in iter_wrappers(ast):
        wrapper_id = get_wrapper_id(div)
        if not wrapper_id:
            continue

        policies = get_policies(div)
        matching = set(policies) & forbidden

        if matching:
            ids_to_remove.add(wrapper_id)

            # Sort matching tags for deterministic reason code
            sorted_tags = sorted(matching)
            primary_tag = sorted_tags[0]

            report.add(
                semantic_id=wrapper_id,
                action="removed",
                reason_code=f"POL_REMOVED_TAG:{primary_tag}",
                message=f"Wrapper '{wrapper_id}' removed: forbidden policy tag(s)",
                path=path,
                details={
                    "matching_policies": sorted_tags,
                    "target": context.build_target,
                },
            )

    # Remove the blocks
    if ids_to_remove:
        result_ast = remove_blocks_by_ids(ast, ids_to_remove)
    else:
        result_ast = copy.deepcopy(ast)

    return result_ast, report
