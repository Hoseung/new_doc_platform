"""
Deterministic JSON serialization for Pandoc AST.

Produces compact, human-readable format matching the expected golden files.
"""

from __future__ import annotations

import json
from typing import Any


def _inline(obj: Any) -> str:
    """Serialize object to compact single-line JSON."""
    return json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))


def _serialize_block(block: dict, indent: str = "    ") -> str:
    """
    Serialize a single block to compact format.

    Simple blocks (Header, Para, Plain, etc.) → single line
    Div blocks → structured multi-line with compact inner content
    """
    block_type = block.get("t", "")

    if block_type == "Div":
        return _serialize_div(block, indent)
    else:
        # Simple block - single line
        return _inline(block)


def _serialize_div(div: dict, indent: str = "    ") -> str:
    """Serialize a Div block with structured formatting."""
    c = div.get("c", [])
    if len(c) < 2:
        return _inline(div)

    attr = c[0]  # [id, classes, attrs]
    content = c[1]  # list of blocks

    lines = []
    lines.append("{")
    lines.append(f'{indent}"t": "Div",')
    lines.append(f'{indent}"c": [')

    # Format attributes
    if len(attr) >= 3:
        sem_id = attr[0]
        classes = attr[1]
        attrs = attr[2]

        # Format attr list with each attribute on its own line
        lines.append(f'{indent}  ["{sem_id}", {_inline(classes)}, [')
        for i, kv in enumerate(attrs):
            comma = "," if i < len(attrs) - 1 else ""
            lines.append(f'{indent}    {_inline(kv)}{comma}')
        lines.append(f'{indent}  ]],')
    else:
        lines.append(f'{indent}  {_inline(attr)},')

    # Format content blocks
    lines.append(f'{indent}  [')
    for i, block in enumerate(content):
        comma = "," if i < len(content) - 1 else ""
        block_str = _serialize_block(block, indent + "    ")
        # Check if it's a simple single-line block
        if "\n" not in block_str:
            lines.append(f'{indent}    {block_str}{comma}')
        else:
            # Multi-line block (nested Div)
            block_lines = block_str.split("\n")
            for j, bl in enumerate(block_lines):
                if j == len(block_lines) - 1:
                    lines.append(f'{indent}    {bl}{comma}')
                else:
                    lines.append(f'{indent}    {bl}')
        # Add blank line between blocks for readability (except after last)
        if i < len(content) - 1:
            lines.append("")
    lines.append(f'{indent}  ]')

    lines.append(f'{indent}]')
    lines.append("}")

    return "\n".join(lines)


def serialize(ast: dict, indent: int = 2) -> str:
    """
    Serialize a Pandoc AST to compact JSON format.

    Produces human-readable format with:
    - Simple blocks on single lines
    - Div blocks with structured multi-line format
    - Attributes each on their own line

    Args:
        ast: Pandoc AST as a dict.
        indent: Base indentation (default 2 spaces).

    Returns:
        Compact JSON string.
    """
    base_indent = " " * indent

    lines = []
    lines.append("{")

    # pandoc-api-version
    api_version = ast.get("pandoc-api-version", [])
    lines.append(f'{base_indent}"pandoc-api-version": {_inline(api_version)},')

    # meta
    meta = ast.get("meta", {})
    lines.append(f'{base_indent}"meta": {_inline(meta)},')

    # blocks
    blocks = ast.get("blocks", [])
    lines.append(f'{base_indent}"blocks": [')

    for i, block in enumerate(blocks):
        comma = "," if i < len(blocks) - 1 else ""
        block_str = _serialize_block(block, base_indent + "  ")

        if "\n" not in block_str:
            # Simple single-line block
            lines.append(f'{base_indent}  {block_str}{comma}')
        else:
            # Multi-line block (Div)
            block_lines = block_str.split("\n")
            for j, bl in enumerate(block_lines):
                if j == len(block_lines) - 1:
                    lines.append(f'{base_indent}  {bl}{comma}')
                else:
                    lines.append(f'{base_indent}  {bl}')

        # Add blank line between blocks for readability (except after last)
        if i < len(blocks) - 1:
            lines.append("")

    lines.append(f'{base_indent}]')
    lines.append("}")

    return "\n".join(lines)


def serialize_to_file(ast: dict, path: str, indent: int = 2) -> None:
    """
    Serialize a Pandoc AST to a JSON file.

    Args:
        ast: Pandoc AST as a dict.
        path: Output file path.
        indent: Indentation level for pretty-printing.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(serialize(ast, indent=indent))
        f.write("\n")
