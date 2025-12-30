"""Top-level resolution API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ResolutionConfig
from .registry import RegistrySnapshot, load_registry
from .plan import ResolutionPlan, build_plan
from .apply import apply_plan


def resolve(
    ast: dict,
    registry: RegistrySnapshot | str | Path,
    config: ResolutionConfig | None = None,
) -> dict:
    """
    Resolve all computed blocks in a normalized AST.

    This is the main entry point for the resolution stage.

    Args:
        ast: Normalized Pandoc AST with placeholder tokens.
        registry: AARC registry (snapshot or path to JSON file).
        config: Resolution configuration (defaults to strict mode).

    Returns:
        Resolved AST with placeholders replaced by computed content.

    Raises:
        RegistryError: If registry cannot be loaded or entries missing.
        PlaceholderError: If placeholder rules violated.
        PayloadError: If any payload cannot be loaded.
        ValidationError: If any payload is invalid.
        KindMismatchError: If wrapper kind doesn't match registry.
    """
    # Default config
    if config is None:
        config = ResolutionConfig()

    # Load registry if path provided
    if isinstance(registry, (str, Path)):
        registry = load_registry(registry)

    # Build resolution plan
    plan = build_plan(ast, registry, config)

    # Apply plan
    return apply_plan(ast, plan, registry, config)


def build_resolution_plan(
    ast: dict,
    registry: RegistrySnapshot | str | Path,
    config: ResolutionConfig | None = None,
) -> ResolutionPlan:
    """
    Build a resolution plan without applying it.

    Useful for inspection, logging, or custom resolution logic.

    Args:
        ast: Normalized Pandoc AST with placeholder tokens.
        registry: AARC registry (snapshot or path to JSON file).
        config: Resolution configuration.

    Returns:
        ResolutionPlan with items to resolve.
    """
    if config is None:
        config = ResolutionConfig()

    if isinstance(registry, (str, Path)):
        registry = load_registry(registry)

    return build_plan(ast, registry, config)
