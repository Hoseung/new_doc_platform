"""Resolution plan builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import ResolutionConfig
from .errors import PlaceholderError, KindMismatchError, RegistryError
from .registry import RegistrySnapshot, RegistryEntry
from .placeholders import (
    Placeholder,
    find_placeholders_in_blocks,
    ARTIFACT_TYPE_TO_KIND,
)


@dataclass(frozen=True)
class ResolutionItem:
    """A single item to resolve."""

    semantic_id: str
    entry: RegistryEntry
    wrapper_index: int  # Index in top-level blocks
    placeholder_index: int  # Index within wrapper content
    placeholder: Placeholder


@dataclass
class ResolutionPlan:
    """Plan for resolving all computed blocks in an AST."""

    items: list[ResolutionItem]

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


def _get_div_id(div: dict) -> str | None:
    """Extract the identifier from a Div block."""
    if div.get("t") != "Div":
        return None
    c = div.get("c", [])
    if len(c) < 2:
        return None
    attr = c[0]
    if len(attr) >= 1 and attr[0]:
        return attr[0]
    return None


def _get_div_attrs(div: dict) -> dict[str, str]:
    """Extract attributes from a Div block as a dict."""
    c = div.get("c", [])
    if len(c) < 1:
        return {}
    attr = c[0]
    if len(attr) < 3:
        return {}
    # attr[2] is list of [key, value] pairs
    return {k: v for k, v in attr[2]}


def _get_div_content(div: dict) -> list[dict]:
    """Get the content blocks from a Div."""
    c = div.get("c", [])
    if len(c) < 2:
        return []
    return c[1]


def _is_computed_wrapper(div: dict) -> bool:
    """Check if a Div is a computed block wrapper."""
    attrs = _get_div_attrs(div)
    role = attrs.get("role", "")
    return role == "computed"


def build_plan(
    ast: dict,
    registry: RegistrySnapshot,
    config: ResolutionConfig,
) -> ResolutionPlan:
    """
    Build a resolution plan by analyzing the AST.

    Finds all computed wrapper Divs, locates their placeholders,
    and matches them to registry entries.

    Args:
        ast: Normalized Pandoc AST.
        registry: AARC registry snapshot.
        config: Resolution configuration.

    Returns:
        ResolutionPlan with items to resolve.

    Raises:
        PlaceholderError: If placeholder rules violated.
        RegistryError: If registry entry missing or incompatible.
        KindMismatchError: If wrapper kind doesn't match registry.
    """
    items: list[ResolutionItem] = []
    blocks = ast.get("blocks", [])

    for wrapper_idx, block in enumerate(blocks):
        if block.get("t") != "Div":
            continue

        if not _is_computed_wrapper(block):
            continue

        semantic_id = _get_div_id(block)
        if not semantic_id:
            continue

        attrs = _get_div_attrs(block)
        wrapper_kind = attrs.get("kind", "")

        # Find placeholders in wrapper content
        content = _get_div_content(block)
        placeholders = find_placeholders_in_blocks(content)

        # Enforce exactly one placeholder rule
        if len(placeholders) == 0:
            raise PlaceholderError(
                f"No placeholder found in computed wrapper",
                semantic_id=semantic_id,
            )
        if len(placeholders) > 1:
            raise PlaceholderError(
                f"Multiple placeholders found in computed wrapper ({len(placeholders)})",
                semantic_id=semantic_id,
            )

        placeholder, placeholder_idx = placeholders[0]

        # Registry lookup
        try:
            entry = registry.get(semantic_id)
        except RegistryError:
            if config.strict or config.is_strict_target():
                raise
            # In non-strict mode, skip unresolvable entries
            continue

        # Compatibility check: wrapper kind vs registry artifact_type
        expected_kind = ARTIFACT_TYPE_TO_KIND.get(entry.artifact_type, "")
        if placeholder.kind != expected_kind:
            raise KindMismatchError(
                semantic_id=semantic_id,
                wrapper_kind=wrapper_kind,
                registry_type=entry.artifact_type,
            )

        items.append(
            ResolutionItem(
                semantic_id=semantic_id,
                entry=entry,
                wrapper_index=wrapper_idx,
                placeholder_index=placeholder_idx,
                placeholder=placeholder,
            )
        )

    return ResolutionPlan(items=items)
