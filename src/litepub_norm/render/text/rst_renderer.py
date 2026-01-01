"""reStructuredText export renderer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import RenderConfig
from ..result import RenderResult
from ..report import RenderReport
from ..pandoc_runner import run as pandoc_run, PandocError
from ...filters.context import BuildContext


def render_rst(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str = "document.rst",
) -> RenderResult:
    """
    Render a filtered AST to reStructuredText.

    This is a best-effort view-only export.
    RST has limited fidelity compared to the canonical AST.

    Args:
        ast: Filtered Pandoc AST
        context: Build context
        config: Render configuration
        output_name: Name of output RST file

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
    report.render_target = "rst"
    report.strict_mode = context.strict

    # Check pandoc version
    report.set_pandoc_version(config.pandoc_path)

    # Prepare output paths
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    # Build extra args
    extra_args = list(config.rst_writer_options)

    # Add warning about best-effort export
    result.add_warning(
        code="RST_BEST_EFFORT",
        message="RST export is best-effort; some formatting may be lost",
    )
    report.add_warning({
        "code": "RST_BEST_EFFORT",
        "message": "RST export is best-effort",
    })

    try:
        # Run pandoc
        pandoc_run(
            input_ast=ast,
            to_format="rst",
            output_path=output_path,
            pandoc_path=config.pandoc_path,
            extra_args=tuple(extra_args),
            standalone=False,
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
            stage="rst_render",
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
