"""
PDF theme manifest parsing.

Handles theme.yaml manifest files that describe PDF theme metadata,
font configuration, and geometry settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json


@dataclass(frozen=True)
class PdfFontConfig:
    """Font configuration for PDF theme."""
    # Main font family (for body text)
    mainfont: str = "DejaVu Serif"
    mainfont_options: str = ""

    # Sans font family (for headings, etc.)
    sansfont: str = "DejaVu Sans"
    sansfont_options: str = ""

    # Monospace font (for code)
    monofont: str = "DejaVu Sans Mono"
    monofont_options: str = "Scale=0.9"

    # CJK font (for Korean/Chinese/Japanese)
    cjkmainfont: str = "Noto Sans CJK KR"
    cjkmainfont_options: str = ""


@dataclass(frozen=True)
class PdfGeometryConfig:
    """Page geometry configuration."""
    paper: str = "a4paper"
    margin: str = "2.5cm"
    top: str = "3cm"
    bottom: str = "3cm"


@dataclass(frozen=True)
class PdfThemeManifest:
    """
    PDF theme manifest data.

    Attributes:
        id: Stable theme identifier
        name: Human-readable theme name
        version: Theme version string
        description: Theme description
        archetype: Theme archetype (std-report, corp-report, academic-paper)
        fonts: Font configuration
        geometry: Page geometry
        secnumdepth: Section numbering depth (1-4)
        toc: Whether to include table of contents
        provenance_footer: Whether to include provenance footer
    """
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    archetype: str = "std-report"
    fonts: PdfFontConfig = field(default_factory=PdfFontConfig)
    geometry: PdfGeometryConfig = field(default_factory=PdfGeometryConfig)
    secnumdepth: int = 3
    toc: bool = True
    provenance_footer: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any], theme_id: str | None = None) -> "PdfThemeManifest":
        """Create manifest from dictionary."""
        font_data = data.get("fonts", {})
        fonts = PdfFontConfig(
            mainfont=font_data.get("mainfont", "DejaVu Serif"),
            mainfont_options=font_data.get("mainfont_options", ""),
            sansfont=font_data.get("sansfont", "DejaVu Sans"),
            sansfont_options=font_data.get("sansfont_options", ""),
            monofont=font_data.get("monofont", "DejaVu Sans Mono"),
            monofont_options=font_data.get("monofont_options", "Scale=0.9"),
            cjkmainfont=font_data.get("cjkmainfont", "Noto Sans CJK KR"),
            cjkmainfont_options=font_data.get("cjkmainfont_options", ""),
        )

        geo_data = data.get("geometry", {})
        geometry = PdfGeometryConfig(
            paper=geo_data.get("paper", "a4paper"),
            margin=geo_data.get("margin", "2.5cm"),
            top=geo_data.get("top", "3cm"),
            bottom=geo_data.get("bottom", "3cm"),
        )

        return cls(
            id=data.get("id", theme_id or "unknown"),
            name=data.get("name", data.get("id", theme_id or "Unknown Theme")),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            archetype=data.get("archetype", "std-report"),
            fonts=fonts,
            geometry=geometry,
            secnumdepth=data.get("secnumdepth", 3),
            toc=data.get("toc", True),
            provenance_footer=data.get("provenance_footer", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "archetype": self.archetype,
            "fonts": {
                "mainfont": self.fonts.mainfont,
                "mainfont_options": self.fonts.mainfont_options,
                "sansfont": self.fonts.sansfont,
                "sansfont_options": self.fonts.sansfont_options,
                "monofont": self.fonts.monofont,
                "monofont_options": self.fonts.monofont_options,
                "cjkmainfont": self.fonts.cjkmainfont,
                "cjkmainfont_options": self.fonts.cjkmainfont_options,
            },
            "geometry": {
                "paper": self.geometry.paper,
                "margin": self.geometry.margin,
                "top": self.geometry.top,
                "bottom": self.geometry.bottom,
            },
            "secnumdepth": self.secnumdepth,
            "toc": self.toc,
            "provenance_footer": self.provenance_footer,
        }

    def to_pandoc_metadata(self) -> dict[str, Any]:
        """
        Convert to Pandoc metadata format.

        This can be passed to Pandoc via --metadata-file.
        """
        metadata = {
            "documentclass": "article",
            "papersize": self.geometry.paper.replace("paper", ""),
            "geometry": [
                f"margin={self.geometry.margin}",
                f"top={self.geometry.top}",
                f"bottom={self.geometry.bottom}",
            ],
            "mainfont": self.fonts.mainfont,
            "sansfont": self.fonts.sansfont,
            "monofont": self.fonts.monofont,
            "CJKmainfont": self.fonts.cjkmainfont,
            "secnumdepth": self.secnumdepth,
            "toc": self.toc,
        }

        if self.fonts.mainfont_options:
            metadata["mainfont-options"] = self.fonts.mainfont_options
        if self.fonts.monofont_options:
            metadata["monofont-options"] = self.fonts.monofont_options
        if self.fonts.cjkmainfont_options:
            metadata["CJKoptions"] = self.fonts.cjkmainfont_options

        return metadata


def load_pdf_manifest(theme_dir: Path) -> PdfThemeManifest | None:
    """
    Load PDF theme manifest from directory.

    Looks for theme.yaml first, then theme.json.

    Args:
        theme_dir: Theme directory path

    Returns:
        PdfThemeManifest if manifest exists, None otherwise
    """
    # Try YAML first (preferred for PDF themes per spec)
    yaml_path = theme_dir / "theme.yaml"
    if yaml_path.exists():
        try:
            # Use simple YAML parsing (avoid dependency)
            data = _parse_simple_yaml(yaml_path.read_text(encoding="utf-8"))
            return PdfThemeManifest.from_dict(data, theme_id=theme_dir.name)
        except Exception as e:
            raise ValueError(f"Invalid theme.yaml in {theme_dir}: {e}") from e

    # Fall back to JSON
    json_path = theme_dir / "theme.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return PdfThemeManifest.from_dict(data, theme_id=theme_dir.name)
        except Exception as e:
            raise ValueError(f"Invalid theme.json in {theme_dir}: {e}") from e

    return None


def _parse_simple_yaml(content: str) -> dict[str, Any]:
    """
    Parse simple YAML without external dependencies.

    Supports only flat key-value pairs and one level of nesting.
    For complex configs, use JSON instead.
    """
    result: dict[str, Any] = {}
    current_section: str | None = None
    current_dict: dict[str, Any] = result

    for line in content.split("\n"):
        # Skip comments and empty lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check indentation
        indent = len(line) - len(line.lstrip())

        if ":" not in stripped:
            continue

        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()

        # Remove quotes from value
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        if indent == 0:
            # Top-level key
            if not value:
                # This is a section header
                result[key] = {}
                current_section = key
                current_dict = result[key]
            else:
                # Simple key-value
                result[key] = _parse_yaml_value(value)
                current_section = None
                current_dict = result
        else:
            # Nested under current section
            if current_section:
                current_dict[key] = _parse_yaml_value(value)

    return result


def _parse_yaml_value(value: str) -> Any:
    """Parse a simple YAML value."""
    if not value:
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def create_default_pdf_manifest(theme_id: str) -> PdfThemeManifest:
    """Create a default manifest for themes without a manifest file."""
    return PdfThemeManifest(
        id=theme_id,
        name=theme_id.replace("-", " ").replace("_", " ").title(),
    )
