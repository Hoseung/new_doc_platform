"""PDF renderer implementation using LaTeX with theme support."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..config import RenderConfig, default_pdf_config
from ..result import RenderResult
from ..report import RenderReport
from ..pandoc_runner import run_to_string, PandocError
from ..latex_runner import build as latex_build, LatexError, is_engine_available
from ...filters.context import BuildContext

# Path to built-in PDF Lua filters
_FILTERS_DIR = Path(__file__).parent.parent / "pdf_themes" / "filters"


def render_pdf(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str = "document.pdf",
) -> RenderResult:
    """
    Render a filtered AST to PDF via LaTeX.

    Supports PDF theming with modular theme packs containing:
    - template.tex: Document structure
    - assets/theme.sty: Styling (colors, fonts, boxes)
    - assets/fonts/: Bundled fonts for determinism

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

    # Add theme info to report
    if config.pdf_theme:
        report.extra_info = report.extra_info or {}
        report.extra_info["pdf_theme"] = config.pdf_theme
        if config.pdf_theme_dir:
            report.extra_info["pdf_theme_dir"] = str(config.pdf_theme_dir)

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

    # Stage assets if using a theme
    staged_assets_dir = None
    if config.latex_assets_dir and config.latex_assets_dir.exists():
        staged_assets_dir = _stage_assets(config.latex_assets_dir, output_dir)
        if staged_assets_dir:
            report.extra_info = report.extra_info or {}
            report.extra_info["staged_assets"] = str(staged_assets_dir)

    # Build extra args for Pandoc
    extra_args = list(config.latex_writer_options)

    # Include table of contents
    extra_args.append("--toc")

    # Use listings package for code blocks (generates \lstlisting environments)
    # This enables theme.sty styling via \lstset configuration
    if context.strict:
        # Disable highlighting in strict mode
        extra_args.append("--no-highlight")
    else:
        extra_args.append("--listings")

    # Collect Lua filters for Pandoc
    lua_filters: list[Path] = []

    # Add callouts filter (maps Div classes to LaTeX environments)
    callouts_filter = _FILTERS_DIR / "pdf_callouts.lua"
    if callouts_filter.exists():
        lua_filters.append(callouts_filter)

    try:
        # Step 1: Generate LaTeX from AST
        latex_content = run_to_string(
            input_ast=ast,
            to_format="latex",
            pandoc_path=config.pandoc_path,
            template=config.latex_template_path,
            lua_filters=lua_filters,
            extra_args=tuple(extra_args),
            standalone=config.standalone,
        )

        # Step 2: Write LaTeX to output directory
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


def _stage_assets(assets_dir: Path, output_dir: Path) -> Path | None:
    """
    Stage theme assets to output directory for LaTeX compilation.

    Copies theme.sty and fonts/ to output directory so LaTeX can find them.
    This ensures deterministic builds with bundled fonts.

    Args:
        assets_dir: Source assets directory from theme pack
        output_dir: Build output directory

    Returns:
        Path to staged assets directory, or None if nothing staged
    """
    staged_dir = output_dir / "assets"

    # Copy theme.sty if present
    style_src = assets_dir / "theme.sty"
    if style_src.exists():
        staged_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(style_src, staged_dir / "theme.sty")

    # Copy fonts directory if present
    fonts_src = assets_dir / "fonts"
    if fonts_src.is_dir():
        fonts_dst = staged_dir / "fonts"
        if fonts_dst.exists():
            shutil.rmtree(fonts_dst)
        shutil.copytree(fonts_src, fonts_dst)

    # Copy images directory if present (for logos, watermarks)
    images_src = assets_dir / "images"
    if images_src.is_dir():
        images_dst = staged_dir / "images"
        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)

    return staged_dir if staged_dir.exists() else None
