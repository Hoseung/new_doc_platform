"""HTML renderer implementation."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..config import RenderConfig, default_html_config
from ..result import RenderResult
from ..report import RenderReport
from ..pandoc_runner import run as pandoc_run, PandocError
from ...filters.context import BuildContext


def render_html(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str = "document.html",
) -> RenderResult:
    """
    Render a filtered AST to HTML.

    Args:
        ast: Filtered Pandoc AST
        context: Build context (build_target, render_target, strict)
        config: Render configuration (uses defaults if None)
        output_name: Name of output HTML file

    Returns:
        RenderResult with success status and output paths
    """
    # Use default config if not provided
    if config is None:
        config = default_html_config()

    result = RenderResult(success=True)
    report = RenderReport()

    # Start report
    report.start()
    report.build_target = context.build_target
    report.render_target = "html"
    report.strict_mode = context.strict

    # Check pandoc version
    report.set_pandoc_version(config.pandoc_path)

    # Set template and assets info
    report.set_template(config.html_template_path)
    report.set_assets(config.html_assets_dir)
    report.set_lua_filters(config.html_lua_filters)

    # Prepare output paths
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    # Build extra args for strict mode
    extra_args = list(config.html_writer_options)
    if context.strict:
        # In strict mode, use safer HTML generation
        extra_args.extend(["--no-highlight"])  # Avoid JS-based highlighting

    try:
        # Run pandoc
        pandoc_run(
            input_ast=ast,
            to_format="html5",
            output_path=output_path,
            pandoc_path=config.pandoc_path,
            template=config.html_template_path,
            lua_filters=config.html_lua_filters,
            extra_args=tuple(extra_args),
            standalone=config.standalone,
        )

        result.add_output_file(output_path)
        report.add_output(output_path)

        # Copy assets if configured
        if config.copy_assets and config.html_assets_dir:
            assets_dest = output_dir / "assets"
            if config.html_assets_dir.exists():
                if assets_dest.exists():
                    shutil.rmtree(assets_dest)
                shutil.copytree(config.html_assets_dir, assets_dest)
                result.add_output_file(assets_dest)
                report.add_output(assets_dest)

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

    except Exception as e:
        result.add_error(
            code="RENDER_ERROR",
            message=str(e),
            stage="html_render",
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
