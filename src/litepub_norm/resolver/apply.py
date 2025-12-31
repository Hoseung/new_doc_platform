"""Apply resolution plan to AST."""

from __future__ import annotations

import copy
from typing import Any

from .config import ResolutionConfig
from .registry import RegistrySnapshot
from .plan import ResolutionPlan, ResolutionItem
from .errors import PayloadError, ValidationError

# Loaders
from .loaders.metric_v1 import load_metric_v1
from .loaders.table_simple_v1 import load_table_simple_v1
from .loaders.table_pandoc_v1 import load_table_pandoc_v1
from .loaders.figure_v1 import load_figure_v1, load_figure_meta_v1

# Validators
from ..validator import (
    validate_metric_v1,
    validate_table_simple_v1,
    validate_table_pandoc_v1,
    validate_figure_meta_v1,
)

# Emitters
from .emitters.metric_v1 import emit_metric_as_table
from .emitters.table_simple_v1 import emit_simple_table
from .emitters.table_pandoc_v1 import emit_pandoc_table
from .emitters.figure_v1 import emit_figure


def _resolve_item(
    item: ResolutionItem,
    registry: RegistrySnapshot,
    config: ResolutionConfig,
) -> dict:
    """
    Resolve a single item: load, validate, and emit.

    Args:
        item: Resolution item from the plan.
        registry: Registry for path resolution.
        config: Resolution configuration.

    Returns:
        Pandoc block to replace the placeholder.

    Raises:
        PayloadError: If payload cannot be loaded.
        ValidationError: If payload is invalid.
    """
    entry = item.entry
    spec = entry.spec

    if spec == "metric.json@v1":
        payload = load_metric_v1(registry, entry, verify=config.strict)
        validate_metric_v1(payload, entry.id)
        return emit_metric_as_table(payload)

    elif spec == "table.simple.json@v1":
        payload = load_table_simple_v1(registry, entry, verify=config.strict)
        validate_table_simple_v1(payload, entry.id, config.limits)
        return emit_simple_table(payload)

    elif spec == "table.pandoc.json@v1":
        payload = load_table_pandoc_v1(registry, entry, verify=config.strict)
        validate_table_pandoc_v1(payload, entry.id, config)
        return emit_pandoc_table(payload)

    elif spec == "figure.binary@v1":
        image_path = load_figure_v1(registry, entry, verify=config.strict)
        meta = load_figure_meta_v1(registry, entry, verify=config.strict)
        validate_figure_meta_v1(meta, entry.id)
        return emit_figure(image_path, meta, entry.id)

    else:
        raise PayloadError(
            f"Unknown payload spec: {spec}",
            semantic_id=entry.id,
        )


def _replace_placeholder_in_wrapper(
    wrapper: dict,
    placeholder_idx: int,
    replacement: dict,
) -> dict:
    """
    Replace the placeholder block in a wrapper Div with the resolved content.

    Args:
        wrapper: The wrapper Div block (will be modified in place).
        placeholder_idx: Index of the placeholder block in wrapper content.
        replacement: The Pandoc block to insert.

    Returns:
        The modified wrapper.
    """
    content = wrapper.get("c", [])
    if len(content) >= 2:
        blocks = content[1]
        if 0 <= placeholder_idx < len(blocks):
            blocks[placeholder_idx] = replacement
    return wrapper


def apply_plan(
    ast: dict,
    plan: ResolutionPlan,
    registry: RegistrySnapshot,
    config: ResolutionConfig,
) -> dict:
    """
    Apply a resolution plan to an AST.

    Resolves all items in the plan, replacing placeholders with
    computed content.

    Args:
        ast: Normalized Pandoc AST (will be copied, not modified).
        plan: Resolution plan with items to resolve.
        registry: Registry for path resolution.
        config: Resolution configuration.

    Returns:
        New AST with placeholders replaced.

    Raises:
        PayloadError: If any payload cannot be loaded.
        ValidationError: If any payload is invalid.
    """
    # Deep copy to avoid modifying original
    result = copy.deepcopy(ast)
    blocks = result.get("blocks", [])

    for item in plan:
        # Resolve the item
        replacement = _resolve_item(item, registry, config)

        # Get the wrapper Div
        wrapper_idx = item.wrapper_index
        if 0 <= wrapper_idx < len(blocks):
            wrapper = blocks[wrapper_idx]
            _replace_placeholder_in_wrapper(
                wrapper,
                item.placeholder_index,
                replacement,
            )

    return result
