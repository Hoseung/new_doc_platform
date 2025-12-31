"""
Core normalization module (format-agnostic).

Takes wrapper Div candidates from adapters and produces the canonical wrapper forms:
- Completes metadata via registry
- Enforces wrapper boundaries
- Applies defaults (computed => lock=true)
- Role-based body cleanup
- Injects placeholders for computed blocks
"""

from __future__ import annotations

from typing import Any

from .registry import Registry
from ..errors import DuplicateIdError


# Placeholder markers for computed blocks
PLACEHOLDER_TABLE = "[[COMPUTED:TABLE]]"
PLACEHOLDER_FIGURE = "[[COMPUTED:FIGURE]]"
PLACEHOLDER_METRIC = "[[COMPUTED:METRIC]]"

# Mapping of kind to placeholder
KIND_PLACEHOLDERS = {
    "table": PLACEHOLDER_TABLE,
    "figure": PLACEHOLDER_FIGURE,
    "metric": PLACEHOLDER_METRIC,
}


def apply(ast: dict, registry: Registry, mode: str = "strict") -> dict:
    """
    Apply core normalization to a Pandoc AST with wrapper Div candidates.

    Args:
        ast: Pandoc AST with wrapper Div candidates (from adapter).
        registry: Registry for metadata lookup.
        mode: "strict" (default) or "draft" for validation behavior.

    Returns:
        Normalized canonical AST.

    Raises:
        DuplicateIdError: If same semantic ID appears multiple times.
        UnknownSemanticIdError: If ID not in registry (strict mode).
        RegistryIncompleteError: If required fields missing (strict mode).
    """
    seen_ids: set[str] = set()
    blocks = ast.get("blocks", [])
    new_blocks = _normalize_blocks(blocks, registry, mode, seen_ids)

    result = ast.copy()
    result["blocks"] = new_blocks
    return result


def _normalize_blocks(
    blocks: list[dict],
    registry: Registry,
    mode: str,
    seen_ids: set[str]
) -> list[dict]:
    """Normalize a list of blocks recursively."""
    result = []

    for block in blocks:
        if block.get("t") == "Div":
            normalized = _normalize_div(block, registry, mode, seen_ids)
            result.append(normalized)
        else:
            result.append(block)

    return result


def _normalize_div(
    div: dict,
    registry: Registry,
    mode: str,
    seen_ids: set[str]
) -> dict:
    """
    Normalize a Div block, completing metadata and applying rules.
    """
    c = div.get("c", [])
    if len(c) < 2:
        return div

    attr = c[0]
    content = c[1]

    # Extract identifier
    identifier = attr[0] if len(attr) > 0 else ""

    if not identifier:
        # Not a semantic block wrapper - just recursively process children
        new_content = _normalize_blocks(content, registry, mode, seen_ids)
        return {"t": "Div", "c": [attr, new_content]}

    # Check for duplicate IDs
    if identifier in seen_ids:
        raise DuplicateIdError(identifier)
    seen_ids.add(identifier)

    # Resolve metadata from registry
    metadata = registry.resolve(identifier)

    # Build canonical attributes
    role = metadata.get("role", "")
    kind = metadata.get("kind", "")

    # Canonical attribute list (sorted for determinism)
    attrs = []

    # Add role
    if role:
        attrs.append(["role", role])

    # Add kind
    if kind:
        attrs.append(["kind", kind])

    # Add source (for computed)
    if "source" in metadata:
        attrs.append(["source", metadata["source"]])

    # Add schema (for computed tables/metrics)
    if "schema" in metadata:
        attrs.append(["schema", metadata["schema"]])

    # Add visibility
    if "visibility" in metadata:
        attrs.append(["visibility", metadata["visibility"]])

    # Add lock (default true for computed)
    if role == "computed":
        lock_val = metadata.get("lock", "true")
        attrs.append(["lock", str(lock_val).lower()])

    # Add bind-to for annotations
    if "bind-to" in metadata:
        attrs.append(["bind-to", metadata["bind-to"]])

    # Preserve existing classes
    classes = attr[1] if len(attr) > 1 else []

    # Build new attr structure: [id, classes, attrs]
    new_attr = [identifier, classes, attrs]

    # Process body based on role
    new_content = _process_body(content, role, kind, registry, mode, seen_ids)

    return {"t": "Div", "c": [new_attr, new_content]}


def _process_body(
    content: list[dict],
    role: str,
    kind: str,
    registry: Registry,
    mode: str,
    seen_ids: set[str]
) -> list[dict]:
    """
    Process the body of a semantic block based on its role.

    For computed blocks:
    - Keep prose (Para with text)
    - Remove manually-authored tables/images
    - Add placeholder

    For hybrid/annotation:
    - Keep prose only

    For authored:
    - Preserve as-is
    """
    if role == "computed":
        return _process_computed_body(content, kind, registry, mode, seen_ids)
    elif role == "hybrid":
        return _process_hybrid_body(content, registry, mode, seen_ids)
    else:
        # authored or unknown - preserve and recurse
        return _normalize_blocks(content, registry, mode, seen_ids)


def _process_computed_body(
    content: list[dict],
    kind: str,
    registry: Registry,
    mode: str,
    seen_ids: set[str]
) -> list[dict]:
    """
    Process body of a computed block.

    - Keep Para blocks (prose/captions)
    - Remove Table, Image, Figure blocks (manually authored payload)
    - Add placeholder at the end
    """
    result = []

    for block in content:
        block_type = block.get("t", "")

        # Skip manually-authored computed payload
        if block_type in ("Table", "Image", "Figure"):
            continue

        # Recursively process nested Divs
        if block_type == "Div":
            result.append(_normalize_div(block, registry, mode, seen_ids))
        else:
            result.append(block)

    # Add placeholder for computed content
    placeholder = KIND_PLACEHOLDERS.get(kind, f"[[COMPUTED:{kind.upper()}]]")
    placeholder_block = _make_para([{"t": "Str", "c": placeholder}])
    result.append(placeholder_block)

    return result


def _process_hybrid_body(
    content: list[dict],
    registry: Registry,
    mode: str,
    seen_ids: set[str]
) -> list[dict]:
    """
    Process body of a hybrid/annotation block.

    - Keep prose only (Para, Plain)
    - Recursively process nested structures
    """
    result = []

    for block in content:
        block_type = block.get("t", "")

        # Keep prose blocks
        if block_type in ("Para", "Plain", "Header", "BlockQuote", "BulletList", "OrderedList"):
            result.append(block)
        elif block_type == "Div":
            result.append(_normalize_div(block, registry, mode, seen_ids))
        # Skip Table, Image, Figure, CodeBlock in annotations

    return result


def _make_para(inlines: list[dict]) -> dict:
    """Create a Para block with the given inlines."""
    return {"t": "Para", "c": inlines}
