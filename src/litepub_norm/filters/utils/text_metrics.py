"""Text size metrics for presentation decisions."""

from __future__ import annotations

from typing import Any


def count_codeblock_lines(codeblock: dict[str, Any]) -> int:
    """
    Count the number of lines in a CodeBlock.

    Args:
        codeblock: Pandoc CodeBlock node

    Returns:
        Number of lines (0 if not a valid CodeBlock)
    """
    if not isinstance(codeblock, dict) or codeblock.get("t") != "CodeBlock":
        return 0

    content = codeblock.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        return 0

    code_text = content[1]
    if not isinstance(code_text, str):
        return 0

    return code_text.count("\n") + 1 if code_text else 0


def count_codeblock_chars(codeblock: dict[str, Any]) -> int:
    """
    Count the number of characters in a CodeBlock.

    Args:
        codeblock: Pandoc CodeBlock node

    Returns:
        Number of characters (0 if not a valid CodeBlock)
    """
    if not isinstance(codeblock, dict) or codeblock.get("t") != "CodeBlock":
        return 0

    content = codeblock.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        return 0

    code_text = content[1]
    if not isinstance(code_text, str):
        return 0

    return len(code_text)


def estimate_block_chars(block: dict[str, Any]) -> int:
    """
    Estimate the character count of a block (best-effort).

    Works on various block types:
    - Para, Plain: Sum of inline text
    - CodeBlock: Code content length
    - BulletList, OrderedList: Sum of items
    - Div: Sum of contained blocks

    Args:
        block: Pandoc block node

    Returns:
        Estimated character count
    """
    if not isinstance(block, dict):
        return 0

    block_type = block.get("t", "")
    content = block.get("c")

    if block_type == "CodeBlock":
        return count_codeblock_chars(block)

    if block_type in ("Para", "Plain"):
        return _estimate_inlines_chars(content) if isinstance(content, list) else 0

    if block_type in ("BulletList", "OrderedList"):
        if isinstance(content, list):
            total = 0
            for item in content:
                if isinstance(item, list):
                    for inner_block in item:
                        total += estimate_block_chars(inner_block)
            return total
        return 0

    if block_type == "Div":
        if isinstance(content, list) and len(content) >= 2:
            inner_blocks = content[1]
            if isinstance(inner_blocks, list):
                return sum(estimate_block_chars(b) for b in inner_blocks)
        return 0

    if block_type == "BlockQuote":
        if isinstance(content, list):
            return sum(estimate_block_chars(b) for b in content)
        return 0

    if block_type == "Header":
        # [level, attr, inlines]
        if isinstance(content, list) and len(content) >= 3:
            return _estimate_inlines_chars(content[2])
        return 0

    if block_type == "Table":
        # Tables are complex; return a rough estimate
        return 100  # Placeholder

    return 0


def _estimate_inlines_chars(inlines: list[Any]) -> int:
    """Estimate character count from a list of inline elements."""
    if not isinstance(inlines, list):
        return 0

    total = 0
    for inline in inlines:
        if not isinstance(inline, dict):
            continue

        inline_type = inline.get("t", "")
        content = inline.get("c")

        if inline_type == "Str":
            if isinstance(content, str):
                total += len(content)
        elif inline_type == "Space":
            total += 1
        elif inline_type == "SoftBreak":
            total += 1
        elif inline_type == "LineBreak":
            total += 1
        elif inline_type in ("Emph", "Strong", "Strikeout", "Superscript",
                             "Subscript", "SmallCaps", "Underline"):
            if isinstance(content, list):
                total += _estimate_inlines_chars(content)
        elif inline_type == "Link":
            # [attr, inlines, target]
            if isinstance(content, list) and len(content) >= 2:
                total += _estimate_inlines_chars(content[1])
        elif inline_type == "Span":
            # [attr, inlines]
            if isinstance(content, list) and len(content) >= 2:
                total += _estimate_inlines_chars(content[1])
        elif inline_type == "Code":
            # [attr, text]
            if isinstance(content, list) and len(content) >= 2:
                if isinstance(content[1], str):
                    total += len(content[1])

    return total


def estimate_div_blocks(div: dict[str, Any]) -> int:
    """
    Count the number of blocks inside a Div.

    Args:
        div: Pandoc Div node

    Returns:
        Number of contained blocks (0 if not a valid Div)
    """
    if not isinstance(div, dict) or div.get("t") != "Div":
        return 0

    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        return 0

    inner_blocks = content[1]
    if not isinstance(inner_blocks, list):
        return 0

    return len(inner_blocks)
