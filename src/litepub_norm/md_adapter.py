"""
Markdown adapter for the normalization pipeline.

Converts HTML comment fences (<!-- BEGIN id --> ... <!-- END id -->)
into wrapper Div candidates in the Pandoc AST.

Also passes through Pandoc fenced Divs as wrapper candidates.

Note: Pandoc may place END fences as RawInline within a Para block
when there's no blank line before the END comment. This adapter
handles both cases.
"""

from __future__ import annotations

import re
from typing import Any

from .errors import FenceMismatchError, FenceOverlapError


# Regex patterns for HTML comment fences
BEGIN_PATTERN = re.compile(r"^\s*<!--\s*BEGIN\s+(\S+)\s*-->\s*$")
END_PATTERN = re.compile(r"^\s*<!--\s*END\s+(\S+)\s*-->\s*$")


def _get_raw_content(node: dict) -> tuple[str, str] | None:
    """
    Extract format and content from a RawBlock or RawInline.
    Returns (format, content) or None if not a raw node.
    """
    t = node.get("t")
    if t in ("RawBlock", "RawInline"):
        c = node.get("c", [])
        if len(c) == 2:
            return c[0], c[1]
    return None


def _parse_fence(node: dict) -> tuple[str, str] | None:
    """
    Parse BEGIN/END fence from a raw node.
    Returns ("begin", id) or ("end", id) or None.
    """
    raw = _get_raw_content(node)
    if raw is None:
        return None

    fmt, content = raw
    if fmt != "html":
        return None

    begin_match = BEGIN_PATTERN.match(content)
    if begin_match:
        return ("begin", begin_match.group(1))

    end_match = END_PATTERN.match(content)
    if end_match:
        return ("end", end_match.group(1))

    return None


def _is_wrapper_div(block: dict) -> bool:
    """Check if a block is already a Div with an identifier (wrapper candidate)."""
    if block.get("t") != "Div":
        return False
    c = block.get("c", [])
    if len(c) < 2:
        return False
    attr = c[0]
    if len(attr) >= 1 and attr[0]:
        return True
    return False


def _extract_end_fence_from_para(block: dict) -> tuple[dict | None, tuple[str, str] | None]:
    """
    Check if a Para block ends with a RawInline END fence.

    Returns:
        (modified_block, fence_info) where:
        - modified_block: Para without the END fence (or None if Para becomes empty)
        - fence_info: ("end", id) or None if no END fence found
    """
    if block.get("t") != "Para":
        return (block, None)

    contents = block.get("c", [])
    if not contents:
        return (block, None)

    # Check if the last element (ignoring trailing Space/SoftBreak) is an END fence
    # Work backwards to find the last RawInline
    end_idx = len(contents) - 1
    while end_idx >= 0:
        elem = contents[end_idx]
        if elem.get("t") == "RawInline":
            fence = _parse_fence(elem)
            if fence and fence[0] == "end":
                # Found END fence - strip it and any preceding SoftBreak/Space
                new_contents = contents[:end_idx]
                # Strip trailing SoftBreak/Space
                while new_contents and new_contents[-1].get("t") in ("SoftBreak", "Space"):
                    new_contents.pop()

                if not new_contents:
                    return (None, fence)

                return ({"t": "Para", "c": new_contents}, fence)
            else:
                # RawInline but not an END fence
                return (block, None)
        elif elem.get("t") in ("SoftBreak", "Space"):
            end_idx -= 1
            continue
        else:
            # Non-raw, non-whitespace element at end
            return (block, None)

    return (block, None)


def _is_begin_fence_block(block: dict) -> tuple[str, str] | None:
    """
    Check if a block is a BEGIN fence.
    Returns ("begin", id) or None.
    """
    if block.get("t") == "RawBlock":
        fence = _parse_fence(block)
        if fence and fence[0] == "begin":
            return fence
        return None

    # Check for Para containing only a BEGIN fence
    if block.get("t") == "Para":
        contents = block.get("c", [])
        # Filter to non-whitespace elements
        non_ws = [c for c in contents if c.get("t") not in ("Space", "SoftBreak")]
        if len(non_ws) == 1 and non_ws[0].get("t") == "RawInline":
            fence = _parse_fence(non_ws[0])
            if fence and fence[0] == "begin":
                return fence

    return None


def _is_end_fence_block(block: dict) -> tuple[str, str] | None:
    """
    Check if a block is a standalone END fence (RawBlock or Para with only RawInline).
    Returns ("end", id) or None.
    """
    if block.get("t") == "RawBlock":
        fence = _parse_fence(block)
        if fence and fence[0] == "end":
            return fence
        return None

    # Check for Para containing only an END fence
    if block.get("t") == "Para":
        contents = block.get("c", [])
        non_ws = [c for c in contents if c.get("t") not in ("Space", "SoftBreak")]
        if len(non_ws) == 1 and non_ws[0].get("t") == "RawInline":
            fence = _parse_fence(non_ws[0])
            if fence and fence[0] == "end":
                return fence

    return None


def apply(ast: dict) -> dict:
    """
    Apply the Markdown adapter to a Pandoc AST.

    Identifies HTML comment fences and converts them into wrapper Div candidates.
    Passes through existing Pandoc fenced Divs.

    Args:
        ast: A Pandoc AST as a dict (parsed JSON).

    Returns:
        Modified AST with wrapper Div candidates.

    Raises:
        FenceMismatchError: If BEGIN/END don't match.
        FenceOverlapError: If fences are nested (v1 disallows nesting).
    """
    blocks = ast.get("blocks", [])
    new_blocks = _process_blocks(blocks)
    result = ast.copy()
    result["blocks"] = new_blocks
    return result


def _process_blocks(blocks: list[dict]) -> list[dict]:
    """
    Process a list of blocks, converting fenced regions to Divs.

    Returns a new list of blocks with fence regions wrapped.
    """
    result = []
    i = 0

    while i < len(blocks):
        block = blocks[i]

        # Check for BEGIN fence (block-level)
        begin_fence = _is_begin_fence_block(block)

        if begin_fence:
            begin_id = begin_fence[1]
            # Find matching END fence
            inner_blocks = []
            j = i + 1
            found_end = False

            while j < len(blocks):
                inner_block = blocks[j]

                # Check for standalone BEGIN (error - nesting)
                inner_begin = _is_begin_fence_block(inner_block)
                if inner_begin:
                    raise FenceOverlapError(begin_id, inner_begin[1])

                # Check for standalone END fence
                inner_end = _is_end_fence_block(inner_block)
                if inner_end:
                    end_id = inner_end[1]
                    if end_id != begin_id:
                        raise FenceMismatchError(begin_id, end_id)
                    found_end = True
                    break

                # Check for END fence embedded in Para
                modified_block, end_fence = _extract_end_fence_from_para(inner_block)
                if end_fence:
                    end_id = end_fence[1]
                    if end_id != begin_id:
                        raise FenceMismatchError(begin_id, end_id)
                    # Add the modified block (without the END fence) if not empty
                    if modified_block:
                        inner_blocks.append(modified_block)
                    found_end = True
                    break

                inner_blocks.append(inner_block)
                j += 1

            if not found_end:
                raise FenceMismatchError(begin_id)

            # Create wrapper Div
            wrapper_div = {
                "t": "Div",
                "c": [
                    [begin_id, [], []],
                    inner_blocks  # Don't recurse - nesting is disallowed in v1
                ]
            }
            result.append(wrapper_div)
            i = j + 1

        elif _is_wrapper_div(block):
            # Existing Pandoc fenced Div - pass through as wrapper candidate
            div_content = block["c"]
            attr = div_content[0]
            inner = div_content[1] if len(div_content) > 1 else []
            new_div = {
                "t": "Div",
                "c": [attr, _process_blocks(inner)]
            }
            result.append(new_div)
            i += 1

        else:
            # Regular block - pass through
            result.append(block)
            i += 1

    return result
