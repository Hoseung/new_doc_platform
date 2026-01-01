"""Render report generation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def directory_manifest_hash(directory: Path) -> str:
    """Compute a hash of all files in a directory (sorted, deterministic)."""
    if not directory.exists():
        return ""

    h = hashlib.sha256()
    files = sorted(directory.rglob("*"))
    for f in files:
        if f.is_file():
            # Include relative path and file hash
            rel_path = f.relative_to(directory)
            h.update(str(rel_path).encode())
            h.update(file_hash(f).encode())
    return f"sha256:{h.hexdigest()}"


def get_pandoc_version(pandoc_path: Path | str | None = None) -> str | None:
    """Get pandoc version string."""
    cmd = [str(pandoc_path) if pandoc_path else "pandoc", "--version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # First line is like "pandoc 3.1.9"
            first_line = result.stdout.split("\n")[0]
            return first_line.split()[1] if len(first_line.split()) > 1 else first_line
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
        pass
    return None


def get_latex_version(engine: str, engine_path: Path | str | None = None) -> str | None:
    """Get LaTeX engine version string."""
    cmd = [str(engine_path) if engine_path else engine, "--version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # First line typically contains version info
            first_line = result.stdout.split("\n")[0]
            return first_line.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


@dataclass
class RenderReport:
    """
    Render report for audit and reproducibility.

    Captures all information needed to understand and reproduce a render.
    """

    # Timestamps
    started_at: str = ""
    completed_at: str = ""

    # Tool versions
    pandoc_version: str | None = None
    latex_engine: str | None = None
    latex_engine_version: str | None = None

    # Build context
    build_target: str = ""
    render_target: str = ""
    strict_mode: bool = False

    # Templates and assets
    template_path: str | None = None
    template_hash: str | None = None
    assets_dir: str | None = None
    assets_hash: str | None = None
    lua_filters: list[str] = field(default_factory=list)
    lua_filter_hashes: dict[str, str] = field(default_factory=dict)

    # Output
    output_files: list[str] = field(default_factory=list)

    # Warnings and errors
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def start(self) -> None:
        """Mark the start of rendering."""
        self.started_at = datetime.now(timezone.utc).isoformat()

    def complete(self) -> None:
        """Mark the completion of rendering."""
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def set_pandoc_version(self, pandoc_path: Path | None = None) -> None:
        """Detect and set pandoc version."""
        self.pandoc_version = get_pandoc_version(pandoc_path)

    def set_latex_version(
        self, engine: str, engine_path: Path | None = None
    ) -> None:
        """Detect and set LaTeX engine version."""
        self.latex_engine = engine
        self.latex_engine_version = get_latex_version(engine, engine_path)

    def set_template(self, template_path: Path | None) -> None:
        """Set template info with hash."""
        if template_path and template_path.exists():
            self.template_path = str(template_path)
            self.template_hash = file_hash(template_path)

    def set_assets(self, assets_dir: Path | None) -> None:
        """Set assets info with manifest hash."""
        if assets_dir and assets_dir.exists():
            self.assets_dir = str(assets_dir)
            self.assets_hash = directory_manifest_hash(assets_dir)

    def set_lua_filters(self, filters: tuple[Path, ...] | list[Path]) -> None:
        """Set Lua filter info with hashes."""
        self.lua_filters = [str(f) for f in filters]
        self.lua_filter_hashes = {str(f): file_hash(f) for f in filters if f.exists()}

    def add_output(self, path: Path) -> None:
        """Add an output file."""
        self.output_files.append(str(path))

    def add_warning(self, warning: dict[str, Any]) -> None:
        """Add a warning entry."""
        self.warnings.append(warning)

    def add_error(self, error: dict[str, Any]) -> None:
        """Add an error entry."""
        self.errors.append(error)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamps": {
                "started_at": self.started_at,
                "completed_at": self.completed_at,
            },
            "tools": {
                "pandoc_version": self.pandoc_version,
                "latex_engine": self.latex_engine,
                "latex_engine_version": self.latex_engine_version,
            },
            "context": {
                "build_target": self.build_target,
                "render_target": self.render_target,
                "strict_mode": self.strict_mode,
            },
            "templates": {
                "template_path": self.template_path,
                "template_hash": self.template_hash,
                "assets_dir": self.assets_dir,
                "assets_hash": self.assets_hash,
                "lua_filters": self.lua_filters,
                "lua_filter_hashes": self.lua_filter_hashes,
            },
            "output": {
                "files": self.output_files,
            },
            "diagnostics": {
                "warnings": self.warnings,
                "errors": self.errors,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: Path) -> None:
        """Save report to a JSON file."""
        path.write_text(self.to_json() + "\n", encoding="utf-8")
