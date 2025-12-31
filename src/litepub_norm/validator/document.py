"""Post-resolution document AST validator.

Validates invariants that must hold after resolution:
- No placeholder tokens remain
- Wrapper discipline (unique IDs, correct structure)
- Global safety (no raw content if disallowed)
- Target-specific visibility policies
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .errors import ValidationError
from ..resolver.config import ResolutionConfig, BuildTarget
from .pandoc_walk import walk_pandoc, WalkContext, NodeContext

# Placeholder pattern
PLACEHOLDER_PATTERN = re.compile(r"\[\[COMPUTED:(METRIC|TABLE|FIGURE)\]\]")

# Types that indicate raw content
RAW_TYPES = {"RawInline", "RawBlock"}


@dataclass
class DocumentValidationResult:
    """Result of document validation."""

    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Collected info
    semantic_ids: set[str] = field(default_factory=set)
    wrapper_count: int = 0
    raw_content_found: bool = False


def validate_resolved_document(
    ast: dict[str, Any],
    config: ResolutionConfig | None = None,
    *,
    check_placeholders: bool = True,
    check_wrappers: bool = True,
    check_raw_content: bool = True,
    check_visibility: bool = True,
    fail_fast: bool = True,
) -> DocumentValidationResult:
    """
    Validate a resolved document AST.

    Args:
        ast: The resolved Pandoc AST.
        config: Resolution config for target-specific checks.
        check_placeholders: Verify no placeholder tokens remain.
        check_wrappers: Verify wrapper discipline (unique IDs, structure).
        check_raw_content: Verify no raw content if disallowed.
        check_visibility: Verify visibility policies for target.
        fail_fast: If True, raise on first error. If False, collect all errors.

    Returns:
        DocumentValidationResult with errors and warnings.

    Raises:
        ValidationError: If fail_fast=True and validation fails.
    """
    result = DocumentValidationResult()
    config = config or ResolutionConfig()

    blocks = ast.get("blocks", [])
    if not isinstance(blocks, list):
        error = ValidationError(
            "Document AST must have 'blocks' array",
            code="VAL_DOC_NO_BLOCKS",
        )
        if fail_fast:
            raise error
        result.errors.append(error)
        result.valid = False
        return result

    # Track seen semantic IDs for uniqueness check
    seen_ids: dict[str, str] = {}  # id -> first occurrence path

    for i, block in enumerate(blocks):
        block_path = f"blocks[{i}]"

        # Check if this is a wrapper Div
        if isinstance(block, dict) and block.get("t") == "Div":
            _validate_wrapper_div(
                block, block_path, config, result, seen_ids,
                check_placeholders, check_wrappers, check_raw_content,
                check_visibility, fail_fast,
            )
        else:
            # Non-wrapper block: check for stray placeholders
            if check_placeholders:
                _check_for_placeholders(block, block_path, result, fail_fast)

            # Check for raw content
            if check_raw_content and not config.allow_raw_pandoc:
                _check_for_raw_content(block, block_path, result, fail_fast)

    return result


def _validate_wrapper_div(
    div: dict[str, Any],
    path: str,
    config: ResolutionConfig,
    result: DocumentValidationResult,
    seen_ids: dict[str, str],
    check_placeholders: bool,
    check_wrappers: bool,
    check_raw_content: bool,
    check_visibility: bool,
    fail_fast: bool,
) -> None:
    """Validate a wrapper Div block."""
    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        return

    attr = content[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return

    semantic_id = attr[0] if len(attr) > 0 else ""
    classes = attr[1] if len(attr) > 1 else []
    key_vals = attr[2] if len(attr) > 2 else []

    # Skip if not a semantic wrapper
    if not semantic_id:
        return

    result.wrapper_count += 1
    result.semantic_ids.add(semantic_id)

    # Parse attributes
    attrs = {kv[0]: kv[1] for kv in key_vals if isinstance(kv, list) and len(kv) >= 2}
    role = attrs.get("role", "")
    kind = attrs.get("kind", "")
    visibility = attrs.get("visibility", "internal")

    # Check wrapper discipline
    if check_wrappers:
        # Unique ID check
        if semantic_id in seen_ids:
            error = ValidationError(
                f"Duplicate semantic ID: '{semantic_id}'",
                code="VAL_DOC_DUPLICATE_ID",
                semantic_id=semantic_id,
                ast_path=path,
                hint=f"First occurrence at {seen_ids[semantic_id]}",
            )
            if fail_fast:
                raise error
            result.errors.append(error)
            result.valid = False
        else:
            seen_ids[semantic_id] = path

        # Computed wrapper should have kind
        if role == "computed" and not kind:
            error = ValidationError(
                f"Computed wrapper missing 'kind' attribute",
                code="VAL_DOC_MISSING_KIND",
                semantic_id=semantic_id,
                ast_path=path,
            )
            if fail_fast:
                raise error
            result.errors.append(error)
            result.valid = False

    # Check visibility policy
    if check_visibility:
        _check_visibility_policy(
            semantic_id, visibility, config.target, path, result, fail_fast
        )

    # Check wrapper content
    wrapper_content = content[1] if len(content) > 1 else []
    if isinstance(wrapper_content, list):
        for j, inner_block in enumerate(wrapper_content):
            inner_path = f"{path}.c[1][{j}]"

            # Check for placeholders in content
            if check_placeholders:
                _check_for_placeholders(inner_block, inner_path, result, fail_fast)

            # Check for raw content
            if check_raw_content and not config.allow_raw_pandoc:
                _check_for_raw_content(inner_block, inner_path, result, fail_fast)


def _check_for_placeholders(
    node: Any,
    path: str,
    result: DocumentValidationResult,
    fail_fast: bool,
) -> None:
    """Check for leftover placeholder tokens in a node."""

    def check_node(n: Any, ctx: WalkContext) -> None:
        # Only check Str nodes
        if ctx.node_type != "Str":
            return

        text = n.get("c", "")
        if isinstance(text, str) and PLACEHOLDER_PATTERN.search(text):
            error = ValidationError(
                f"Unresolved placeholder found: {text}",
                code="VAL_DOC_UNRESOLVED_PLACEHOLDER",
                ast_path=ctx.path,
                hint="This placeholder should have been replaced during resolution",
            )
            if fail_fast:
                raise error
            result.errors.append(error)
            result.valid = False

    try:
        walk_pandoc(node, check_node, "", path=path)
    except ValidationError:
        raise


def _check_for_raw_content(
    node: Any,
    path: str,
    result: DocumentValidationResult,
    fail_fast: bool,
) -> None:
    """Check for raw content (RawInline/RawBlock) in a node."""

    def check_node(n: Any, ctx: WalkContext) -> None:
        if ctx.node_type in RAW_TYPES:
            result.raw_content_found = True
            error = ValidationError(
                f"Raw content ({ctx.node_type}) found in document",
                code=f"VAL_DOC_{ctx.node_type.upper()}_FORBIDDEN",
                ast_path=ctx.path,
                hint="Set allow_raw_pandoc=True in config to allow raw content",
            )
            if fail_fast:
                raise error
            result.errors.append(error)
            result.valid = False

    try:
        walk_pandoc(node, check_node, "", path=path)
    except ValidationError:
        raise


def _check_visibility_policy(
    semantic_id: str,
    visibility: str,
    target: BuildTarget,
    path: str,
    result: DocumentValidationResult,
    fail_fast: bool,
) -> None:
    """Check visibility monotonicity policy."""
    # Visibility ordering: internal < external < dossier
    # internal-only content must not appear in external/dossier builds

    visibility_levels = {"internal": 0, "external": 1, "dossier": 2}
    target_levels = {"internal": 0, "external": 1, "dossier": 2}

    vis_level = visibility_levels.get(visibility, 0)
    target_level = target_levels.get(target, 0)

    # If content visibility is lower than target, it shouldn't appear
    # e.g., internal-only content in external build
    if vis_level < target_level:
        error = ValidationError(
            f"Content with visibility '{visibility}' should not appear in '{target}' build",
            code="VAL_DOC_VISIBILITY_VIOLATION",
            semantic_id=semantic_id,
            ast_path=path,
            hint=f"Internal-only content should be filtered for {target} builds",
        )
        if fail_fast:
            raise error
        result.errors.append(error)
        result.valid = False


def validate_wrapper_content_type(
    div: dict[str, Any],
    expected_kind: str,
    semantic_id: str,
) -> None:
    """
    Validate that wrapper content matches expected kind.

    Args:
        div: The wrapper Div block.
        expected_kind: Expected kind (metric, table, figure).
        semantic_id: Semantic ID for error messages.

    Raises:
        ValidationError: If content doesn't match expected kind.
    """
    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        raise ValidationError(
            "Invalid wrapper structure",
            code="VAL_DOC_WRAPPER_STRUCTURE",
            semantic_id=semantic_id,
        )

    wrapper_content = content[1]
    if not isinstance(wrapper_content, list) or len(wrapper_content) == 0:
        raise ValidationError(
            "Empty wrapper content",
            code="VAL_DOC_WRAPPER_EMPTY",
            semantic_id=semantic_id,
        )

    # Find the primary content block
    primary_block = wrapper_content[0]
    if not isinstance(primary_block, dict):
        raise ValidationError(
            "Invalid primary block in wrapper",
            code="VAL_DOC_WRAPPER_INVALID_PRIMARY",
            semantic_id=semantic_id,
        )

    block_type = primary_block.get("t", "")

    # Check type matches kind
    expected_types = {
        "metric": {"Table"},  # Metrics are rendered as tables
        "table": {"Table"},
        "figure": {"Figure"},
    }

    allowed = expected_types.get(expected_kind.lower(), set())
    if block_type not in allowed:
        raise ValidationError(
            f"Wrapper kind '{expected_kind}' expected {allowed}, got '{block_type}'",
            code="VAL_DOC_WRAPPER_KIND_MISMATCH",
            semantic_id=semantic_id,
            hint=f"Primary block type should be one of: {allowed}",
        )
