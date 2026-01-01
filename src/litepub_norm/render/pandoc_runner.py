"""Pandoc invocation wrapper for deterministic rendering."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .report import get_pandoc_version


class PandocError(Exception):
    """Error during pandoc invocation."""

    def __init__(
        self,
        message: str,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class PandocVersionError(PandocError):
    """Pandoc version mismatch error."""

    pass


@dataclass
class PandocResult:
    """Result of a pandoc invocation."""

    success: bool
    output_path: Path | None
    stdout: str
    stderr: str
    returncode: int
    command: list[str]


def check_pandoc_version(
    pandoc_path: Path | str | None = None,
    required_version: str | None = None,
) -> str:
    """
    Check pandoc version and return it.

    Raises:
        PandocVersionError: If pandoc not found or version mismatch.
    """
    version = get_pandoc_version(pandoc_path)
    if version is None:
        raise PandocVersionError("Pandoc not found or version could not be determined")

    if required_version and version != required_version:
        raise PandocVersionError(
            f"Pandoc version mismatch: found {version}, required {required_version}"
        )

    return version


def _stable_temp_path(content: bytes, suffix: str) -> Path:
    """
    Create a stable temp file path based on content hash.

    This ensures deterministic behavior - same content gets same path.
    """
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    temp_dir = Path(tempfile.gettempdir()) / "litepub_render"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / f"ast_{content_hash}{suffix}"


def run(
    input_ast: dict[str, Any],
    to_format: Literal["html5", "chunkedhtml", "latex", "gfm", "rst", "markdown"],
    output_path: Path,
    pandoc_path: Path | str | None = None,
    template: Path | None = None,
    lua_filters: tuple[Path, ...] | list[Path] = (),
    extra_args: tuple[str, ...] | list[str] = (),
    standalone: bool = True,
) -> PandocResult:
    """
    Run pandoc to convert AST to target format.

    Args:
        input_ast: Pandoc AST as dictionary
        to_format: Output format (html5, chunkedhtml, latex, gfm, rst, markdown)
        output_path: Path for output file (for chunkedhtml, this is a directory)
        pandoc_path: Path to pandoc executable (None = system pandoc)
        template: Template file path
        lua_filters: List of Lua filter paths
        extra_args: Additional pandoc arguments
        standalone: Whether to produce standalone document

    Returns:
        PandocResult with success status and details

    Raises:
        PandocError: If pandoc invocation fails

    Note:
        For chunkedhtml output, the output_path should be a directory path
        without extension. Pandoc will create multiple HTML files in that
        directory including index.html and sitemap.json.
    """
    # Serialize AST to JSON
    ast_json = json.dumps(input_ast, ensure_ascii=False)
    ast_bytes = ast_json.encode("utf-8")

    # Create stable temp file for input
    input_path = _stable_temp_path(ast_bytes, ".json")
    input_path.write_bytes(ast_bytes)

    # Build command
    cmd = [str(pandoc_path) if pandoc_path else "pandoc"]
    cmd.extend(["--from=json", f"--to={to_format}"])

    if standalone:
        cmd.append("--standalone")

    if template and template.exists():
        cmd.extend([f"--template={template}"])

    for lua_filter in lua_filters:
        if lua_filter.exists():
            cmd.extend([f"--lua-filter={lua_filter}"])

    cmd.extend(extra_args)
    cmd.extend(["-o", str(output_path)])
    cmd.append(str(input_path))

    # Ensure output directory exists
    # For chunkedhtml, pandoc creates the directory itself; we create parent
    if to_format == "chunkedhtml":
        # For chunkedhtml, output_path is the directory to create
        # Pandoc will error if it exists, so we ensure parent exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Remove existing output directory if it exists (for rebuild)
        if output_path.exists():
            import shutil
            shutil.rmtree(output_path)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run pandoc
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=None,  # Use current environment, no network isolation needed
        )
    except subprocess.TimeoutExpired as e:
        raise PandocError(
            "Pandoc timed out after 5 minutes",
            stdout=e.stdout or "",
            stderr=e.stderr or "",
        )
    except FileNotFoundError:
        raise PandocError("Pandoc executable not found")

    pandoc_result = PandocResult(
        success=result.returncode == 0,
        output_path=output_path if result.returncode == 0 else None,
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
        command=cmd,
    )

    if not pandoc_result.success:
        raise PandocError(
            f"Pandoc failed with exit code {result.returncode}",
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return pandoc_result


def run_to_string(
    input_ast: dict[str, Any],
    to_format: Literal["html5", "latex", "gfm", "rst", "markdown"],
    pandoc_path: Path | str | None = None,
    template: Path | None = None,
    lua_filters: tuple[Path, ...] | list[Path] = (),
    extra_args: tuple[str, ...] | list[str] = (),
    standalone: bool = True,
) -> str:
    # Note: chunkedhtml is not supported here as it outputs multiple files
    """
    Run pandoc and return output as string.

    Useful for intermediate LaTeX generation before XeLaTeX.

    Args:
        input_ast: Pandoc AST as dictionary
        to_format: Output format
        pandoc_path: Path to pandoc executable
        template: Template file path
        lua_filters: List of Lua filter paths
        extra_args: Additional pandoc arguments
        standalone: Whether to produce standalone document

    Returns:
        Pandoc output as string

    Raises:
        PandocError: If pandoc invocation fails
    """
    # Serialize AST to JSON
    ast_json = json.dumps(input_ast, ensure_ascii=False)
    ast_bytes = ast_json.encode("utf-8")

    # Create stable temp file for input
    input_path = _stable_temp_path(ast_bytes, ".json")
    input_path.write_bytes(ast_bytes)

    # Build command
    cmd = [str(pandoc_path) if pandoc_path else "pandoc"]
    cmd.extend(["--from=json", f"--to={to_format}"])

    if standalone:
        cmd.append("--standalone")

    if template and template.exists():
        cmd.extend([f"--template={template}"])

    for lua_filter in lua_filters:
        if lua_filter.exists():
            cmd.extend([f"--lua-filter={lua_filter}"])

    cmd.extend(extra_args)
    cmd.append(str(input_path))

    # Run pandoc
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as e:
        raise PandocError(
            "Pandoc timed out",
            stdout=e.stdout or "",
            stderr=e.stderr or "",
        )
    except FileNotFoundError:
        raise PandocError("Pandoc executable not found")

    if result.returncode != 0:
        raise PandocError(
            f"Pandoc failed with exit code {result.returncode}",
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return result.stdout
