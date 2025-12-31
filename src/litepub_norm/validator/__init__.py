"""Validation stage - validates AST invariants and contracts.

Validators ensure:
- Payload schemas are correct
- Content is safe (no raw HTML/LaTeX injection)
- Size limits are respected
- Document invariants hold after resolution
"""

from .metric_v1 import validate_metric_v1
from .table_simple_v1 import validate_table_simple_v1, validate_table_simple_optional_fields
from .table_pandoc_v1 import validate_table_pandoc_v1
from .figure_v1 import validate_figure_meta_v1
from .pandoc_walk import walk_pandoc, WalkContext, NodeContext, collect_all_types, find_nodes_by_type
from .document import (
    validate_resolved_document,
    validate_wrapper_content_type,
    DocumentValidationResult,
)

__all__ = [
    # Payload validators
    "validate_metric_v1",
    "validate_table_simple_v1",
    "validate_table_simple_optional_fields",
    "validate_table_pandoc_v1",
    "validate_figure_meta_v1",
    # Pandoc walker
    "walk_pandoc",
    "WalkContext",
    "NodeContext",
    "collect_all_types",
    "find_nodes_by_type",
    # Document validator
    "validate_resolved_document",
    "validate_wrapper_content_type",
    "DocumentValidationResult",
]
