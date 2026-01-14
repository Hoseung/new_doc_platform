# Pipeline Stages Demo (Normalization + Resolution)

This example demonstrates the **AST processing stages** of the LitePub pipeline.
It does **NOT** produce final document output (HTML/PDF) - only intermediate JSON
AST files for inspection and debugging.

**For a complete example that renders actual documents, see `examples/rst_source/`.**

## What This Demo Does

1. **Normalization**: Parses Markdown source into Pandoc AST with semantic metadata
2. **Resolution**: Replaces placeholders with computed content from artifact files
3. **Transformation**: *(not implemented - placeholder only)*
4. **Presentation**: *(not implemented - placeholder only)*

## Project Structure

```
pipeline_stages_demo/
├── src/                          # Source documents
│   └── report.md                 # Main report (Markdown with semantic blocks)
├── config/                       # Configuration files
│   ├── litepub.yaml              # Global pipeline configuration
│   ├── normalization_registry.json   # Semantic ID metadata
│   └── aarc_registry.json        # AARC v1.1 artifact registry
├── schemas/                      # JSON Schema definitions
│   ├── metric.json.v1.schema.json
│   ├── table.simple.json.v1.schema.json
│   ├── table.pandoc.json.v1.schema.json
│   └── figure.meta.json.v1.schema.json
├── artifacts/                    # Computed artifacts (from analysis pipeline)
│   ├── metrics/
│   │   ├── yaw_mae.json          # metric.json@v1
│   │   └── eye_open_ratio.json   # metric.json@v1
│   ├── tables/
│   │   ├── yaw_mae_table.json    # table.simple.json@v1
│   │   ├── occ_cls_confusion.json    # table.simple.json@v1
│   │   └── category_hierarchy.table.json  # table.pandoc.json@v1
│   └── figures/
│       ├── dummy_plot.png        # figure.binary@v1
│       └── dummy_plot.meta.json  # figure.meta.json@v1
├── build/                        # Build outputs (generated)
│   ├── 01_normalized.json        # Normalized AST
│   ├── 02_resolution_report.json # Resolution debugging info
│   └── 02_resolved.json          # Resolved AST
└── build.py                      # Build script
```

## Quick Start

```bash
# From the project root
uv run python examples/pipeline_stages_demo/build.py --output-ast --skip-hash-verify

# With hash verification (for production)
uv run python examples/pipeline_stages_demo/build.py --output-ast
```

## Output

Running with `--output-ast` generates JSON files in `build/`:

| File | Description |
|------|-------------|
| `01_normalized.json` | Pandoc AST with semantic Divs and placeholder tokens |
| `02_resolution_report.json` | Debugging report with hash verification status |
| `02_resolved.json` | Final Pandoc AST with computed content embedded |

**Note:** No HTML or PDF files are generated. This demo only produces intermediate AST files.

## Semantic Blocks

The source document contains these semantic blocks:

| ID | Type | Description |
|----|------|-------------|
| `metric.face.yaw_mae.v1` | metric | Face yaw MAE value |
| `metric.driver.eye_open_ratio.v1` | metric | Eye openness ratio |
| `tbl.kpi.face.yaw_mae.v1` | table | Yaw MAE by angle range |
| `tbl.kpi.face.yaw_mae.v1.annotation` | annotation | Interpretation notes |
| `tbl.occ_cls.confusion_matrix.v1` | table | Occlusion confusion matrix |
| `tbl.summary.category_hierarchy.v1` | table | Category distribution |
| `fig.demo.dummy_plot.v1` | figure | Performance visualization |

## Configuration Files

### normalization_registry.json

Maps semantic IDs to metadata:
- `role`: "computed" (from artifacts), "hybrid" (author + computed), "authored"
- `kind`: "metric", "table", "figure", "annotation"
- `visibility`: "internal", "external"

### aarc_registry.json

AARC v1.1 format linking semantic IDs to artifact files:
- `artifact_root`: Base path for artifact URIs
- `entries`: List of artifacts with URI, SHA256, spec version
- `run`: Provenance information (pipeline, commit, inputs)

### litepub.yaml

Global configuration:
- Project metadata
- Build targets with visibility filters
- Resolution settings (strict mode, limits)
- Output format preferences

## Artifact Formats

| Format | Spec | Schema | Description |
|--------|------|--------|-------------|
| `metric.json` | `metric.json@v1` | `schemas/metric.json.v1.schema.json` | Single KPI value with label, unit |
| `table.simple.json` | `table.simple.json@v1` | `schemas/table.simple.json.v1.schema.json` | Columns + rows structure |
| `table.pandoc.json` | `table.pandoc.json@v1` | `schemas/table.pandoc.json.v1.schema.json` | Native Pandoc Table block |
| `image.png` | `figure.binary@v1` | `schemas/figure.meta.json.v1.schema.json` | Binary image with sidecar metadata |

## Schema Validation

The `schemas/` directory contains JSON Schema files for formal validation of artifacts.
These can be used with tools like `ajv`, `jsonschema`, or IDE plugins for validation.

Example validation with Python:
```python
import json
import jsonschema

with open("schemas/metric.json.v1.schema.json") as f:
    schema = json.load(f)

with open("artifacts/metrics/yaw_mae.json") as f:
    payload = json.load(f)

jsonschema.validate(payload, schema)  # Raises if invalid
```
