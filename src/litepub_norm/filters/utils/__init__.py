"""Filter utilities."""

from .wrappers import (
    iter_wrappers,
    get_wrapper_id,
    get_wrapper_attr,
    set_wrapper_attr,
    del_wrapper_attr,
    get_wrapper_attrs_dict,
    is_semantic_wrapper,
    get_visibility,
    get_policies,
    is_additional,
)

from .ast_walk import (
    walk_blocks,
    filter_blocks,
    get_block_path,
)

from .text_metrics import (
    count_codeblock_lines,
    count_codeblock_chars,
    estimate_block_chars,
    estimate_div_blocks,
)

__all__ = [
    # Wrapper utilities
    "iter_wrappers",
    "get_wrapper_id",
    "get_wrapper_attr",
    "set_wrapper_attr",
    "del_wrapper_attr",
    "get_wrapper_attrs_dict",
    "is_semantic_wrapper",
    "get_visibility",
    "get_policies",
    "is_additional",
    # AST walk utilities
    "walk_blocks",
    "filter_blocks",
    "get_block_path",
    # Text metrics
    "count_codeblock_lines",
    "count_codeblock_chars",
    "estimate_block_chars",
    "estimate_div_blocks",
]
