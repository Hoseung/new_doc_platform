"""Generic Pandoc AST walker for validation.

This module provides a complete traversal of Pandoc AST nodes,
ensuring no content can bypass validation by being nested in untraversed nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Iterator

from ..errors import ValidationError


class NodeContext(Enum):
    """Context in which a node appears."""

    BLOCK = auto()
    INLINE = auto()
    META = auto()


@dataclass(frozen=True)
class WalkContext:
    """Context passed to walker callbacks."""

    semantic_id: str
    node_type: str
    context: NodeContext
    path: str  # e.g., "Table.c[4][0].c[3][0].c[1][0]"
    depth: int


# Node type classification for traversal
# Based on pandoc-types: https://hackage.haskell.org/package/pandoc-types

# Block types and their content structure
BLOCK_TYPES: dict[str, list[str]] = {
    "Plain": ["[Inline]"],
    "Para": ["[Inline]"],
    "LineBlock": ["[[Inline]]"],
    "CodeBlock": ["Attr", "Text"],
    "RawBlock": ["Format", "Text"],
    "BlockQuote": ["[Block]"],
    "OrderedList": ["ListAttributes", "[[Block]]"],
    "BulletList": ["[[Block]]"],
    "DefinitionList": ["[([Inline], [[Block]])]"],
    "Header": ["Int", "Attr", "[Inline]"],
    "HorizontalRule": [],
    "Table": ["Attr", "Caption", "[ColSpec]", "TableHead", "[TableBody]", "TableFoot"],
    "Figure": ["Attr", "Caption", "[Block]"],
    "Div": ["Attr", "[Block]"],
}

# Inline types and their content structure
INLINE_TYPES: dict[str, list[str]] = {
    "Str": ["Text"],
    "Emph": ["[Inline]"],
    "Underline": ["[Inline]"],
    "Strong": ["[Inline]"],
    "Strikeout": ["[Inline]"],
    "Superscript": ["[Inline]"],
    "Subscript": ["[Inline]"],
    "SmallCaps": ["[Inline]"],
    "Quoted": ["QuoteType", "[Inline]"],
    "Cite": ["[Citation]", "[Inline]"],
    "Code": ["Attr", "Text"],
    "Space": [],
    "SoftBreak": [],
    "LineBreak": [],
    "Math": ["MathType", "Text"],
    "RawInline": ["Format", "Text"],
    "Link": ["Attr", "[Inline]", "Target"],
    "Image": ["Attr", "[Inline]", "Target"],
    "Note": ["[Block]"],
    "Span": ["Attr", "[Inline]"],
}

# Table-specific types
TABLE_TYPES = {
    "TableHead": ["Attr", "[Row]"],
    "TableBody": ["Attr", "RowHeadColumns", "[Row]", "[Row]"],
    "TableFoot": ["Attr", "[Row]"],
    "Row": ["Attr", "[Cell]"],
    "Cell": ["Attr", "Alignment", "RowSpan", "ColSpan", "[Block]"],
}

# Caption structure
CAPTION_STRUCTURE = ["ShortCaption", "[Block]"]

# All node types
ALL_BLOCK_TYPES = set(BLOCK_TYPES.keys())
ALL_INLINE_TYPES = set(INLINE_TYPES.keys())
ALL_TABLE_TYPES = set(TABLE_TYPES.keys())


def walk_pandoc(
    node: Any,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    *,
    context: NodeContext = NodeContext.BLOCK,
    path: str = "",
    depth: int = 0,
) -> None:
    """
    Walk a Pandoc AST node recursively, calling callback on every node.

    This ensures complete traversal - no content can be hidden in unvisited nodes.

    Args:
        node: The AST node to walk.
        callback: Function called for each node with (node, context).
        semantic_id: Semantic ID for error messages.
        context: Whether we're in block or inline context.
        path: Path to this node for error messages.
        depth: Current recursion depth.
    """
    if depth > 100:
        raise ValidationError(
            "AST nesting too deep (>100 levels)",
            code="VAL_PANDOC_TOO_DEEP",
            semantic_id=semantic_id,
            ast_path=path,
        )

    if node is None:
        return

    # Handle lists
    if isinstance(node, list):
        for i, item in enumerate(node):
            item_path = f"{path}[{i}]"
            walk_pandoc(item, callback, semantic_id, context=context, path=item_path, depth=depth + 1)
        return

    # Handle primitives
    if isinstance(node, (str, int, float, bool)):
        return

    # Handle dict nodes (the main Pandoc AST structure)
    if isinstance(node, dict):
        node_type = node.get("t", "")

        # Build context for callback
        walk_ctx = WalkContext(
            semantic_id=semantic_id,
            node_type=node_type,
            context=context,
            path=path,
            depth=depth,
        )

        # Call the callback
        callback(node, walk_ctx)

        # Get content to traverse
        content = node.get("c")
        if content is None:
            return

        # Determine context for children
        child_context = context
        if node_type in ALL_BLOCK_TYPES:
            child_context = NodeContext.BLOCK
        elif node_type in ALL_INLINE_TYPES:
            child_context = NodeContext.INLINE

        # Traverse based on node type
        content_path = f"{path}.c" if path else "c"

        if node_type in ("Plain", "Para"):
            # [Inline]
            walk_pandoc(content, callback, semantic_id, context=NodeContext.INLINE, path=content_path, depth=depth + 1)

        elif node_type == "LineBlock":
            # [[Inline]]
            for i, line in enumerate(content):
                walk_pandoc(line, callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[{i}]", depth=depth + 1)

        elif node_type == "BlockQuote":
            # [Block]
            walk_pandoc(content, callback, semantic_id, context=NodeContext.BLOCK, path=content_path, depth=depth + 1)

        elif node_type in ("BulletList",):
            # [[Block]]
            for i, item in enumerate(content):
                walk_pandoc(item, callback, semantic_id, context=NodeContext.BLOCK, path=f"{content_path}[{i}]", depth=depth + 1)

        elif node_type == "OrderedList":
            # [ListAttributes, [[Block]]]
            if len(content) >= 2:
                items = content[1]
                for i, item in enumerate(items):
                    walk_pandoc(item, callback, semantic_id, context=NodeContext.BLOCK, path=f"{content_path}[1][{i}]", depth=depth + 1)

        elif node_type == "DefinitionList":
            # [([Inline], [[Block]])]
            for i, (term, defs) in enumerate(content):
                walk_pandoc(term, callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[{i}][0]", depth=depth + 1)
                for j, def_blocks in enumerate(defs):
                    walk_pandoc(def_blocks, callback, semantic_id, context=NodeContext.BLOCK, path=f"{content_path}[{i}][1][{j}]", depth=depth + 1)

        elif node_type == "Header":
            # [Int, Attr, [Inline]]
            if len(content) >= 3:
                walk_pandoc(content[2], callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[2]", depth=depth + 1)

        elif node_type == "Table":
            # [Attr, Caption, [ColSpec], TableHead, [TableBody], TableFoot]
            _walk_table(content, callback, semantic_id, content_path, depth)

        elif node_type == "Figure":
            # [Attr, Caption, [Block]]
            if len(content) >= 3:
                # Caption: [ShortCaption, [Block]]
                if len(content[1]) >= 2:
                    walk_pandoc(content[1][1], callback, semantic_id, context=NodeContext.BLOCK, path=f"{content_path}[1][1]", depth=depth + 1)
                # Figure content
                walk_pandoc(content[2], callback, semantic_id, context=NodeContext.BLOCK, path=f"{content_path}[2]", depth=depth + 1)

        elif node_type == "Div":
            # [Attr, [Block]]
            if len(content) >= 2:
                walk_pandoc(content[1], callback, semantic_id, context=NodeContext.BLOCK, path=f"{content_path}[1]", depth=depth + 1)

        # Inline types with nested content
        elif node_type in ("Emph", "Underline", "Strong", "Strikeout", "Superscript", "Subscript", "SmallCaps"):
            # [Inline]
            walk_pandoc(content, callback, semantic_id, context=NodeContext.INLINE, path=content_path, depth=depth + 1)

        elif node_type == "Quoted":
            # [QuoteType, [Inline]]
            if len(content) >= 2:
                walk_pandoc(content[1], callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[1]", depth=depth + 1)

        elif node_type == "Cite":
            # [[Citation], [Inline]]
            if len(content) >= 2:
                walk_pandoc(content[1], callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[1]", depth=depth + 1)

        elif node_type in ("Link", "Image"):
            # [Attr, [Inline], Target]
            if len(content) >= 2:
                walk_pandoc(content[1], callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[1]", depth=depth + 1)

        elif node_type == "Note":
            # [Block]
            walk_pandoc(content, callback, semantic_id, context=NodeContext.BLOCK, path=content_path, depth=depth + 1)

        elif node_type == "Span":
            # [Attr, [Inline]]
            if len(content) >= 2:
                walk_pandoc(content[1], callback, semantic_id, context=NodeContext.INLINE, path=f"{content_path}[1]", depth=depth + 1)

        # Table structure types
        elif node_type in ("TableHead", "TableFoot"):
            _walk_table_head_foot(content, callback, semantic_id, content_path, depth)

        elif node_type == "TableBody":
            _walk_table_body(content, callback, semantic_id, content_path, depth)

        elif node_type == "Row":
            _walk_row(content, callback, semantic_id, content_path, depth)

        elif node_type == "Cell":
            _walk_cell(content, callback, semantic_id, content_path, depth)


def _walk_table(
    content: list,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    path: str,
    depth: int,
) -> None:
    """Walk a Table's content array."""
    if len(content) < 6:
        return

    # c[1]: Caption [ShortCaption, [Block]]
    caption = content[1]
    if isinstance(caption, list) and len(caption) >= 2:
        walk_pandoc(caption[1], callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[1][1]", depth=depth + 1)

    # c[3]: TableHead
    table_head = content[3]
    if isinstance(table_head, dict):
        walk_pandoc(table_head, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[3]", depth=depth + 1)

    # c[4]: [TableBody]
    table_bodies = content[4]
    if isinstance(table_bodies, list):
        for i, body in enumerate(table_bodies):
            walk_pandoc(body, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[4][{i}]", depth=depth + 1)

    # c[5]: TableFoot
    table_foot = content[5]
    if isinstance(table_foot, dict):
        walk_pandoc(table_foot, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[5]", depth=depth + 1)


def _walk_table_head_foot(
    content: list,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    path: str,
    depth: int,
) -> None:
    """Walk TableHead or TableFoot content: [Attr, [Row]]."""
    if len(content) < 2:
        return

    rows = content[1]
    if isinstance(rows, list):
        for i, row in enumerate(rows):
            walk_pandoc(row, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[1][{i}]", depth=depth + 1)


def _walk_table_body(
    content: list,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    path: str,
    depth: int,
) -> None:
    """Walk TableBody content: [Attr, RowHeadColumns, [Row], [Row]]."""
    if len(content) < 4:
        return

    # Intermediate head rows
    intermediate_rows = content[2]
    if isinstance(intermediate_rows, list):
        for i, row in enumerate(intermediate_rows):
            walk_pandoc(row, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[2][{i}]", depth=depth + 1)

    # Body rows
    body_rows = content[3]
    if isinstance(body_rows, list):
        for i, row in enumerate(body_rows):
            walk_pandoc(row, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[3][{i}]", depth=depth + 1)


def _walk_row(
    content: list,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    path: str,
    depth: int,
) -> None:
    """Walk Row content: [Attr, [Cell]]."""
    if len(content) < 2:
        return

    cells = content[1]
    if isinstance(cells, list):
        for i, cell in enumerate(cells):
            walk_pandoc(cell, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[1][{i}]", depth=depth + 1)


def _walk_cell(
    content: list,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    path: str,
    depth: int,
) -> None:
    """Walk Cell content: [Attr, Alignment, RowSpan, ColSpan, [Block]]."""
    if len(content) < 5:
        return

    blocks = content[4]
    if isinstance(blocks, list):
        walk_pandoc(blocks, callback, semantic_id, context=NodeContext.BLOCK, path=f"{path}[4]", depth=depth + 1)


def collect_all_types(node: Any, semantic_id: str) -> set[str]:
    """Collect all node types found in an AST subtree."""
    types: set[str] = set()

    def collector(n: Any, ctx: WalkContext) -> None:
        if ctx.node_type:
            types.add(ctx.node_type)

    walk_pandoc(node, collector, semantic_id)
    return types


def find_nodes_by_type(node: Any, target_types: set[str], semantic_id: str) -> list[tuple[Any, WalkContext]]:
    """Find all nodes of specified types in an AST subtree."""
    found: list[tuple[Any, WalkContext]] = []

    def finder(n: Any, ctx: WalkContext) -> None:
        if ctx.node_type in target_types:
            found.append((n, ctx))

    walk_pandoc(node, finder, semantic_id)
    return found
