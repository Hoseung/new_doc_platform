"""Resolution module - replaces placeholders with computed content."""

from .api import resolve, build_resolution_plan
from .config import ResolutionConfig, ResolutionLimits, BuildTarget
from .registry import RegistrySnapshot, RegistryEntry, RegistryRun, load_registry
from .plan import ResolutionPlan, ResolutionItem, build_plan
from .apply import apply_plan
from .errors import (
    ResolutionError,
    RegistryError,
    PlaceholderError,
    PayloadError,
    ValidationError,
    HashMismatchError,
    KindMismatchError,
)

__all__ = [
    # API
    "resolve",
    "build_resolution_plan",
    # Config
    "ResolutionConfig",
    "ResolutionLimits",
    "BuildTarget",
    # Registry
    "RegistrySnapshot",
    "RegistryEntry",
    "RegistryRun",
    "load_registry",
    # Plan
    "ResolutionPlan",
    "ResolutionItem",
    "build_plan",
    "apply_plan",
    # Errors
    "ResolutionError",
    "RegistryError",
    "PlaceholderError",
    "PayloadError",
    "ValidationError",
    "HashMismatchError",
    "KindMismatchError",
]
