#!/usr/bin/env python3
"""
Build script for the rst_source example.

Demonstrates the litepub_norm pipeline with RST source files.
This script shows how to process multi-file RST documents through
the normalization, resolution, filtering, and rendering stages.

PIPELINE NOTES:
- RST files are concatenated in order before processing
- The RST adapter wraps figure/table directives with :name: as semantic blocks
- Inline tables remain as regular content (not externalized)
- Figures are verified against the AARC registry

Usage:
    python build.py              # Build all targets (single-page HTML/PDF)
    python build.py --site       # Build multi-page static site
    python build.py --help       # Show help
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from litepub_norm.normalizer import harness
from litepub_norm.resolver import resolve, ResolutionConfig, load_registry
from litepub_norm.filters import apply_filters, BuildContext, FilterConfig
from litepub_norm.render import render, RenderConfig
from litepub_norm.render.config import (
    default_html_config,
    default_html_site_config,
    default_pdf_config,
    themed_pdf_config,
)
from litepub_norm.render.pdf_themes import list_pdf_themes


# Paths
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"


# Chapter order (matches toctree in index.rst)
CHAPTER_ORDER = [
    "index.rst",
    "chapters/01-introduction.rst",
    "chapters/02-methodology.rst",
    "chapters/03-results.rst",
    "chapters/04-conclusion.rst",
    "chapters/05-korean-example.rst",
    "chapters/06-system-overview.rst",
    "chapters/90-appendix-documentation.rst",
]


def concatenate_rst_files() -> str:
    """
    Concatenate RST files in the correct order.

    Returns:
        Combined RST content as a single string.
    """
    parts = []
    for filename in CHAPTER_ORDER:
        filepath = SRC_DIR / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            # Add a separator comment between files
            parts.append(f"\n.. File: {filename}\n\n")
            parts.append(content)
        else:
            print(f"Warning: {filepath} not found")

    return "\n".join(parts)


def count_wrappers(ast: dict) -> dict:
    """Count wrapper Divs by kind and visibility."""
    counts = {"total": 0, "by_kind": {}, "by_visibility": {}}

    def walk(node):
        if isinstance(node, dict):
            if node.get("t") == "Div":
                # Check attributes
                attrs = node.get("c", [[]])[0]
                identifier = attrs[0] if len(attrs) > 0 else ""
                classes = attrs[1] if len(attrs) > 1 else []
                kv = dict(attrs[2]) if len(attrs) > 2 else {}

                # Count wrappers with IDs (semantic blocks)
                if identifier:
                    counts["total"] += 1
                    kind = kv.get("kind", "unknown")
                    vis = kv.get("visibility", "unknown")

                    counts["by_kind"][kind] = counts["by_kind"].get(kind, 0) + 1
                    counts["by_visibility"][vis] = counts["by_visibility"].get(vis, 0) + 1

            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(ast)
    return counts


def print_stats(label: str, ast: dict):
    """Print statistics about an AST."""
    counts = count_wrappers(ast)
    print(f"\n{label}")
    print(f"  Total wrappers: {counts['total']}")
    print(f"  By kind: {counts['by_kind']}")
    print(f"  By visibility: {counts['by_visibility']}")


def build_for_target(
    normalized_ast: dict,
    registry,
    target: str,
    render_target: str = "html",
    do_render: bool = False,
    site_mode: bool = False,
    split_level: int = 1,
    pdf_theme: str | None = None,
) -> tuple[dict, bool]:
    """Build the document for a specific target.

    Returns:
        Tuple of (filtered_ast, render_success). render_success is True if
        rendering succeeded or was not requested.
    """
    render_success = True
    mode_label = f"{render_target}" + (" site" if site_mode else "")
    print(f"\n{'='*60}")
    print(f"Building for target: {target} (render: {mode_label})")
    print("=" * 60)

    # Resolve placeholders
    config = ResolutionConfig(target=target, strict=False)  # Non-strict for RST
    resolved = resolve(normalized_ast, registry, config)
    print_stats("After resolution:", resolved)

    # Apply filters
    # For internal builds, use non-strict mode to enable syntax highlighting
    is_strict = target != "internal"
    context = BuildContext(build_target=target, render_target=render_target, strict=is_strict)
    filter_config = FilterConfig()
    filtered, report = apply_filters(resolved, filter_config, context)

    print_stats("After filtering:", filtered)

    # Report summary
    print(f"\n  Filter report summary:")
    print(f"    Total entries: {len(report.entries)}")
    # Group by action for cleaner output
    actions = {}
    for entry in report.entries:
        key = entry.action
        if key not in actions:
            actions[key] = []
        actions[key].append(entry.semantic_id)
    for action, ids in sorted(actions.items()):
        print(f"      [{action}] ({len(ids)} items): {', '.join(ids[:5])}{'...' if len(ids) > 5 else ''}")

    # Render if requested
    if do_render:
        if site_mode and render_target == "html":
            print(f"\n  Rendering to HTML site (split_level={split_level})...")
            render_output_dir = OUTPUT_DIR / f"{target}_site"

            # Use site config
            render_config = default_html_site_config(split_level).with_output_dir(render_output_dir)
            output_name = "whitepaper"  # Directory name for site

            render_result = render(filtered, context, render_config, output_name)

            if render_result.success:
                print(f"    Rendered successfully!")
                print(f"    Site directory: {render_result.primary_output}")
                # List some generated pages
                pages = [f for f in render_result.output_files if str(f).endswith('.html')]
                print(f"    Generated {len(pages)} pages")
                for page in pages[:5]:
                    print(f"      - {page.name if hasattr(page, 'name') else page}")
                if len(pages) > 5:
                    print(f"      ... and {len(pages) - 5} more")
            else:
                render_success = False
                print(f"    Render failed!")
                for err in render_result.errors:
                    print(f"      Error: {err.code} - {err.message}")
        else:
            print(f"\n  Rendering to {render_target}...")
            render_output_dir = OUTPUT_DIR / f"{target}_{render_target}"

            # Use appropriate default config and override output_dir
            if render_target == "pdf":
                if pdf_theme:
                    print(f"    Using PDF theme: {pdf_theme}")
                    render_config = themed_pdf_config(pdf_theme).with_output_dir(render_output_dir)
                else:
                    render_config = default_pdf_config().with_output_dir(render_output_dir)
            else:
                render_config = default_html_config().with_output_dir(render_output_dir)

            output_name = f"whitepaper.{render_target}" if render_target != "pdf" else "whitepaper.pdf"

            render_result = render(filtered, context, render_config, output_name)

            if render_result.success:
                print(f"    Rendered successfully!")
                print(f"    Primary output: {render_result.primary_output}")
                for f in render_result.output_files[1:4]:  # Show first few secondary files
                    print(f"    Secondary: {f}")
            else:
                render_success = False
                print(f"    Render failed!")
                for err in render_result.errors:
                    print(f"      Error: {err.code} - {err.message}")

    return filtered, render_success


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Build RST source documents through the litepub_norm pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py              # Build single-page HTML and PDF
  python build.py --site       # Build multi-page static site
  python build.py --site --split-level=1  # Split at section level
        """
    )
    parser.add_argument(
        "--site",
        action="store_true",
        help="Build multi-page static site instead of single-page HTML"
    )
    parser.add_argument(
        "--split-level",
        type=int,
        default=1,
        help="Split level for site mode (1=chapters, 2=sections, 3=subsections, default: 1)"
    )
    parser.add_argument(
        "--only-site",
        action="store_true",
        help="Only build site (skip single-page HTML/PDF builds)"
    )
    parser.add_argument(
        "--pdf-theme",
        type=str,
        default=None,
        choices=list_pdf_themes(),
        help=f"PDF theme to use. Available: {', '.join(list_pdf_themes())}"
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print("RST Source Build Pipeline")
    print("=" * 60)

    # Load registry files
    norm_registry_path = CONFIG_DIR / "normalization_registry.json"
    aarc_registry_path = CONFIG_DIR / "aarc_registry.json"

    print(f"Source directory: {SRC_DIR}")
    print(f"Normalization registry: {norm_registry_path}")
    print(f"AARC registry: {aarc_registry_path}")
    if args.site:
        print(f"Site mode: enabled (split_level={args.split_level})")
    if args.pdf_theme:
        print(f"PDF theme: {args.pdf_theme}")

    # Step 0: Concatenate RST files
    print("\n" + "=" * 60)
    print("Stage 0: Concatenating RST files")
    print("=" * 60)
    combined_rst = concatenate_rst_files()
    print(f"Combined {len(CHAPTER_ORDER)} files, {len(combined_rst)} characters total")

    # Save combined RST for debugging
    combined_path = OUTPUT_DIR / "combined.rst"
    combined_path.write_text(combined_rst, encoding="utf-8")
    print(f"Saved: {combined_path}")

    # Step 1: Normalize
    print("\n" + "=" * 60)
    print("Stage 1: Normalization")
    print("=" * 60)

    normalized = harness.normalize_text(
        combined_rst,
        "rst",
        norm_registry_path,
        mode="draft"  # Allow unknown IDs as warnings
    )
    print_stats("After normalization:", normalized)

    # Save normalized AST
    norm_output = OUTPUT_DIR / "normalized.json"
    with open(norm_output, "w") as f:
        json.dump(normalized, f, indent=2)
    print(f"Saved: {norm_output}")

    # Load AARC registry for resolution
    aarc_registry = load_registry(aarc_registry_path)

    # Step 2: Build for different targets
    # Tuple: (build_target, render_target, do_render, site_mode)
    if args.only_site:
        # Only build site
        targets = [
            ("internal", "html", True, True),  # Render site
        ]
    elif args.site:
        # Build both regular and site
        targets = [
            ("internal", "html", True, False),  # Single-page HTML
            ("internal", "pdf", True, False),   # PDF
            ("internal", "html", True, True),   # Multi-page site
            ("external", "html", True, False),  # External HTML
            ("dossier", "pdf", True, False),    # Dossier PDF
        ]
    else:
        # Regular build (no site)
        targets = [
            ("internal", "html", True, False),  # Render HTML
            ("internal", "pdf", True, False),   # Render PDF
            ("external", "html", True, False),  # Render HTML
            ("dossier", "pdf", True, False),    # Render PDF for dossier
        ]

    failures = []
    for build_target, render_target, do_render, site_mode in targets:
        try:
            filtered, render_success = build_for_target(
                normalized,
                aarc_registry,
                build_target,
                render_target,
                do_render=do_render,
                site_mode=site_mode,
                split_level=args.split_level,
                pdf_theme=args.pdf_theme,
            )

            if not render_success:
                mode_suffix = " (site)" if site_mode else ""
                failures.append(f"{build_target}/{render_target}{mode_suffix}")

            # Save filtered AST
            suffix = "_site" if site_mode else f"_{render_target}"
            output_name = f"filtered_{build_target}{suffix}.json"
            output_path = OUTPUT_DIR / output_name
            with open(output_path, "w") as f:
                json.dump(filtered, f, indent=2)
            print(f"Saved: {output_path}")
        except Exception as e:
            mode_suffix = " (site)" if site_mode else ""
            failures.append(f"{build_target}/{render_target}{mode_suffix}")
            print(f"  ERROR during {build_target}/{render_target}: {e}")
            import traceback
            traceback.print_exc()

    # Summary comparison
    print("\n" + "=" * 60)
    print("Summary: Content Comparison by Target")
    print("=" * 60)

    print("\nContent visibility by build target:")
    print("  - internal: ALL content (internal + external + dossier visibility)")
    print("  - external: external + dossier visibility only")
    print("  - dossier: dossier visibility only")

    if args.site:
        print("\nSite mode outputs:")
        print(f"  - internal_site/: Multi-page static site (split_level={args.split_level})")

    # Final status
    if failures:
        print(f"\nBuild completed with {len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\nBuild complete!")


if __name__ == "__main__":
    main()
