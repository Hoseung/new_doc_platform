"""LaTeX compilation wrapper for PDF generation."""

from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path


class LatexError(Exception):
    """Error during LaTeX compilation."""

    def __init__(
        self,
        message: str,
        returncode: int | None = None,
        log_file: Path | None = None,
    ):
        super().__init__(message)
        self.returncode = returncode
        self.log_file = log_file


@dataclass
class LatexResult:
    """Result of a LaTeX compilation."""

    success: bool
    pdf_path: Path | None
    log_path: Path | None
    returncode: int
    runs: int


def build(
    latex_path: Path,
    output_dir: Path | None = None,
    engine: str = "xelatex",
    engine_path: Path | str | None = None,
    runs: int = 2,
    timeout: int = 300,
) -> LatexResult:
    """
    Compile LaTeX to PDF using XeLaTeX or other engine.

    Args:
        latex_path: Path to .tex file
        output_dir: Output directory (defaults to same as input)
        engine: LaTeX engine to use (xelatex, pdflatex, lualatex)
        engine_path: Path to engine executable (None = use system)
        runs: Number of compilation runs (for references, TOC, etc.)
        timeout: Timeout per run in seconds

    Returns:
        LatexResult with success status and paths

    Raises:
        LatexError: If compilation fails
    """
    if not latex_path.exists():
        raise LatexError(f"LaTeX file not found: {latex_path}")

    # Determine output directory
    if output_dir is None:
        output_dir = latex_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    engine_cmd = str(engine_path) if engine_path else engine

    # Common flags for reproducible builds
    cmd = [
        engine_cmd,
        "-interaction=nonstopmode",  # Don't stop for errors
        "-halt-on-error",  # But do halt on serious errors
        "-file-line-error",  # Better error messages
        f"-output-directory={output_dir}",
    ]

    # XeLaTeX-specific flags
    if engine in ("xelatex", "lualatex"):
        cmd.append("-shell-escape")  # May be needed for some packages

    cmd.append(str(latex_path))

    # Run compilation multiple times
    last_returncode = 0
    for run_num in range(1, runs + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=latex_path.parent,
            )
            last_returncode = result.returncode

            # Check for fatal errors
            if result.returncode != 0:
                # Check log for actual errors vs warnings
                log_path = output_dir / f"{latex_path.stem}.log"
                raise LatexError(
                    f"LaTeX compilation failed on run {run_num}",
                    returncode=result.returncode,
                    log_file=log_path if log_path.exists() else None,
                )

        except subprocess.TimeoutExpired:
            raise LatexError(
                f"LaTeX timed out after {timeout}s on run {run_num}",
                returncode=-1,
            )
        except FileNotFoundError:
            raise LatexError(f"LaTeX engine not found: {engine_cmd}")

    # Check for output PDF
    pdf_name = latex_path.stem + ".pdf"
    pdf_path = output_dir / pdf_name
    log_path = output_dir / f"{latex_path.stem}.log"

    if not pdf_path.exists():
        raise LatexError(
            "PDF was not generated",
            returncode=last_returncode,
            log_file=log_path if log_path.exists() else None,
        )

    return LatexResult(
        success=True,
        pdf_path=pdf_path,
        log_path=log_path if log_path.exists() else None,
        returncode=0,
        runs=runs,
    )


def cleanup_aux_files(latex_path: Path, output_dir: Path | None = None) -> None:
    """
    Clean up auxiliary files from LaTeX compilation.

    Removes .aux, .log, .out, .toc, etc.
    """
    if output_dir is None:
        output_dir = latex_path.parent

    stem = latex_path.stem
    aux_extensions = [
        ".aux", ".log", ".out", ".toc", ".lof", ".lot",
        ".bbl", ".blg", ".idx", ".ind", ".ilg",
        ".nav", ".snm", ".vrb", ".fdb_latexmk", ".fls",
    ]

    for ext in aux_extensions:
        aux_file = output_dir / f"{stem}{ext}"
        if aux_file.exists():
            aux_file.unlink()


def is_engine_available(engine: str = "xelatex") -> bool:
    """Check if a LaTeX engine is available."""
    return shutil.which(engine) is not None
