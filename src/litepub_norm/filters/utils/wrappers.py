"""Wrapper detection and manipulation utilities."""

from __future__ import annotations

from typing import Any, Iterator
import copy


def is_semantic_wrapper(block: dict[str, Any]) -> bool:
    """
    Check if a block is a semantic wrapper Div.

    A semantic wrapper is a Div with a non-empty identifier.
    """
    if not isinstance(block, dict) or block.get("t") != "Div":
        return False

    content = block.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        return False

    attr = content[0]
    if not isinstance(attr, list) or len(attr) < 1:
        return False

    # Check for non-empty identifier
    identifier = attr[0] if len(attr) > 0 else ""
    return bool(identifier)


def get_wrapper_id(div: dict[str, Any]) -> str | None:
    """
    Get the semantic ID from a wrapper Div.

    Returns None if not a semantic wrapper.
    """
    if not is_semantic_wrapper(div):
        return None

    content = div.get("c", [])
    attr = content[0]
    return attr[0] if attr[0] else None


def get_wrapper_attrs_dict(div: dict[str, Any]) -> dict[str, str]:
    """
    Get all key-value attributes from a wrapper Div as a dict.

    Returns empty dict if not a valid wrapper.
    """
    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 1:
        return {}

    attr = content[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return {}

    key_vals = attr[2] if len(attr) > 2 else []
    return {kv[0]: kv[1] for kv in key_vals if isinstance(kv, list) and len(kv) >= 2}


def get_wrapper_attr(div: dict[str, Any], key: str) -> str | None:
    """
    Get a specific attribute value from a wrapper Div.

    Returns None if attribute not found.
    """
    attrs = get_wrapper_attrs_dict(div)
    return attrs.get(key)


def set_wrapper_attr(div: dict[str, Any], key: str, value: str) -> None:
    """
    Set an attribute on a wrapper Div.

    Modifies the div in place.
    """
    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 1:
        return

    attr = content[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return

    key_vals = attr[2]
    # Update existing or append
    for kv in key_vals:
        if isinstance(kv, list) and len(kv) >= 2 and kv[0] == key:
            kv[1] = value
            return
    key_vals.append([key, value])


def del_wrapper_attr(div: dict[str, Any], key: str) -> bool:
    """
    Delete an attribute from a wrapper Div.

    Modifies the div in place. Returns True if deleted, False if not found.
    """
    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 1:
        return False

    attr = content[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return False

    key_vals = attr[2]
    for i, kv in enumerate(key_vals):
        if isinstance(kv, list) and len(kv) >= 2 and kv[0] == key:
            del key_vals[i]
            return True
    return False


def get_visibility(div: dict[str, Any]) -> str:
    """
    Get visibility level from a wrapper Div.

    Returns "internal" as default if not specified.
    """
    return get_wrapper_attr(div, "visibility") or "internal"


def get_policies(div: dict[str, Any]) -> list[str]:
    """
    Get policy tags from a wrapper Div.

    Returns empty list if no policies specified.
    Policies can be in:
    - "policies" attribute (comma-separated)
    - Div classes
    """
    policies = []

    # Check policies attribute
    policies_attr = get_wrapper_attr(div, "policies")
    if policies_attr:
        policies.extend(p.strip() for p in policies_attr.split(",") if p.strip())

    # Check classes
    content = div.get("c", [])
    if isinstance(content, list) and len(content) >= 1:
        attr = content[0]
        if isinstance(attr, list) and len(attr) >= 2:
            classes = attr[1]
            if isinstance(classes, list):
                policies.extend(classes)

    return policies


def is_additional(div: dict[str, Any]) -> bool:
    """
    Check if a wrapper is marked as "additional" content.

    A wrapper is additional if:
    - It has policy tag "additional", OR
    - It has attr presentation="additional", OR
    - It has class "additional"
    """
    policies = get_policies(div)
    if "additional" in policies:
        return True

    presentation = get_wrapper_attr(div, "presentation")
    if presentation == "additional":
        return True

    return False


def iter_wrappers(
    ast: dict[str, Any],
    *,
    include_nested: bool = True,
) -> Iterator[tuple[dict[str, Any], str, int]]:
    """
    Iterate over all semantic wrapper Divs in the AST.

    Yields:
        Tuple of (div_node, path_string, block_index)

    Args:
        ast: Pandoc AST dictionary
        include_nested: If True, also yield nested wrappers
    """
    blocks = ast.get("blocks", [])

    def _iter_blocks(
        block_list: list[dict[str, Any]],
        path_prefix: str,
    ) -> Iterator[tuple[dict[str, Any], str, int]]:
        for i, block in enumerate(block_list):
            path = f"{path_prefix}[{i}]"

            if is_semantic_wrapper(block):
                yield (block, path, i)

                # Check nested content if requested
                if include_nested:
                    content = block.get("c", [])
                    if len(content) >= 2:
                        inner_blocks = content[1]
                        if isinstance(inner_blocks, list):
                            yield from _iter_blocks(inner_blocks, f"{path}.c[1]")

            elif block.get("t") == "Div":
                # Non-semantic Div, still check nested
                if include_nested:
                    content = block.get("c", [])
                    if len(content) >= 2:
                        inner_blocks = content[1]
                        if isinstance(inner_blocks, list):
                            yield from _iter_blocks(inner_blocks, f"{path}.c[1]")

    yield from _iter_blocks(blocks, "blocks")
