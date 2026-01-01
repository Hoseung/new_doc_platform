"""
Theme selection integration.

Provides helpers to configure RenderConfig with themes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .resolver import resolve_theme, ThemeBundle

if TYPE_CHECKING:
    from ..render.config import RenderConfig


def with_theme(
    config: "RenderConfig",
    theme_id: str,
    project_themes_dir: Path | None = None,
) -> "RenderConfig":
    """
    Create a new RenderConfig with theme settings applied.

    This is the main integration point between theming and rendering.

    Args:
        config: Base render configuration
        theme_id: Theme identifier (e.g., "sidebar_docs", "base")
        project_themes_dir: Optional project-local themes directory

    Returns:
        New RenderConfig with theme template and assets configured

    Example:
        >>> from litepub_norm.render.config import default_html_config
        >>> from litepub_norm.theming import with_theme
        >>>
        >>> config = default_html_config()
        >>> themed_config = with_theme(config, "sidebar_docs")
    """
    bundle = resolve_theme(theme_id, project_themes_dir)
    return apply_theme_bundle(config, bundle)


def apply_theme_bundle(
    config: "RenderConfig",
    bundle: ThemeBundle,
) -> "RenderConfig":
    """
    Apply a resolved ThemeBundle to a RenderConfig.

    Args:
        config: Base render configuration
        bundle: Resolved theme bundle

    Returns:
        New RenderConfig with theme settings
    """
    # Import here to avoid circular import
    from ..render.config import RenderConfig

    return RenderConfig(
        output_dir=config.output_dir,
        pandoc_path=config.pandoc_path,
        pandoc_required_version=config.pandoc_required_version,
        html_template_path=bundle.template_path,
        html_assets_dir=bundle.assets_dir,
        html_lua_filters=config.html_lua_filters,
        html_mode=config.html_mode,
        html_site_split_level=config.html_site_split_level,
        html_site_chunk_template=config.html_site_chunk_template,
        latex_template_path=config.latex_template_path,
        latex_engine=config.latex_engine,
        latex_engine_path=config.latex_engine_path,
        latex_runs=config.latex_runs,
        html_writer_options=config.html_writer_options,
        latex_writer_options=config.latex_writer_options,
        md_writer_options=config.md_writer_options,
        rst_writer_options=config.rst_writer_options,
        copy_assets=config.copy_assets,
        standalone=config.standalone,
    )


def get_theme_info(
    theme_id: str,
    project_themes_dir: Path | None = None,
) -> dict:
    """
    Get theme information for reporting/debugging.

    Args:
        theme_id: Theme identifier
        project_themes_dir: Optional project-local themes directory

    Returns:
        Dictionary with theme metadata and hashes
    """
    bundle = resolve_theme(theme_id, project_themes_dir)
    return {
        "id": bundle.theme_id,
        "name": bundle.manifest.name,
        "version": bundle.manifest.version,
        "template_path": str(bundle.template_path),
        "assets_dir": str(bundle.assets_dir),
        "template_hash": bundle.template_hash,
        "assets_hash": bundle.assets_hash,
        "supports_single": bundle.manifest.supports_single,
        "supports_site": bundle.manifest.supports_site,
    }
