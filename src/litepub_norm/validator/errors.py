"""Validation-specific error types.

Re-exports ValidationError from resolver.errors for backward compatibility.
"""

from ..resolver.errors import ValidationError

__all__ = ["ValidationError"]
