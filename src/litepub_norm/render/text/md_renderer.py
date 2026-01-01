"""Markdown export renderer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import RenderConfig
from ..result import RenderResult
from ..report import RenderReport
from ..pandoc_runner import run as pandoc_run, PandocError
from ...filters.context import BuildContext


def render_md(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str = "document.md",
    flavor: str = "gfm",
) -> RenderResult:
    """
    Render a filtered AST to Markdown.

    This is a view-only export, not a canonical source.
    Semantic wrapper IDs are preserved where possible.

    Args:
        ast: Filtered Pandoc AST
        context: Build context
        config: Render configuration
        output_name: Name of output Markdown file
        flavor: Markdown flavor (gfm, commonmark, markdown)

    Returns:
        RenderResult with success status and output paths
    """
    if config is None:
        config = RenderConfig()

    result = RenderResult(success=True)
    report = RenderReport()

    # Start report
    report.start()
    report.build_target = context.build_target
    report.render_target = "md"
    report.strict_mode = context.strict

    # Check pandoc version
    report.set_pandoc_version(config.pandoc_path)

    # Prepare output paths
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    # Build extra args
    extra_args = list(config.md_writer_options)
    # Use fenced divs to preserve wrapper IDs
    extra_args.extend(["--wrap=none"])  # Prevent line wrapping issues

    try:
        # Run pandoc
        pandoc_run(
            input_ast=ast,
            to_format=flavor,
            output_path=output_path,
            pandoc_path=config.pandoc_path,
            extra_args=tuple(extra_args),
            standalone=False,  # Markdown doesn't need standalone
        )

        result.add_output_file(output_path)
        report.add_output(output_path)

    except PandocError as e:
        result.add_error(
            code="PANDOC_FAILED",
            message=str(e),
            stage="pandoc",
            details={"stderr": e.stderr, "returncode": e.returncode},
        )
        report.add_error({
            "code": "PANDOC_FAILED",
            "message": str(e),
        })

    except Exception as e:
        result.add_error(
            code="RENDER_ERROR",
            message=str(e),
            stage="md_render",
        )
        report.add_error({
            "code": "RENDER_ERROR",
            "message": str(e),
        })

    # Complete report
    report.complete()
    result.report = report.to_dict()

    # Save report
    report_path = output_dir / "render_report.json"
    report.save(report_path)
    result.add_output_file(report_path)

    return result
