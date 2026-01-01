"""Render configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from ..theming.resolver import ThemeBundle

RenderTarget = Literal["html", "pdf", "md", "rst"]
HtmlMode = Literal["single", "site"]

# Default theme ID
DEFAULT_THEME = "base"


@dataclass(frozen=True)
class RenderConfig:
    """
    Configuration for the rendering stage.

    Attributes:
        output_dir: Directory for output files
        pandoc_path: Path to pandoc executable (None = use system pandoc)
        pandoc_required_version: Required pandoc version (None = any)
        html_theme: Theme ID for HTML rendering (e.g., "base", "sidebar_docs")
        html_template_path: Path to HTML template (overrides theme if set)
        html_assets_dir: Path to HTML assets (overrides theme if set)
        html_lua_filters: List of Lua filter paths for HTML
        html_mode: HTML rendering mode ('single' or 'site')
        html_site_split_level: Split level for site mode (1=chapter, 2=section)
        html_site_chunk_template: Filename template for site chunks
        latex_template_path: Path to LaTeX template
        latex_engine: LaTeX engine to use
        latex_engine_path: Path to LaTeX engine (None = use system)
        latex_runs: Number of LaTeX compilation runs
        html_writer_options: Additional options for HTML writer
        latex_writer_options: Additional options for LaTeX writer
        md_writer_options: Additional options for Markdown writer
        rst_writer_options: Additional options for RST writer
        copy_assets: Whether to copy assets to output directory
        standalone: Whether to produce standalone documents
    """

    output_dir: Path = field(default_factory=Path.cwd)
    pandoc_path: Path | None = None
    pandoc_required_version: str | None = None

    # HTML options
    html_theme: str | None = None  # Theme ID (resolved at render time)
    html_template_path: Path | None = None
    html_assets_dir: Path | None = None
    html_lua_filters: tuple[Path, ...] = ()
    html_mode: HtmlMode = "single"
    html_site_split_level: int = 1  # Split at level-1 headings (chapters)
    html_site_chunk_template: str = "%s-%i.html"  # section-number-identifier.html

    # PDF/LaTeX options
    latex_template_path: Path | None = None
    latex_engine: str = "xelatex"
    latex_engine_path: Path | None = None
    latex_runs: int = 2

    # Writer options (passed to pandoc)
    html_writer_options: tuple[str, ...] = ()
    latex_writer_options: tuple[str, ...] = ()
    md_writer_options: tuple[str, ...] = ()
    rst_writer_options: tuple[str, ...] = ()

    # General options
    copy_assets: bool = True
    standalone: bool = True

    def __post_init__(self):
        # Convert string paths to Path objects if needed
        if isinstance(self.output_dir, str):
            object.__setattr__(self, "output_dir", Path(self.output_dir))

    def get_writer_options(self, target: RenderTarget) -> tuple[str, ...]:
        """Get writer options for a specific target."""
        options_map = {
            "html": self.html_writer_options,
            "pdf": self.latex_writer_options,
            "md": self.md_writer_options,
            "rst": self.rst_writer_options,
        }
        return options_map.get(target, ())

    def get_template_path(self, target: RenderTarget) -> Path | None:
        """Get template path for a specific target."""
        if target == "html":
            return self.html_template_path
        elif target == "pdf":
            return self.latex_template_path
        return None

    def with_output_dir(self, output_dir: Path | str) -> RenderConfig:
        """Return a new config with a different output directory."""
        return RenderConfig(
            output_dir=Path(output_dir),
            pandoc_path=self.pandoc_path,
            pandoc_required_version=self.pandoc_required_version,
            html_theme=self.html_theme,
            html_template_path=self.html_template_path,
            html_assets_dir=self.html_assets_dir,
            html_lua_filters=self.html_lua_filters,
            html_mode=self.html_mode,
            html_site_split_level=self.html_site_split_level,
            html_site_chunk_template=self.html_site_chunk_template,
            latex_template_path=self.latex_template_path,
            latex_engine=self.latex_engine,
            latex_engine_path=self.latex_engine_path,
            latex_runs=self.latex_runs,
            html_writer_options=self.html_writer_options,
            latex_writer_options=self.latex_writer_options,
            md_writer_options=self.md_writer_options,
            rst_writer_options=self.rst_writer_options,
            copy_assets=self.copy_assets,
            standalone=self.standalone,
        )

    def with_html_mode(self, mode: HtmlMode, split_level: int = 1) -> RenderConfig:
        """Return a new config with HTML mode settings."""
        return RenderConfig(
            output_dir=self.output_dir,
            pandoc_path=self.pandoc_path,
            pandoc_required_version=self.pandoc_required_version,
            html_theme=self.html_theme,
            html_template_path=self.html_template_path,
            html_assets_dir=self.html_assets_dir,
            html_lua_filters=self.html_lua_filters,
            html_mode=mode,
            html_site_split_level=split_level,
            html_site_chunk_template=self.html_site_chunk_template,
            latex_template_path=self.latex_template_path,
            latex_engine=self.latex_engine,
            latex_engine_path=self.latex_engine_path,
            latex_runs=self.latex_runs,
            html_writer_options=self.html_writer_options,
            latex_writer_options=self.latex_writer_options,
            md_writer_options=self.md_writer_options,
            rst_writer_options=self.rst_writer_options,
            copy_assets=self.copy_assets,
            standalone=self.standalone,
        )

    def with_theme(
        self,
        theme_id: str,
        project_themes_dir: Path | None = None,
    ) -> RenderConfig:
        """
        Return a new config with theme settings applied.

        This resolves the theme and sets template/assets paths.

        Args:
            theme_id: Theme identifier (e.g., "base", "sidebar_docs", "topbar_classic")
            project_themes_dir: Optional project-local themes directory

        Returns:
            New RenderConfig with theme template and assets configured
        """
        from ..theming.resolver import resolve_theme

        bundle = resolve_theme(theme_id, project_themes_dir)

        return RenderConfig(
            output_dir=self.output_dir,
            pandoc_path=self.pandoc_path,
            pandoc_required_version=self.pandoc_required_version,
            html_theme=theme_id,
            html_template_path=bundle.template_path,
            html_assets_dir=bundle.assets_dir,
            html_lua_filters=self.html_lua_filters,
            html_mode=self.html_mode,
            html_site_split_level=self.html_site_split_level,
            html_site_chunk_template=self.html_site_chunk_template,
            latex_template_path=self.latex_template_path,
            latex_engine=self.latex_engine,
            latex_engine_path=self.latex_engine_path,
            latex_runs=self.latex_runs,
            html_writer_options=self.html_writer_options,
            latex_writer_options=self.latex_writer_options,
            md_writer_options=self.md_writer_options,
            rst_writer_options=self.rst_writer_options,
            copy_assets=self.copy_assets,
            standalone=self.standalone,
        )


def default_html_config(theme_id: str = DEFAULT_THEME) -> RenderConfig:
    """
    Create a default config for single-page HTML rendering.

    Args:
        theme_id: Theme to use (default: "base")
                  Available: "base", "sidebar_docs", "topbar_classic", "book_tutorial"
    """
    themes_dir = Path(__file__).parent / "themes"
    theme_dir = themes_dir / theme_id

    # Use theme template and assets if available
    if theme_dir.exists():
        template_path = theme_dir / "template.html"
        assets_dir = theme_dir / "assets"
    else:
        # Fallback to legacy location
        render_dir = Path(__file__).parent
        template_path = render_dir / "html" / "templates" / "template.html"
        assets_dir = render_dir / "html" / "assets"

    return RenderConfig(
        html_theme=theme_id,
        html_template_path=template_path,
        html_assets_dir=assets_dir,
        html_mode="single",
    )


def default_html_site_config(
    split_level: int = 1,
    theme_id: str = DEFAULT_THEME,
) -> RenderConfig:
    """
    Create a default config for multi-page HTML site rendering.

    Args:
        split_level: Where to split pages (1=chapters, 2=sections)
        theme_id: Theme to use (default: "base")
                  Available: "base", "sidebar_docs", "topbar_classic", "book_tutorial"
    """
    themes_dir = Path(__file__).parent / "themes"
    theme_dir = themes_dir / theme_id

    # Use theme template and assets if available
    if theme_dir.exists():
        template_path = theme_dir / "template.html"
        assets_dir = theme_dir / "assets"
    else:
        # Fallback to legacy location
        render_dir = Path(__file__).parent
        template_path = render_dir / "html" / "templates" / "template.html"
        assets_dir = render_dir / "html" / "assets"

    return RenderConfig(
        html_theme=theme_id,
        html_template_path=template_path,
        html_assets_dir=assets_dir,
        html_mode="site",
        html_site_split_level=split_level,
    )


def default_pdf_config() -> RenderConfig:
    """Create a default config for PDF rendering."""
    render_dir = Path(__file__).parent
    return RenderConfig(
        latex_template_path=render_dir / "pdf" / "templates" / "template.tex",
    )


def themed_html_config(
    theme_id: str,
    mode: HtmlMode = "single",
    split_level: int = 1,
    project_themes_dir: Path | None = None,
) -> RenderConfig:
    """
    Create a config with a specific theme.

    Args:
        theme_id: Theme identifier (e.g., "sidebar_docs", "topbar_classic", "book_tutorial")
        mode: HTML mode ("single" or "site")
        split_level: Split level for site mode
        project_themes_dir: Optional project-local themes directory

    Returns:
        RenderConfig with theme applied
    """
    from ..theming.resolver import resolve_theme

    bundle = resolve_theme(theme_id, project_themes_dir)

    return RenderConfig(
        html_theme=theme_id,
        html_template_path=bundle.template_path,
        html_assets_dir=bundle.assets_dir,
        html_mode=mode,
        html_site_split_level=split_level,
    )
