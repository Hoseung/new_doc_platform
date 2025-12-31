"""Presentation filter - transforms AST for PDF/HTML output."""

from __future__ import annotations

from typing import Any
import copy
import hashlib

from .context import BuildContext
from .config import FilterConfig
from .report import FilterReport
from .utils.wrappers import (
    iter_wrappers,
    get_wrapper_id,
    is_additional,
)
from .utils.text_metrics import (
    count_codeblock_lines,
    count_codeblock_chars,
    estimate_block_chars,
    estimate_div_blocks,
)
from .utils.sectioning import (
    make_anchor_id,
    ensure_appendix_section,
    append_to_appendix,
    make_stub_para,
)


def filter_presentation(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    Apply presentation transformations for PDF or HTML output.

    PDF transformations:
    - T1: Externalize long code blocks into link stubs
    - T2: Move long additional sections to Appendix with stub

    HTML transformations:
    - T3: Fold long additional sections
    - T4: Fold long code blocks

    Args:
        ast: Pandoc AST
        config: Filter configuration
        context: Build context

    Returns:
        Tuple of (transformed AST, report)
    """
    report = FilterReport()
    result_ast = copy.deepcopy(ast)

    if context.render_target == "pdf":
        result_ast, code_report = _transform_pdf_code_blocks(result_ast, config, context)
        report = report.merge(code_report)

        result_ast, appendix_report = _transform_pdf_additional_to_appendix(result_ast, config, context)
        report = report.merge(appendix_report)

    elif context.render_target == "html":
        result_ast, fold_report = _transform_html_fold_additional(result_ast, config, context)
        report = report.merge(fold_report)

        result_ast, code_fold_report = _transform_html_fold_code_blocks(result_ast, config, context)
        report = report.merge(code_fold_report)

    return result_ast, report


def _transform_pdf_code_blocks(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    PDF T1: Externalize long code blocks.

    Replace long code blocks with stub + preview.
    """
    report = FilterReport()
    thresholds = config.thresholds

    def process_blocks(blocks: list[dict[str, Any]], path_prefix: str) -> list[dict[str, Any]]:
        result = []
        for i, block in enumerate(blocks):
            path = f"{path_prefix}[{i}]"

            if block.get("t") == "CodeBlock":
                lines = count_codeblock_lines(block)
                chars = count_codeblock_chars(block)

                if lines > thresholds.pdf_code_max_lines or chars > thresholds.pdf_code_max_chars:
                    # Generate stub blocks
                    stub_blocks = _make_code_stub(block, config, context, thresholds)
                    result.extend(stub_blocks)

                    # Generate a stable ID for reporting
                    content = block.get("c", [])
                    code_text = content[1] if len(content) >= 2 else ""
                    code_hash = hashlib.sha256(code_text.encode()).hexdigest()[:8]

                    report.add(
                        semantic_id=f"codeblock-{code_hash}",
                        action="externalized",
                        reason_code="PRES_PDF_CODEBLOCK_EXTERNALIZED",
                        message=f"Code block externalized ({lines} lines, {chars} chars)",
                        path=path,
                        details={"lines": lines, "chars": chars},
                    )
                else:
                    result.append(block)

            elif block.get("t") == "Div":
                # Process nested blocks in Divs
                content = block.get("c", [])
                if len(content) >= 2 and isinstance(content[1], list):
                    content[1] = process_blocks(content[1], f"{path}.c[1]")
                result.append(block)

            else:
                result.append(block)

        return result

    blocks = ast.get("blocks", [])
    ast["blocks"] = process_blocks(blocks, "blocks")

    return ast, report


def _make_code_stub(
    codeblock: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
    thresholds,
) -> list[dict[str, Any]]:
    """Create stub blocks for an externalized code block."""
    content = codeblock.get("c", [])
    code_text = content[1] if len(content) >= 2 else ""

    # Generate stable link target
    code_hash = hashlib.sha256(code_text.encode()).hexdigest()[:16]

    if context.artifact_base_url:
        link_target = f"{context.artifact_base_url}/code_snippets/{code_hash}.txt"
    else:
        link_target = f"code_snippets/{code_hash}.txt"

    stub_blocks = []

    # Stub paragraph
    stub_para = make_stub_para(
        "Code snippet omitted from PDF. See:",
        link_text=link_target,
        link_target=link_target,
    )
    stub_blocks.append(stub_para)

    # Preview (first N lines)
    if thresholds.pdf_code_preview_lines > 0:
        lines = code_text.split("\n")[:thresholds.pdf_code_preview_lines]
        preview_text = "\n".join(lines)
        if len(code_text.split("\n")) > thresholds.pdf_code_preview_lines:
            preview_text += "\n# ... (truncated)"

        # Preserve language info
        attr = content[0] if len(content) >= 1 else ["", [], []]
        preview_block = {"t": "CodeBlock", "c": [attr, preview_text]}
        stub_blocks.append(preview_block)

    return stub_blocks


def _transform_pdf_additional_to_appendix(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    PDF T2: Move long additional sections to Appendix.
    """
    report = FilterReport()
    thresholds = config.thresholds
    appendix_opts = config.appendix

    # Collect wrappers to move (in document order)
    wrappers_to_move: list[tuple[str, str, dict[str, Any]]] = []

    for div, path, idx in iter_wrappers(ast):
        wrapper_id = get_wrapper_id(div)
        if not wrapper_id:
            continue

        if not is_additional(div):
            continue

        block_count = estimate_div_blocks(div)
        char_count = estimate_block_chars(div)

        if (block_count > thresholds.appendix_threshold_blocks or
                char_count > thresholds.appendix_threshold_chars):
            wrappers_to_move.append((wrapper_id, path, div))

    if not wrappers_to_move:
        return ast, report

    # Ensure appendix exists
    ast, appendix_idx, appendix_anchor = ensure_appendix_section(
        ast,
        title=appendix_opts.title,
        anchor_prefix=appendix_opts.anchor_prefix,
    )

    # Process each wrapper
    blocks = ast.get("blocks", [])
    ids_to_remove: set[str] = set()

    for wrapper_id, path, div in wrappers_to_move:
        # Create anchor for this subsection
        anchor_id = make_anchor_id(wrapper_id, appendix_opts.anchor_prefix)

        # Extract content from wrapper
        content = div.get("c", [])
        inner_blocks = content[1] if len(content) >= 2 else []

        # Append to appendix
        append_to_appendix(
            ast,
            appendix_idx,
            subsection_title=f"Additional: {wrapper_id}",
            content_blocks=inner_blocks if isinstance(inner_blocks, list) else [],
            anchor_id=anchor_id,
        )

        # Mark for replacement with stub
        ids_to_remove.add(wrapper_id)

        report.add(
            semantic_id=wrapper_id,
            action="moved_to_appendix",
            reason_code="PRES_PDF_MOVED_TO_APPENDIX",
            message=f"Additional content '{wrapper_id}' moved to Appendix",
            path=path,
            details={"anchor_id": anchor_id},
        )

    # Replace original wrappers with stubs
    def replace_with_stub(block_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for block in block_list:
            from .utils.wrappers import get_wrapper_id as get_id
            bid = get_id(block)
            if bid and bid in ids_to_remove:
                anchor_id = make_anchor_id(bid, appendix_opts.anchor_prefix)
                stub = make_stub_para(
                    f"[Moved to {appendix_opts.title}]",
                    link_text=bid,
                    link_target=f"#{anchor_id}",
                )
                result.append(stub)
            elif block.get("t") == "Div":
                content = block.get("c", [])
                if len(content) >= 2 and isinstance(content[1], list):
                    content[1] = replace_with_stub(content[1])
                result.append(block)
            else:
                result.append(block)
        return result

    ast["blocks"] = replace_with_stub(blocks)

    return ast, report


def _transform_html_fold_additional(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    HTML T3: Fold long additional sections.
    """
    report = FilterReport()
    thresholds = config.thresholds

    for div, path, idx in iter_wrappers(ast):
        wrapper_id = get_wrapper_id(div)
        if not wrapper_id:
            continue

        if not is_additional(div):
            continue

        block_count = estimate_div_blocks(div)
        char_count = estimate_block_chars(div)

        if (block_count > thresholds.html_fold_threshold_blocks or
                char_count > thresholds.html_fold_threshold_chars):
            # Wrap content in foldable div
            _make_foldable(div, title=f"Additional: {wrapper_id}")

            report.add(
                semantic_id=wrapper_id,
                action="folded",
                reason_code="PRES_HTML_FOLDED",
                message=f"Additional content '{wrapper_id}' folded",
                path=path,
                details={"blocks": block_count, "chars": char_count},
            )

    return ast, report


def _transform_html_fold_code_blocks(
    ast: dict[str, Any],
    config: FilterConfig,
    context: BuildContext,
) -> tuple[dict[str, Any], FilterReport]:
    """
    HTML T4: Fold long code blocks.
    """
    report = FilterReport()
    thresholds = config.thresholds

    def process_blocks(blocks: list[dict[str, Any]], path_prefix: str) -> None:
        for i, block in enumerate(blocks):
            path = f"{path_prefix}[{i}]"

            if block.get("t") == "CodeBlock":
                lines = count_codeblock_lines(block)
                chars = count_codeblock_chars(block)

                if lines > thresholds.pdf_code_max_lines or chars > thresholds.pdf_code_max_chars:
                    # Wrap in foldable div (in-place transformation for next step)
                    content = block.get("c", [])
                    code_text = content[1] if len(content) >= 2 else ""
                    code_hash = hashlib.sha256(code_text.encode()).hexdigest()[:8]

                    report.add(
                        semantic_id=f"codeblock-{code_hash}",
                        action="folded",
                        reason_code="PRES_HTML_CODEBLOCK_FOLDED",
                        message=f"Code block folded ({lines} lines)",
                        path=path,
                        details={"lines": lines, "chars": chars},
                    )

            elif block.get("t") == "Div":
                content = block.get("c", [])
                if len(content) >= 2 and isinstance(content[1], list):
                    process_blocks(content[1], f"{path}.c[1]")

    blocks = ast.get("blocks", [])
    process_blocks(blocks, "blocks")

    return ast, report


def _make_foldable(div: dict[str, Any], title: str) -> None:
    """
    Mark a Div as foldable for HTML rendering.

    Adds class "foldable" and data-* attributes.
    Modifies the div in place.
    """
    content = div.get("c", [])
    if not isinstance(content, list) or len(content) < 1:
        return

    attr = content[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return

    # Add foldable class
    classes = attr[1]
    if "foldable" not in classes:
        classes.append("foldable")

    # Add data attributes
    key_vals = attr[2]
    key_vals.append(["data-title", title])
    key_vals.append(["data-collapsed", "true"])
