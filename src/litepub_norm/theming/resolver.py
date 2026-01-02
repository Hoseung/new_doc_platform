"""
Theme resolver.

Finds themes on disk and validates theme packs.
Returns ThemeBundle objects with resolved paths and hashes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .manifest import ThemeManifest, load_manifest, create_default_manifest
from .contract import validate_template_file, ValidationResult


# Built-in themes directory (relative to this file)
BUILTIN_THEMES_DIR = Path(__file__).parent.parent / "render" / "themes"


class ThemeNotFoundError(Exception):
    """Theme could not be found."""
    pass


class ThemeValidationError(Exception):
    """Theme pack validation failed."""
    pass


@dataclass(frozen=True)
class ThemeBundle:
    """
    Resolved theme bundle ready for rendering.

    Contains all paths and metadata needed by the renderer.
    """
    theme_id: str
    theme_dir: Path
    template_path: Path
    assets_dir: Path
    css_files: tuple[Path, ...]
    js_files: tuple[Path, ...]
    manifest: ThemeManifest
    template_hash: str
    assets_hash: str

    def get_relative_css(self) -> tuple[str, ...]:
        """Get CSS paths relative to assets dir for HTML output."""
        return tuple(f"assets/{p.name}" for p in self.css_files if p.exists())

    def get_relative_js(self) -> tuple[str, ...]:
        """Get JS paths relative to assets dir for HTML output."""
        return tuple(f"assets/{p.name}" for p in self.js_files if p.exists())


def _compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()[:16]}"


def _compute_dir_hash(directory: Path) -> str:
    """Compute hash of all files in a directory (sorted, deterministic)."""
    if not directory.exists():
        return ""

    h = hashlib.sha256()
    files = sorted(directory.rglob("*"))
    for f in files:
        if f.is_file():
            rel_path = f.relative_to(directory)
            h.update(str(rel_path).encode())
            h.update(_compute_file_hash(f).encode())
    return f"sha256:{h.hexdigest()[:16]}"


def _find_theme_dir(
    theme_id: str,
    project_themes_dir: Path | None = None,
) -> Path:
    """
    Find theme directory by ID.

    Resolution order:
    1. project-local ./themes/<id>
    2. built-in repo/themes/<id>

    Args:
        theme_id: Theme identifier
        project_themes_dir: Optional project-local themes directory

    Returns:
        Path to theme directory

    Raises:
        ThemeNotFoundError: If theme not found
    """
    # Check project-local themes first
    if project_themes_dir:
        local_path = project_themes_dir / theme_id
        if local_path.is_dir():
            return local_path

    # Check built-in themes
    builtin_path = BUILTIN_THEMES_DIR / theme_id
    if builtin_path.is_dir():
        return builtin_path

    # Theme not found
    available = list_available_themes(project_themes_dir)
    raise ThemeNotFoundError(
        f"Theme '{theme_id}' not found. Available themes: {', '.join(available)}"
    )


def _validate_theme_pack(
    theme_dir: Path,
    manifest: ThemeManifest,
) -> None:
    """
    Validate a theme pack has required files.

    Raises:
        ThemeValidationError: If validation fails
    """
    errors = []

    # Check template exists
    template_path = theme_dir / manifest.entry.template
    if not template_path.exists():
        errors.append(f"Template not found: {manifest.entry.template}")

    # Check assets directory
    assets_dir = theme_dir / "assets"
    if not assets_dir.is_dir():
        errors.append("Assets directory not found")

    # Check CSS files
    for css in manifest.entry.css:
        css_path = theme_dir / css
        if not css_path.exists():
            errors.append(f"CSS file not found: {css}")

    # Validate template hooks (lenient mode - only check mandatory)
    if template_path.exists():
        result = validate_template_file(template_path, mode="lenient")
        if not result.valid:
            for missing in result.missing_mandatory:
                errors.append(f"Template missing required hook: {missing}")

    if errors:
        raise ThemeValidationError(
            f"Theme '{manifest.id}' validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )


def resolve_theme(
    theme_id: str,
    project_themes_dir: Path | None = None,
    validate: bool = True,
) -> ThemeBundle:
    """
    Resolve a theme by ID and return a ThemeBundle.

    Args:
        theme_id: Theme identifier (e.g., "sidebar_docs", "base")
        project_themes_dir: Optional project-local themes directory
        validate: Whether to validate the theme pack

    Returns:
        ThemeBundle with resolved paths and hashes

    Raises:
        ThemeNotFoundError: If theme not found
        ThemeValidationError: If theme validation fails
    """
    # Find theme directory
    theme_dir = _find_theme_dir(theme_id, project_themes_dir)

    # Load or create manifest
    manifest = load_manifest(theme_dir)
    if manifest is None:
        manifest = create_default_manifest(theme_id)

    # Validate if requested
    if validate:
        _validate_theme_pack(theme_dir, manifest)

    # Resolve paths
    template_path = theme_dir / manifest.entry.template
    assets_dir = theme_dir / "assets"
    css_files = tuple(theme_dir / css for css in manifest.entry.css)
    js_files = tuple(theme_dir / js for js in manifest.entry.js)

    # Compute hashes for reproducibility
    template_hash = _compute_file_hash(template_path)
    assets_hash = _compute_dir_hash(assets_dir)

    return ThemeBundle(
        theme_id=theme_id,
        theme_dir=theme_dir,
        template_path=template_path,
        assets_dir=assets_dir,
        css_files=css_files,
        js_files=js_files,
        manifest=manifest,
        template_hash=template_hash,
        assets_hash=assets_hash,
    )


def list_available_themes(
    project_themes_dir: Path | None = None,
) -> list[str]:
    """
    List all available theme IDs.

    Args:
        project_themes_dir: Optional project-local themes directory

    Returns:
        List of theme IDs (directory names)
    """
    themes = set()

    # Built-in themes
    if BUILTIN_THEMES_DIR.is_dir():
        for d in BUILTIN_THEMES_DIR.iterdir():
            if d.is_dir() and (d / "template.html").exists():
                themes.add(d.name)

    # Project-local themes
    if project_themes_dir and project_themes_dir.is_dir():
        for d in project_themes_dir.iterdir():
            if d.is_dir() and (d / "template.html").exists():
                themes.add(d.name)

    return sorted(themes)
