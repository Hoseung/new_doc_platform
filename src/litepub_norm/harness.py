"""
Normalization harness - the main pipeline driver.

Provides high-level functions that orchestrate:
parse -> adapt -> normalize -> serialize
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pypandoc

from .registry import Registry
from . import md_adapter
from . import rst_adapter
from . import core_normalize
from .serialize import serialize


def parse_to_pandoc_ast(text: str, fmt: str) -> dict:
    """
    Parse text to Pandoc AST using pypandoc.

    Args:
        text: Source text content.
        fmt: Format string ("markdown" or "rst").

    Returns:
        Pandoc AST as a dict.
    """
    # pypandoc.convert_text returns JSON string when output format is "json"
    json_str = pypandoc.convert_text(text, "json", format=fmt)
    return json.loads(json_str)


def adapt(fmt: str, ast: dict) -> dict:
    """
    Apply format-specific adapter to identify semantic block candidates.

    Args:
        fmt: Format string ("markdown", "md", "rst").
        ast: Pandoc AST.

    Returns:
        AST with wrapper Div candidates.
    """
    fmt_lower = fmt.lower()
    if fmt_lower in ("markdown", "md"):
        return md_adapter.apply(ast)
    elif fmt_lower == "rst":
        return rst_adapter.apply(ast)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def normalize(
    ast: dict,
    registry: Registry,
    mode: str = "strict"
) -> dict:
    """
    Apply core normalization to produce canonical AST.

    Args:
        ast: AST with wrapper Div candidates.
        registry: Registry for metadata lookup.
        mode: "strict" or "draft".

    Returns:
        Normalized canonical AST.
    """
    return core_normalize.apply(ast, registry, mode)


def normalize_text(
    text: str,
    fmt: str,
    registry: Registry | dict | str | Path,
    mode: str = "strict"
) -> dict:
    """
    Full normalization pipeline for text input.

    Args:
        text: Source text content.
        fmt: Format string ("markdown", "md", "rst").
        registry: Registry instance, dict, or path to registry JSON.
        mode: "strict" or "draft".

    Returns:
        Normalized canonical AST.
    """
    # Handle registry argument types
    if isinstance(registry, (str, Path)):
        registry = Registry.from_file(registry, strict=(mode == "strict"))
    elif isinstance(registry, dict):
        registry = Registry.from_dict(registry, strict=(mode == "strict"))

    # For RST, we need to preprocess before parsing
    if fmt.lower() == "rst":
        text = rst_adapter.preprocess_rst(text)
        # After preprocessing, RST directives become HTML comment fences
        # which Pandoc's RST reader will preserve as RawBlocks

    # Parse
    ast = parse_to_pandoc_ast(text, fmt)

    # Adapt
    ast = adapt(fmt, ast)

    # Normalize
    ast = normalize(ast, registry, mode)

    return ast


def normalize_file(
    path: str | Path,
    registry: Registry | dict | str | Path,
    mode: str = "strict"
) -> dict:
    """
    Full normalization pipeline for a file.

    Args:
        path: Path to source file (.md or .rst).
        registry: Registry instance, dict, or path to registry JSON.
        mode: "strict" or "draft".

    Returns:
        Normalized canonical AST.
    """
    path = Path(path)

    # Determine format from extension
    ext = path.suffix.lower()
    if ext == ".md":
        fmt = "markdown"
    elif ext == ".rst":
        fmt = "rst"
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Read file
    text = path.read_text(encoding="utf-8")

    return normalize_text(text, fmt, registry, mode)


def normalize_and_serialize(
    path: str | Path,
    registry: Registry | dict | str | Path,
    mode: str = "strict",
    indent: int = 2
) -> str:
    """
    Full pipeline with JSON serialization.

    Args:
        path: Path to source file.
        registry: Registry for metadata lookup.
        mode: "strict" or "draft".
        indent: JSON indentation level.

    Returns:
        Serialized canonical AST as JSON string.
    """
    ast = normalize_file(path, registry, mode)
    return serialize(ast, indent=indent)
