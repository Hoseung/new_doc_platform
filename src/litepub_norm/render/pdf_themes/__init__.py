"""
PDF theming system.

Provides theme packs for PDF rendering via XeLaTeX.
Each theme pack contains: template.tex, theme.yaml, and assets/ (theme.sty, fonts).
"""

from .manifest import PdfThemeManifest, load_pdf_manifest
from .resolver import (
    PdfThemeBundle,
    resolve_pdf_theme,
    list_pdf_themes,
    PdfThemeNotFoundError,
    PdfThemeValidationError,
)

__all__ = [
    "PdfThemeManifest",
    "load_pdf_manifest",
    "PdfThemeBundle",
    "resolve_pdf_theme",
    "list_pdf_themes",
    "PdfThemeNotFoundError",
    "PdfThemeValidationError",
]
