"""Visibility filter - removes wrappers not allowed by build target."""

from __future__ import annotations

from typing import Any
import copy

from .context import BuildContext
from .config import FilterConfig
from .report import FilterReport
from .utils.wrappers import iter_wrappers, get_wrapper_id, get_visibility
from .utils.ast_walk import remove_blocks_by_ids


def filter_visibility(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    Remove wrappers not allowed by build target visibility.

    Visibility ordering: internal < external < dossier

    - internal build: allows all
    - external build: allows external + dossier (removes internal-only)
    - dossier build: allows dossier only (removes internal and external)

    Args:
        ast: Resolved Pandoc AST
        config: Filter configuration
        context: Build context

    Returns:
        Tuple of (filtered AST, report)
    """
    report = FilterReport()
    target_level = config.get_allowed_visibility_level(context.build_target)

    # Collect IDs to remove
    ids_to_remove: set[str] = set()

    for div, path, idx in iter_wrappers(ast):
        wrapper_id = get_wrapper_id(div)
        if not wrapper_id:
            continue

        visibility = get_visibility(div)
        vis_level = config.visibility_order.get(visibility, 0)

        # If wrapper's visibility level is below target, remove it
        if vis_level < target_level:
            ids_to_remove.add(wrapper_id)

            # Determine reason code
            if visibility == "internal":
                reason_code = "VIS_REMOVED_INTERNAL_ONLY"
                message = f"Wrapper '{wrapper_id}' removed: internal-only content"
            else:
                reason_code = "VIS_REMOVED_EXTERNAL_ONLY"
                message = f"Wrapper '{wrapper_id}' removed: not visible in {context.build_target}"

            report.add(
                semantic_id=wrapper_id,
                action="removed",
                reason_code=reason_code,
                message=message,
                path=path,
                details={"visibility": visibility, "target": context.build_target},
            )

    # Remove the blocks
    if ids_to_remove:
        result_ast = remove_blocks_by_ids(ast, ids_to_remove)
    else:
        result_ast = copy.deepcopy(ast)

    return result_ast, report
