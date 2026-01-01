"""PDF renderer implementation using LaTeX."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from ..config import RenderConfig, default_pdf_config
from ..result import RenderResult
from ..report import RenderReport
from ..pandoc_runner import run_to_string, PandocError
from ..latex_runner import build as latex_build, LatexError, is_engine_available
from ...filters.context import BuildContext


def render_pdf(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str = "document.pdf",
) -> RenderResult:
    """
    Render a filtered AST to PDF via LaTeX.

    Args:
        ast: Filtered Pandoc AST
        context: Build context (build_target, render_target, strict)
        config: Render configuration (uses defaults if None)
        output_name: Name of output PDF file

    Returns:
        RenderResult with success status and output paths
    """
    # Use default config if not provided
    if config is None:
        config = default_pdf_config()

    result = RenderResult(success=True)
    report = RenderReport()

    # Start report
    report.start()
    report.build_target = context.build_target
    report.render_target = "pdf"
    report.strict_mode = context.strict

    # Check pandoc and latex versions
    report.set_pandoc_version(config.pandoc_path)
    report.set_latex_version(config.latex_engine, config.latex_engine_path)
    report.set_template(config.latex_template_path)

    # Prepare output paths
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    # Check if LaTeX engine is available
    engine = config.latex_engine
    if not is_engine_available(engine):
        result.add_error(
            code="LATEX_NOT_FOUND",
            message=f"LaTeX engine '{engine}' not found in PATH",
            stage="latex",
        )
        report.add_error({
            "code": "LATEX_NOT_FOUND",
            "message": f"LaTeX engine '{engine}' not found",
        })
        report.complete()
        result.report = report.to_dict()
        return result

    # Build extra args for strict mode
    extra_args = list(config.latex_writer_options)
    if context.strict:
        # Disable raw LaTeX in strict mode
        extra_args.extend(["--no-highlight"])

    try:
        # Step 1: Generate LaTeX from AST
        latex_content = run_to_string(
            input_ast=ast,
            to_format="latex",
            pandoc_path=config.pandoc_path,
            template=config.latex_template_path,
            extra_args=tuple(extra_args),
            standalone=config.standalone,
        )

        # Step 2: Write LaTeX to temp file
        tex_path = output_dir / f"{output_path.stem}.tex"
        tex_path.write_text(latex_content, encoding="utf-8")
        result.add_output_file(tex_path)
        report.add_output(tex_path)

        # Step 3: Compile LaTeX to PDF
        latex_result = latex_build(
            latex_path=tex_path,
            output_dir=output_dir,
            engine=config.latex_engine,
            engine_path=config.latex_engine_path,
            runs=config.latex_runs,
        )

        if latex_result.success and latex_result.pdf_path:
            # Move PDF to desired output name if different
            if latex_result.pdf_path != output_path:
                latex_result.pdf_path.rename(output_path)

            # Insert PDF at the beginning so it's the primary output
            result.output_files.insert(0, output_path)
            report.add_output(output_path)

            # Add log file to outputs for debugging
            if latex_result.log_path:
                result.add_output_file(latex_result.log_path)

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
            "stderr": e.stderr,
        })

    except LatexError as e:
        result.add_error(
            code="LATEX_FAILED",
            message=str(e),
            stage="latex",
            details={"returncode": e.returncode},
        )
        report.add_error({
            "code": "LATEX_FAILED",
            "message": str(e),
            "log_file": str(e.log_file) if e.log_file else None,
        })

        # Try to include log content in error
        if e.log_file and e.log_file.exists():
            try:
                log_content = e.log_file.read_text(encoding="utf-8", errors="replace")
                # Find error lines
                error_lines = [
                    line for line in log_content.split("\n")
                    if "!" in line or "Error" in line
                ][:10]
                if error_lines:
                    result.errors[-1].details = result.errors[-1].details or {}
                    result.errors[-1].details["error_lines"] = error_lines
            except Exception:
                pass

    except Exception as e:
        result.add_error(
            code="RENDER_ERROR",
            message=str(e),
            stage="pdf_render",
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
