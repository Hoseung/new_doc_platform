"""Render configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

RenderTarget = Literal["html", "pdf", "md", "rst"]


@dataclass(frozen=True)
class RenderConfig:
    """
    Configuration for the rendering stage.

    Attributes:
        output_dir: Directory for output files
        pandoc_path: Path to pandoc executable (None = use system pandoc)
        pandoc_required_version: Required pandoc version (None = any)
        html_template_path: Path to HTML template
        html_assets_dir: Path to HTML assets (CSS, JS)
        html_lua_filters: List of Lua filter paths for HTML
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
    html_template_path: Path | None = None
    html_assets_dir: Path | None = None
    html_lua_filters: tuple[Path, ...] = ()

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
            html_template_path=self.html_template_path,
            html_assets_dir=self.html_assets_dir,
            html_lua_filters=self.html_lua_filters,
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


def default_html_config() -> RenderConfig:
    """Create a default config for HTML rendering."""
    render_dir = Path(__file__).parent
    return RenderConfig(
        html_template_path=render_dir / "html" / "templates" / "template.html",
        html_assets_dir=render_dir / "html" / "assets",
        html_lua_filters=(render_dir / "html" / "lua" / "foldable.lua",),
    )


def default_pdf_config() -> RenderConfig:
    """Create a default config for PDF rendering."""
    render_dir = Path(__file__).parent
    return RenderConfig(
        latex_template_path=render_dir / "pdf" / "templates" / "template.tex",
    )
