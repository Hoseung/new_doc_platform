"""
HTML Theming module for LitePub.

Provides a pluggable theming system with:
- Stable DOM contract (hook points)
- Theme pack format (template + assets)
- Theme resolution and bundling
"""

from .contract import (
    REQUIRED_IDS,
    REQUIRED_CLASSES,
    validate_template_hooks,
)
from .manifest import ThemeManifest, load_manifest
from .resolver import ThemeBundle, resolve_theme, list_available_themes
from .selection import with_theme

__all__ = [
    # Contract
    "REQUIRED_IDS",
    "REQUIRED_CLASSES",
    "validate_template_hooks",
    # Manifest
    "ThemeManifest",
    "load_manifest",
    # Resolver
    "ThemeBundle",
    "resolve_theme",
    "list_available_themes",
    # Selection
    "with_theme",
]
