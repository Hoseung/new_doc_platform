"""Format-specific adapters for document ingestion.

Adapters convert format-specific constructs into canonical Div wrappers
recognized by the normalizer.

- markdown: HTML comment fences → Div blocks
- rst: RST directives → Div blocks
"""

from . import markdown
from . import rst

__all__ = [
    "markdown",
    "rst",
]
