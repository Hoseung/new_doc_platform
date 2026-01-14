#!/usr/bin/env python3
"""
Pipeline stages demo: Normalization and Resolution only.

This script demonstrates the AST processing stages of the LitePub pipeline.
It does NOT produce final document output (HTML/PDF) - only intermediate
JSON AST files for inspection and debugging.

Stages implemented:
  1. Normalization: Parse Markdown -> Pandoc AST, inject semantic metadata
  2. Resolution: Replace placeholders with computed content from artifacts

Stages NOT implemented (placeholders only):
  3. Transformation: Visibility filtering
  4. Presentation: HTML/PDF rendering

For a complete example that produces actual documents, see:
  examples/rst_source/

Usage:
    python build.py [--target internal|external] [--output-ast]

Output (with --output-ast):
    build/01_normalized.json        - AST after normalization
    build/02_resolved.json          - AST after resolution
    build/02_resolution_report.json - Debug info
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from litepub_norm import (
    normalize_file,
    resolve,
    build_resolution_plan,
    load_registry,
    Registry,
    ResolutionConfig,
)
from litepub_norm.serialize import serialize
from litepub_norm.resolver.report import build_resolution_report


def main():
    parser = argparse.ArgumentParser(
        description="Demo: Normalization and Resolution stages (no document output)"
    )
    parser.add_argument(
        "--target",
        choices=["internal", "external"],
        default="internal",
        help="Build target (default: internal)",
    )
    parser.add_argument(
        "--output-ast",
        action="store_true",
        help="Save intermediate AST files",
    )
    parser.add_argument(
        "--skip-hash-verify",
        action="store_true",
        help="Skip SHA256 hash verification (for development)",
    )
    args = parser.parse_args()

    # Paths
    example_dir = Path(__file__).parent
    src_file = example_dir / "src" / "report.md"
    norm_registry_file = example_dir / "config" / "normalization_registry.json"
    aarc_registry_file = example_dir / "config" / "aarc_registry.json"
    build_dir = example_dir / "build"
    build_dir.mkdir(exist_ok=True)

    print(f"Building report for target: {args.target}")
    print(f"Source: {src_file}")
    print()

    # Step 1: Normalization
    print("=" * 60)
    print("Stage 1: NORMALIZATION")
    print("=" * 60)

    with open(norm_registry_file) as f:
        norm_registry_data = json.load(f)
    norm_registry = Registry.from_dict(norm_registry_data)

    print(f"  Loading source: {src_file.name}")
    print(f"  Registry entries: {len(norm_registry_data)}")

    normalized_ast = normalize_file(str(src_file), norm_registry)

    # Count blocks
    blocks = normalized_ast.get("blocks", [])
    div_count = sum(1 for b in blocks if b.get("t") == "Div")
    print(f"  Normalized blocks: {len(blocks)} ({div_count} semantic Divs)")

    if args.output_ast:
        normalized_path = build_dir / "01_normalized.json"
        with open(normalized_path, "w") as f:
            f.write(serialize(normalized_ast))
            f.write("\n")
        print(f"  Saved: {normalized_path}")

    print()

    # Step 2: Resolution
    print("=" * 60)
    print("Stage 2: RESOLUTION")
    print("=" * 60)

    aarc_registry = load_registry(aarc_registry_file)
    print(f"  AARC registry: {aarc_registry_file.name}")
    print(f"  Registry entries: {len(aarc_registry.entries)}")
    print(f"  Run ID: {aarc_registry.run.run_id}")

    config = ResolutionConfig(
        target=args.target,
        strict=not args.skip_hash_verify,
    )

    # Build resolution plan first (for reporting)
    plan = build_resolution_plan(normalized_ast, aarc_registry, config)
    print(f"  Resolution plan: {len(plan)} items")

    # Generate resolution report (pre-resolution debugging info)
    if args.output_ast:
        report = build_resolution_report(plan, aarc_registry, config)
        report_path = build_dir / "02_resolution_report.json"
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  Resolution report: {report_path.name}")

        # Print hash verification summary
        hash_ok = sum(1 for item in report.items if item.hash_match)
        hash_fail = sum(1 for item in report.items if item.hash_match is False)
        print(f"  Hash verification: {hash_ok} OK, {hash_fail} mismatch")

    # Apply resolution
    resolved_ast = resolve(normalized_ast, aarc_registry, config)

    # Count resolved content
    resolved_tables = 0
    resolved_figures = 0
    for block in resolved_ast.get("blocks", []):
        if block.get("t") == "Div":
            content = block.get("c", [[], []])[1]
            for inner in content:
                if inner.get("t") == "Table":
                    resolved_tables += 1
                elif inner.get("t") == "Figure":
                    resolved_figures += 1

    print(f"  Resolved tables: {resolved_tables}")
    print(f"  Resolved figures: {resolved_figures}")

    if args.output_ast:
        resolved_path = build_dir / "02_resolved.json"
        with open(resolved_path, "w") as f:
            f.write(serialize(resolved_ast))
            f.write("\n")
        print(f"  Saved: {resolved_path.name}")

    print()

    # Step 3: Transformation (placeholder for future)
    print("=" * 60)
    print("Stage 3: TRANSFORMATION (not yet implemented)")
    print("=" * 60)
    print(f"  Target: {args.target}")
    print("  [Would apply visibility filtering here]")
    print()

    # Step 4: Presentation (placeholder for future)
    print("=" * 60)
    print("Stage 4: PRESENTATION (not yet implemented)")
    print("=" * 60)
    print("  [Would generate HTML/PDF here using Pandoc]")
    print()

    # Summary
    print("=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"  Output directory: {build_dir}")
    if args.output_ast:
        print("  Generated files:")
        for f in sorted(build_dir.glob("*.json")):
            print(f"    - {f.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
