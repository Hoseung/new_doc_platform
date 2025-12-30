"""Resolution-specific error types."""


class ResolutionError(Exception):
    """Base exception for resolution errors."""

    def __init__(
        self,
        message: str,
        semantic_id: str | None = None,
        path: str | None = None,
    ):
        super().__init__(message)
        self.semantic_id = semantic_id
        self.path = path

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.semantic_id:
            parts.append(f"[id={self.semantic_id}]")
        if self.path:
            parts.append(f"[path={self.path}]")
        return " ".join(parts)


class RegistryError(ResolutionError):
    """Error in registry loading or lookup."""

    pass


class PlaceholderError(ResolutionError):
    """Error in placeholder detection or validation."""

    pass


class PayloadError(ResolutionError):
    """Error loading or parsing payload file."""

    pass


class ValidationError(ResolutionError):
    """Error validating payload content."""

    pass


class HashMismatchError(PayloadError):
    """SHA256 hash mismatch for payload."""

    def __init__(
        self,
        semantic_id: str,
        expected: str,
        actual: str,
        path: str | None = None,
    ):
        message = f"Hash mismatch: expected {expected}, got {actual}"
        super().__init__(message, semantic_id=semantic_id, path=path)
        self.expected = expected
        self.actual = actual


class KindMismatchError(ResolutionError):
    """Mismatch between wrapper kind and registry artifact_type."""

    def __init__(
        self,
        semantic_id: str,
        wrapper_kind: str,
        registry_type: str,
    ):
        message = f"Kind mismatch: wrapper expects '{wrapper_kind}', registry has '{registry_type}'"
        super().__init__(message, semantic_id=semantic_id)
        self.wrapper_kind = wrapper_kind
        self.registry_type = registry_type
