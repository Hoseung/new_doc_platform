#!/usr/bin/env python3
"""
Build script for the extended report example.

Demonstrates the full litepub_norm pipeline with visibility and policy filtering.
This script shows the impact of different build targets (internal, external, dossier)
on the final document content.
"""

import json
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from litepub_norm.normalizer import harness
from litepub_norm.resolver import resolve, ResolutionConfig, load_registry
from litepub_norm.filters import apply_filters, BuildContext, FilterConfig


# Paths
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"


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
) -> dict:
    """Build the document for a specific target."""
    print(f"\n{'='*60}")
    print(f"Building for target: {target} (render: {render_target})")
    print("=" * 60)

    # Resolve placeholders
    config = ResolutionConfig(target=target)
    resolved = resolve(normalized_ast, registry, config)
    print_stats("After resolution:", resolved)

    # Apply filters
    context = BuildContext(build_target=target, render_target=render_target)
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

    return filtered


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Extended Report Build Pipeline")
    print("=" * 60)

    # Load registry files
    norm_registry_path = CONFIG_DIR / "normalization_registry.json"
    aarc_registry_path = CONFIG_DIR / "aarc_registry.json"
    report_path = SRC_DIR / "report.md"

    print(f"Source: {report_path}")
    print(f"Normalization registry: {norm_registry_path}")
    print(f"AARC registry: {aarc_registry_path}")

    # Step 1: Normalize
    print("\n" + "=" * 60)
    print("Stage 1: Normalization")
    print("=" * 60)
    normalized = harness.normalize_file(
        report_path,
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
    targets = [
        ("internal", "html"),
        ("internal", "pdf"),
        ("external", "html"),
        ("external", "pdf"),
        ("dossier", "pdf"),
    ]

    for build_target, render_target in targets:
        filtered = build_for_target(
            normalized,
            aarc_registry,
            build_target,
            render_target,
        )

        # Save filtered AST
        output_name = f"filtered_{build_target}_{render_target}.json"
        output_path = OUTPUT_DIR / output_name
        with open(output_path, "w") as f:
            json.dump(filtered, f, indent=2)
        print(f"Saved: {output_path}")

    # Summary comparison
    print("\n" + "=" * 60)
    print("Summary: Content Comparison by Target")
    print("=" * 60)

    print("\nContent visibility by build target:")
    print("  - internal: ALL content (internal + external + dossier visibility)")
    print("  - external: external + dossier visibility only")
    print("  - dossier: dossier visibility only")

    print("\nPolicy-based exclusions:")
    print("  - draft, wip: excluded from external/dossier")
    print("  - internal-only: excluded from external/dossier")
    print("  - verbose, additional: may be excluded based on config")

    print("\nPresentation transforms:")
    print("  - PDF: large code blocks externalized, large tables to appendix")
    print("  - HTML: large content folded")

    print("\nBuild complete!")


if __name__ == "__main__":
    main()
