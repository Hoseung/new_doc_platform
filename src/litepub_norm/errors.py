"""Custom exceptions for the normalization pipeline."""


class NormalizationError(Exception):
    """Base exception for normalization errors."""
    pass


class FenceMismatchError(NormalizationError):
    """Raised when BEGIN/END fences don't match."""

    def __init__(self, begin_id: str, end_id: str | None = None):
        if end_id is None:
            msg = f"Unclosed fence: BEGIN {begin_id} has no matching END"
        else:
            msg = f"Fence mismatch: BEGIN {begin_id} closed with END {end_id}"
        super().__init__(msg)
        self.begin_id = begin_id
        self.end_id = end_id


class FenceOverlapError(NormalizationError):
    """Raised when fences overlap or nest (v1 disallows nesting)."""

    def __init__(self, outer_id: str, inner_id: str):
        msg = f"Nested fences not allowed in v1: BEGIN {inner_id} inside open fence {outer_id}"
        super().__init__(msg)
        self.outer_id = outer_id
        self.inner_id = inner_id


class UnknownSemanticIdError(NormalizationError):
    """Raised when a semantic ID is not found in the registry."""

    def __init__(self, semantic_id: str):
        msg = f"Unknown semantic ID: {semantic_id} not found in registry"
        super().__init__(msg)
        self.semantic_id = semantic_id


class RegistryIncompleteError(NormalizationError):
    """Raised when registry entry is missing required fields for a computed block."""

    def __init__(self, semantic_id: str, missing_fields: list[str]):
        fields_str = ", ".join(missing_fields)
        msg = f"Incomplete registry entry for {semantic_id}: missing {fields_str}"
        super().__init__(msg)
        self.semantic_id = semantic_id
        self.missing_fields = missing_fields


class DuplicateIdError(NormalizationError):
    """Raised when the same semantic ID appears multiple times."""

    def __init__(self, semantic_id: str):
        msg = f"Duplicate semantic ID: {semantic_id}"
        super().__init__(msg)
        self.semantic_id = semantic_id
