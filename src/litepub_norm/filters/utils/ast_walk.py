"""AST walking and filtering utilities."""

from __future__ import annotations

from typing import Any, Callable, Iterator
import copy


def get_block_path(block_index: int, parent_path: str = "blocks") -> str:
    """Generate a stable path string for a block."""
    return f"{parent_path}[{block_index}]"


def walk_blocks(
    blocks: list[dict[str, Any]],
    callback: Callable[[dict[str, Any], str, int], None],
    path_prefix: str = "blocks",
) -> None:
    """
    Walk through all blocks and call callback for each.

    Args:
        blocks: List of Pandoc blocks
        callback: Function called with (block, path, index)
        path_prefix: Prefix for path strings
    """
    for i, block in enumerate(blocks):
        path = f"{path_prefix}[{i}]"
        callback(block, path, i)


def filter_blocks(
    blocks: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """
    Filter blocks, keeping only those where predicate returns True.

    Args:
        blocks: List of Pandoc blocks
        predicate: Function that returns True to keep the block

    Returns:
        New list with filtered blocks (does not modify original)
    """
    return [block for block in blocks if predicate(block)]


def remove_blocks_by_ids(
    ast: dict[str, Any],
    ids_to_remove: set[str],
) -> dict[str, Any]:
    """
    Remove blocks with specific semantic IDs from the AST.

    Args:
        ast: Pandoc AST dictionary
        ids_to_remove: Set of semantic IDs to remove

    Returns:
        New AST with blocks removed (does not modify original)
    """
    from .wrappers import get_wrapper_id

    result = copy.deepcopy(ast)
    blocks = result.get("blocks", [])

    def _filter_blocks(block_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered = []
        for block in block_list:
            wrapper_id = get_wrapper_id(block)
            if wrapper_id and wrapper_id in ids_to_remove:
                continue  # Remove this block

            # Check nested content in Divs
            if block.get("t") == "Div":
                content = block.get("c", [])
                if len(content) >= 2 and isinstance(content[1], list):
                    content[1] = _filter_blocks(content[1])

            filtered.append(block)
        return filtered

    result["blocks"] = _filter_blocks(blocks)
    return result


def collect_wrapper_ids(ast: dict[str, Any]) -> set[str]:
    """
    Collect all semantic wrapper IDs from the AST.

    Returns:
        Set of all semantic IDs found
    """
    from .wrappers import iter_wrappers, get_wrapper_id

    ids = set()
    for div, path, idx in iter_wrappers(ast):
        wrapper_id = get_wrapper_id(div)
        if wrapper_id:
            ids.add(wrapper_id)
    return ids
