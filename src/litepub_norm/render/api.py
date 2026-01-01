"""Top-level rendering API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from .config import RenderConfig, RenderTarget
from .result import RenderResult
from .html.renderer import render_html
from .pdf.renderer import render_pdf
from .text.md_renderer import render_md
from .text.rst_renderer import render_rst
from ..filters.context import BuildContext


def render(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str | None = None,
) -> RenderResult:
    """
    Render a filtered AST to the target format.

    This is the main entry point for the rendering stage.

    Args:
        ast: Filtered Pandoc AST (after normalization, resolution, filtering)
        context: Build context with build_target and render_target
        config: Render configuration (uses defaults if None)
        output_name: Output filename (auto-generated if None)

    Returns:
        RenderResult with success status, output files, and report

    Raises:
        ValueError: If render_target is unsupported
    """
    if config is None:
        config = RenderConfig()

    target = context.render_target

    # Auto-generate output name if not provided
    if output_name is None:
        extensions = {
            "html": ".html",
            "pdf": ".pdf",
            "md": ".md",
            "rst": ".rst",
        }
        ext = extensions.get(target, ".out")
        output_name = f"document{ext}"

    # Route to appropriate renderer
    if target == "html":
        return render_html(ast, context, config, output_name)
    elif target == "pdf":
        return render_pdf(ast, context, config, output_name)
    elif target == "md":
        return render_md(ast, context, config, output_name)
    elif target == "rst":
        return render_rst(ast, context, config, output_name)
    else:
        raise ValueError(f"Unsupported render target: {target}")


def render_all_targets(
    ast: dict[str, Any],
    build_target: Literal["internal", "external", "dossier"] = "internal",
    config: RenderConfig | None = None,
    targets: list[RenderTarget] | None = None,
) -> dict[RenderTarget, RenderResult]:
    """
    Render to multiple target formats.

    Args:
        ast: Filtered Pandoc AST
        build_target: Build target for context
        config: Render configuration
        targets: List of targets to render (defaults to all)

    Returns:
        Dictionary mapping target to RenderResult
    """
    if targets is None:
        targets = ["html", "pdf", "md", "rst"]

    if config is None:
        config = RenderConfig()

    results = {}
    for target in targets:
        context = BuildContext(
            build_target=build_target,
            render_target=target,
            strict=(build_target != "internal"),
        )
        results[target] = render(ast, context, config)

    return results
