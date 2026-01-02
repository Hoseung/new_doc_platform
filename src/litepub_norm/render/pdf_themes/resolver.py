"""
PDF theme resolver.

Finds PDF themes on disk and validates theme packs.
Returns PdfThemeBundle objects with resolved paths and hashes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .manifest import PdfThemeManifest, load_pdf_manifest, create_default_pdf_manifest


# Built-in PDF themes directory
BUILTIN_PDF_THEMES_DIR = Path(__file__).parent / "themes"


class PdfThemeNotFoundError(Exception):
    """PDF theme could not be found."""
    pass


class PdfThemeValidationError(Exception):
    """PDF theme pack validation failed."""
    pass


@dataclass(frozen=True)
class PdfThemeBundle:
    """
    Resolved PDF theme bundle ready for rendering.

    Contains all paths and metadata needed by the PDF renderer.
    """
    theme_id: str
    theme_dir: Path
    template_path: Path
    style_path: Path | None  # theme.sty
    assets_dir: Path
    fonts_dir: Path | None
    manifest: PdfThemeManifest
    template_hash: str
    style_hash: str
    assets_hash: str


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


def _find_pdf_theme_dir(
    theme_id: str,
    project_themes_dir: Path | None = None,
) -> Path:
    """
    Find PDF theme directory by ID.

    Resolution order:
    1. project-local ./pdf_themes/<id>
    2. built-in themes/<id>

    Args:
        theme_id: Theme identifier
        project_themes_dir: Optional project-local PDF themes directory

    Returns:
        Path to theme directory

    Raises:
        PdfThemeNotFoundError: If theme not found
    """
    # Check project-local themes first
    if project_themes_dir:
        local_path = project_themes_dir / theme_id
        if local_path.is_dir():
            return local_path

    # Check built-in themes
    builtin_path = BUILTIN_PDF_THEMES_DIR / theme_id
    if builtin_path.is_dir():
        return builtin_path

    # Theme not found
    available = list_pdf_themes(project_themes_dir)
    raise PdfThemeNotFoundError(
        f"PDF theme '{theme_id}' not found. Available: {', '.join(available) or 'none'}"
    )


def _validate_pdf_theme_pack(
    theme_dir: Path,
    manifest: PdfThemeManifest,
) -> None:
    """
    Validate a PDF theme pack has required files.

    Raises:
        PdfThemeValidationError: If validation fails
    """
    errors = []

    # Check template exists
    template_path = theme_dir / "template.tex"
    if not template_path.exists():
        errors.append("template.tex not found")

    # Check assets directory
    assets_dir = theme_dir / "assets"
    if not assets_dir.is_dir():
        errors.append("assets/ directory not found")
    else:
        # Check for theme.sty
        style_path = assets_dir / "theme.sty"
        if not style_path.exists():
            errors.append("assets/theme.sty not found")

    if errors:
        raise PdfThemeValidationError(
            f"PDF theme '{manifest.id}' validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )


def resolve_pdf_theme(
    theme_id: str,
    project_themes_dir: Path | None = None,
    validate: bool = True,
) -> PdfThemeBundle:
    """
    Resolve a PDF theme by ID and return a PdfThemeBundle.

    Args:
        theme_id: Theme identifier (e.g., "std-report", "corp-report")
        project_themes_dir: Optional project-local PDF themes directory
        validate: Whether to validate the theme pack

    Returns:
        PdfThemeBundle with resolved paths and hashes

    Raises:
        PdfThemeNotFoundError: If theme not found
        PdfThemeValidationError: If theme validation fails
    """
    # Find theme directory
    theme_dir = _find_pdf_theme_dir(theme_id, project_themes_dir)

    # Load or create manifest
    manifest = load_pdf_manifest(theme_dir)
    if manifest is None:
        manifest = create_default_pdf_manifest(theme_id)

    # Validate if requested
    if validate:
        _validate_pdf_theme_pack(theme_dir, manifest)

    # Resolve paths
    template_path = theme_dir / "template.tex"
    assets_dir = theme_dir / "assets"
    style_path = assets_dir / "theme.sty" if (assets_dir / "theme.sty").exists() else None
    fonts_dir = assets_dir / "fonts" if (assets_dir / "fonts").is_dir() else None

    # Compute hashes for reproducibility
    template_hash = _compute_file_hash(template_path)
    style_hash = _compute_file_hash(style_path) if style_path else ""
    assets_hash = _compute_dir_hash(assets_dir)

    return PdfThemeBundle(
        theme_id=theme_id,
        theme_dir=theme_dir,
        template_path=template_path,
        style_path=style_path,
        assets_dir=assets_dir,
        fonts_dir=fonts_dir,
        manifest=manifest,
        template_hash=template_hash,
        style_hash=style_hash,
        assets_hash=assets_hash,
    )


def list_pdf_themes(
    project_themes_dir: Path | None = None,
) -> list[str]:
    """
    List all available PDF theme IDs.

    Args:
        project_themes_dir: Optional project-local PDF themes directory

    Returns:
        List of theme IDs (directory names)
    """
    themes = set()

    # Built-in themes
    if BUILTIN_PDF_THEMES_DIR.is_dir():
        for d in BUILTIN_PDF_THEMES_DIR.iterdir():
            if d.is_dir() and (d / "template.tex").exists():
                themes.add(d.name)

    # Project-local themes
    if project_themes_dir and project_themes_dir.is_dir():
        for d in project_themes_dir.iterdir():
            if d.is_dir() and (d / "template.tex").exists():
                themes.add(d.name)

    return sorted(themes)
