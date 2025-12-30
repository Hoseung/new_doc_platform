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

# Resolution module
from .resolver import (
    resolve,
    build_resolution_plan,
    load_registry,
    ResolutionConfig,
    ResolutionLimits,
    RegistrySnapshot,
    RegistryEntry,
    ResolutionPlan,
    ResolutionError,
    RegistryError,
    PlaceholderError,
    PayloadError,
    ValidationError,
    HashMismatchError,
    KindMismatchError,
)

__all__ = [
    # Normalization
    "normalize_file",
    "normalize_text",
    "Registry",
    "NormalizationError",
    "FenceMismatchError",
    "FenceOverlapError",
    "UnknownSemanticIdError",
    "RegistryIncompleteError",
    # Resolution
    "resolve",
    "build_resolution_plan",
    "load_registry",
    "ResolutionConfig",
    "ResolutionLimits",
    "RegistrySnapshot",
    "RegistryEntry",
    "ResolutionPlan",
    "ResolutionError",
    "RegistryError",
    "PlaceholderError",
    "PayloadError",
    "ValidationError",
    "HashMismatchError",
    "KindMismatchError",
]
