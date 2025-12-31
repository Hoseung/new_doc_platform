"""Core normalizer - creates canonical AST from adapted input.

The normalizer:
- Enforces wrapper boundary invariants
- Resolves IDs against registry and injects metadata
- Applies defaults (computed → lock=true)
- Cleans up bodies by role
- Injects deterministic placeholders for later resolution
"""

from .harness import normalize_file, normalize_text
from .registry import Registry
from .core import apply as normalize_ast

__all__ = [
    "normalize_file",
    "normalize_text",
    "normalize_ast",
    "Registry",
]
