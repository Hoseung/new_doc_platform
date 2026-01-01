#!/usr/bin/env python3
"""
Build RST source to RTD-like HTML.

Usage:
    python build.py                    # Single-page HTML
    python build.py --site             # Multi-page site
    python build.py --theme sidebar_docs  # Specify theme
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from litepub_norm.normalizer import harness
from litepub_norm.resolver import resolve, ResolutionConfig, load_registry
from litepub_norm.filters import apply_filters, BuildContext
from litepub_norm.render import render, themed_html_config
from litepub_norm.theming import list_available_themes


# === Configuration ===
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR               # RST files are in this directory
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"

# RST files in order (matches toctree in index.rst)
RST_FILES = [
    "index.rst",
    "chapters/01-introduction.rst",
    "chapters/02-methodology.rst",
    "chapters/03-results.rst",
    "chapters/04-conclusion.rst",
    "chapters/05-korean-example.rst",
    "chapters/06-system-overview.rst",
    "chapters/90-appendix-documentation.rst",
]


def concatenate_rst(files: list[str]) -> str:
    """Concatenate RST files in order."""
    parts = []
    for filename in files:
        filepath = SRC_DIR / filename
        if filepath.exists():
            parts.append(filepath.read_text(encoding="utf-8"))
        else:
            print(f"Warning: {filepath} not found")
    return "\n\n".join(parts)


def build(
    theme: str = "sidebar_docs",
    site_mode: bool = False,
    split_level: int = 2,
    build_target: str = "external",
):
    """Build RST to HTML with specified theme."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print(f"Building with theme: {theme}")
    print(f"Mode: {'site' if site_mode else 'single-page'}")
    
    # 1. Concatenate RST files
    rst_content = concatenate_rst(RST_FILES)
    print(f"Combined {len(RST_FILES)} files")
    
    # 2. Normalize to Pandoc AST
    norm_registry = CONFIG_DIR / "normalization_registry.json"
    normalized_ast = harness.normalize_text(
        rst_content,
        "rst",
        norm_registry,
        mode="draft"
    )
    print("Normalization complete")
    
    # 3. Resolve computed blocks (if you have them)
    aarc_registry_path = CONFIG_DIR / "aarc_registry.json"
    if aarc_registry_path.exists():
        aarc_registry = load_registry(aarc_registry_path)
        config = ResolutionConfig(target=build_target, strict=False)
        resolved_ast = resolve(normalized_ast, aarc_registry, config)
    else:
        resolved_ast = normalized_ast
    print("Resolution complete")
    
    # 4. Apply filters
    context = BuildContext(build_target=build_target, render_target="html")
    filtered_ast, report = apply_filters(resolved_ast, context=context)
    print(f"Filtering complete ({len(report.entries)} entries)")
    
    # 5. Render with theme
    output_dir = OUTPUT_DIR / f"{build_target}_{'site' if site_mode else 'html'}"
    
    config = themed_html_config(
        theme,
        mode="site" if site_mode else "single",
        split_level=split_level,
    ).with_output_dir(output_dir)
    
    output_name = "docs" if site_mode else "index.html"
    result = render(filtered_ast, context, config, output_name)
    
    # 6. Report result
    if result.success:
        print(f"\nSuccess! Output: {result.primary_output}")
        if site_mode:
            pages = [f for f in result.output_files if str(f).endswith('.html')]
            print(f"Generated {len(pages)} pages")
    else:
        print("\nBuild failed:")
        for err in result.errors:
            print(f"  {err.code}: {err.message}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Build RST to HTML")
    parser.add_argument("--site", action="store_true", help="Multi-page site")
    parser.add_argument("--split-level", type=int, default=2, 
                        help="Split level (1=chapters, 2=sections)")
    parser.add_argument("--theme", default="sidebar_docs",
                        choices=list_available_themes(),
                        help="Theme to use")
    parser.add_argument("--target", default="external",
                        choices=["internal", "external", "dossier"],
                        help="Build target")
    
    args = parser.parse_args()
    
    build(
        theme=args.theme,
        site_mode=args.site,
        split_level=args.split_level,
        build_target=args.target,
    )


if __name__ == "__main__":
    main()
