"""litepub_norm - AST normalization pipeline for documentation platform."""

from .harness import normalize_file, normalize_text
from .registry import Registry
from .errors import (
    NormalizationError,
    FenceMismatchError,
    FenceOverlapError,
    UnknownSemanticIdError,
    RegistryIncompleteError,
)

__all__ = [
    "normalize_file",
    "normalize_text",
    "Registry",
    "NormalizationError",
    "FenceMismatchError",
    "FenceOverlapError",
    "UnknownSemanticIdError",
    "RegistryIncompleteError",
]
