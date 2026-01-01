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

    Supports two modes:
    - single: Single-page HTML document (default)
    - site: Multi-page static site using Pandoc chunkedhtml

    Args:
        ast: Filtered Pandoc AST
        context: Build context (build_target, render_target, strict)
        config: Render configuration (uses defaults if None)
        output_name: Name of output HTML file (for single mode) or
                     directory name (for site mode, e.g., "site")

    Returns:
        RenderResult with success status and output paths
    """
    # Use default config if not provided
    if config is None:
        config = default_html_config()

    # Dispatch to appropriate renderer based on mode
    if config.html_mode == "site":
        return _render_html_site(ast, context, config, output_name)
    else:
        return _render_html_single(ast, context, config, output_name)


def _render_html_single(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig,
    output_name: str,
) -> RenderResult:
    """Render to single-page HTML document."""
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


def _render_html_site(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig,
    output_name: str,
) -> RenderResult:
    """
    Render to multi-page static site using Pandoc chunkedhtml.

    Uses Pandoc's chunkedhtml writer which produces:
    - index.html (top page)
    - Multiple section pages (*.html)
    - sitemap.json (navigation structure)
    """
    result = RenderResult(success=True)
    report = RenderReport()

    # Start report
    report.start()
    report.build_target = context.build_target
    report.render_target = "html"
    report.strict_mode = context.strict

    # Add site mode info to report
    report.extra_info = {
        "html_mode": "site",
        "split_level": config.html_site_split_level,
        "chunk_template": config.html_site_chunk_template,
    }

    # Check pandoc version
    report.set_pandoc_version(config.pandoc_path)

    # Set template and assets info
    report.set_template(config.html_template_path)
    report.set_assets(config.html_assets_dir)
    report.set_lua_filters(config.html_lua_filters)

    # Prepare output paths
    # For chunkedhtml, output_name is the directory name (without extension)
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove .html extension if present for site mode
    site_name = output_name.replace(".html", "") if output_name.endswith(".html") else output_name
    site_output_dir = output_dir / site_name

    # Build extra args for chunkedhtml
    extra_args = list(config.html_writer_options)
    extra_args.extend([
        f"--split-level={config.html_site_split_level}",
        f"--chunk-template={config.html_site_chunk_template}",
        "--toc",  # Include table of contents
    ])

    if context.strict:
        extra_args.extend(["--no-highlight"])

    try:
        # Run pandoc with chunkedhtml writer
        pandoc_run(
            input_ast=ast,
            to_format="chunkedhtml",
            output_path=site_output_dir,
            pandoc_path=config.pandoc_path,
            template=config.html_template_path,
            lua_filters=config.html_lua_filters,
            extra_args=tuple(extra_args),
            standalone=config.standalone,
        )

        # Add the site directory as output
        result.add_output_file(site_output_dir)
        report.add_output(site_output_dir)

        # List generated pages for the report
        if site_output_dir.exists():
            html_pages = sorted(site_output_dir.glob("*.html"))
            report.extra_info["pages"] = [p.name for p in html_pages]
            for page in html_pages:
                result.add_output_file(page)

            # Check for sitemap.json
            sitemap_path = site_output_dir / "sitemap.json"
            if sitemap_path.exists():
                result.add_output_file(sitemap_path)
                report.add_output(sitemap_path)

        # Copy assets if configured
        if config.copy_assets and config.html_assets_dir:
            assets_dest = site_output_dir / "assets"
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

    # Save report in the site directory
    report_path = site_output_dir / "render_report.json" if site_output_dir.exists() else output_dir / "render_report.json"
    report.save(report_path)
    result.add_output_file(report_path)

    return result
