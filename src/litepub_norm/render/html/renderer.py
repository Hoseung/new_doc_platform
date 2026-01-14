"""HTML renderer implementation."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from ..config import RenderConfig, default_html_config
from ..result import RenderResult
from ..report import RenderReport
from ..pandoc_runner import run as pandoc_run, PandocError
from ...filters.context import BuildContext


def _merge_first_chapter_into_index(site_dir: Path) -> dict[str, Any]:
    """
    Post-process chunkedhtml output to merge first chapter into index.html.

    Pandoc's chunkedhtml creates an empty index.html with only navigation.
    This function merges the first chapter's content into index.html and
    removes the redundant first chapter file.

    Args:
        site_dir: Path to the chunkedhtml output directory

    Returns:
        Dict with merge info: {merged: bool, first_chapter: str, removed: bool}
    """
    result = {"merged": False, "first_chapter": None, "removed": False}

    index_path = site_dir / "index.html"
    if not index_path.exists():
        return result

    # Find the first chapter file (numbered files like "1-*.html")
    chapter_files = sorted(
        [f for f in site_dir.glob("*.html") if re.match(r"^\d+-", f.name)],
        key=lambda f: int(re.match(r"^(\d+)-", f.name).group(1))
    )

    if not chapter_files:
        return result

    first_chapter_path = chapter_files[0]
    result["first_chapter"] = first_chapter_path.name

    # Read both files
    index_html = index_path.read_text(encoding="utf-8")
    chapter_html = first_chapter_path.read_text(encoding="utf-8")

    # Extract main content from first chapter
    # Look for content inside <main id="lp-content">...</main>
    main_pattern = re.compile(
        r'(<main[^>]*id="lp-content"[^>]*>)(.*?)(</main>)',
        re.DOTALL
    )

    chapter_match = main_pattern.search(chapter_html)
    if not chapter_match:
        return result

    chapter_content = chapter_match.group(2)

    # Extract title from first chapter for index page
    title_pattern = re.compile(r'<title>([^<]+)</title>')
    chapter_title_match = title_pattern.search(chapter_html)
    if chapter_title_match:
        chapter_title = chapter_title_match.group(1)
        index_html = title_pattern.sub(f'<title>{chapter_title}</title>', index_html)

    # Replace index.html main content with first chapter content
    def replace_main_content(match):
        return match.group(1) + chapter_content + match.group(3)

    new_index_html = main_pattern.sub(replace_main_content, index_html)

    # Update navigation links in index.html:
    # - Remove "previous" link pointing to index (it's now the first page)
    # - Update "next" link to point to second chapter (if exists)
    if len(chapter_files) > 1:
        second_chapter = chapter_files[1].name
        # Update next link to point to second chapter instead of first
        new_index_html = re.sub(
            rf'href="{re.escape(first_chapter_path.name)}"([^>]*class="page-nav-next")',
            f'href="{second_chapter}"\\1',
            new_index_html
        )
        # Also update the title in the next link
        # Extract title from second chapter
        second_chapter_html = chapter_files[1].read_text(encoding="utf-8")
        second_title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', second_chapter_html)
        if second_title_match:
            second_title = second_title_match.group(1).strip()
            new_index_html = re.sub(
                r'(<a[^>]*class="page-nav-next"[^>]*>.*?<span class="page-nav-title">)[^<]*(</span>)',
                rf'\g<1>{second_title}\2',
                new_index_html,
                flags=re.DOTALL
            )
    else:
        # No more chapters, remove the next navigation entirely
        new_index_html = re.sub(
            r'<a[^>]*class="page-nav-next"[^>]*>.*?</a>',
            '<span class="page-nav-next"></span>',
            new_index_html,
            flags=re.DOTALL
        )

    # Remove the "previous" link from index.html (it's now the first page)
    # Replace the prev link with an empty span
    new_index_html = re.sub(
        r'<a[^>]*class="page-nav-prev"[^>]*>.*?</a>',
        '<span class="page-nav-prev"></span>',
        new_index_html,
        flags=re.DOTALL
    )

    # Write updated index.html
    index_path.write_text(new_index_html, encoding="utf-8")
    result["merged"] = True

    # Update links in all other chapter files:
    # - Links pointing to first chapter should now point to index.html
    for chapter_file in chapter_files[1:]:
        content = chapter_file.read_text(encoding="utf-8")
        # Replace links to first chapter with links to index.html
        updated_content = content.replace(
            f'href="{first_chapter_path.name}"',
            'href="index.html"'
        )
        # Update prev link that points to first chapter
        updated_content = re.sub(
            rf'<a href="index\.html"([^>]*class="page-nav-prev"[^>]*>.*?<span class="page-nav-title">)[^<]*(</span>)',
            rf'<a href="index.html"\1{chapter_title}\2',
            updated_content,
            flags=re.DOTALL
        )
        if updated_content != content:
            chapter_file.write_text(updated_content, encoding="utf-8")

    # Also update TOC links in all files (including index.html)
    all_html_files = list(site_dir.glob("*.html"))
    for html_file in all_html_files:
        content = html_file.read_text(encoding="utf-8")
        # Replace TOC links that reference the first chapter file
        updated_content = content.replace(
            f'href="{first_chapter_path.name}#',
            'href="index.html#'
        )
        updated_content = updated_content.replace(
            f'href="{first_chapter_path.name}"',
            'href="index.html"'
        )
        if updated_content != content:
            html_file.write_text(updated_content, encoding="utf-8")

    # Remove the first chapter file (now redundant)
    first_chapter_path.unlink()
    result["removed"] = True

    return result


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

    # Add theme info to report
    report.extra_info = {
        "html_mode": "single",
        "html_theme": config.html_theme,
    }

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

    # Build extra args
    extra_args = list(config.html_writer_options)
    extra_args.append("--toc")  # Include table of contents
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

    # Add site mode and theme info to report
    report.extra_info = {
        "html_mode": "site",
        "html_theme": config.html_theme,
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
        "--toc",  # Generate table of contents
        "-V", "toc",  # Include TOC on all pages (not just index)
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

        # Post-process: merge first chapter into index.html
        # This ensures index.html has content instead of being empty
        if site_output_dir.exists():
            merge_result = _merge_first_chapter_into_index(site_output_dir)
            if merge_result["merged"]:
                report.extra_info["index_merge"] = merge_result
                # Update pages list (first chapter file was removed)
                html_pages = sorted(site_output_dir.glob("*.html"))
                report.extra_info["pages"] = [p.name for p in html_pages]

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
