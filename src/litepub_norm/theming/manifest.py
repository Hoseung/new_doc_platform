"""
Theme manifest parsing.

Handles optional theme.json manifest files that describe
theme metadata and entry points.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ThemeEntry:
    """Entry points for a theme."""
    template: str = "template.html"
    css: tuple[str, ...] = ("assets/theme.css",)
    js: tuple[str, ...] = ("assets/theme.js",)


@dataclass(frozen=True)
class ThemeManifest:
    """
    Theme manifest data.

    Attributes:
        id: Stable theme identifier (used in config/CLI)
        name: Human-readable theme name
        version: Theme version string
        description: Theme description
        base: ID of parent theme (for inheritance, optional)
        entry: Entry points (template, CSS, JS files)
        supports_single: Whether theme works in single-page mode
        supports_site: Whether theme works in site mode
    """
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    base: str | None = None
    entry: ThemeEntry = field(default_factory=ThemeEntry)
    supports_single: bool = True
    supports_site: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any], theme_id: str | None = None) -> "ThemeManifest":
        """
        Create manifest from dictionary.

        Args:
            data: Manifest data dictionary
            theme_id: Fallback theme ID if not in data
        """
        entry_data = data.get("entry", {})
        entry = ThemeEntry(
            template=entry_data.get("template", "template.html"),
            css=tuple(entry_data.get("css", ["assets/theme.css"])),
            js=tuple(entry_data.get("js", ["assets/theme.js"])),
        )

        supports = data.get("supports", {})

        return cls(
            id=data.get("id", theme_id or "unknown"),
            name=data.get("name", data.get("id", theme_id or "Unknown Theme")),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            base=data.get("base"),
            entry=entry,
            supports_single=supports.get("single", True),
            supports_site=supports.get("site", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "base": self.base,
            "entry": {
                "template": self.entry.template,
                "css": list(self.entry.css),
                "js": list(self.entry.js),
            },
            "supports": {
                "single": self.supports_single,
                "site": self.supports_site,
            },
        }


def load_manifest(theme_dir: Path) -> ThemeManifest | None:
    """
    Load theme manifest from directory.

    Args:
        theme_dir: Theme directory path

    Returns:
        ThemeManifest if theme.json exists, None otherwise
    """
    manifest_path = theme_dir / "theme.json"

    if not manifest_path.exists():
        return None

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return ThemeManifest.from_dict(data, theme_id=theme_dir.name)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(f"Invalid theme.json in {theme_dir}: {e}") from e


def create_default_manifest(theme_id: str) -> ThemeManifest:
    """
    Create a default manifest for themes without theme.json.

    Args:
        theme_id: Theme directory name as ID
    """
    return ThemeManifest(
        id=theme_id,
        name=theme_id.replace("_", " ").title(),
        entry=ThemeEntry(),
    )
