"""
Deterministic JSON serialization for Pandoc AST.

Ensures stable key ordering and attribute ordering for diffable output.
"""

from __future__ import annotations

import json
from typing import Any


def serialize(ast: dict, indent: int = 2) -> str:
    """
    Serialize a Pandoc AST to deterministic JSON.

    Args:
        ast: Pandoc AST as a dict.
        indent: Indentation level for pretty-printing.

    Returns:
        JSON string with stable ordering.
    """
    return json.dumps(ast, indent=indent, ensure_ascii=False, sort_keys=False)


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
