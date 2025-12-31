# Demo Report Example

A complete example documentation project demonstrating the LitePub pipeline.

## Project Structure

```
demo_report/
├── src/                          # Source documents
│   └── report.md                 # Main report (Markdown with semantic blocks)
├── config/                       # Configuration files
│   ├── litepub.yaml              # Global pipeline configuration
│   ├── normalization_registry.json   # Semantic ID metadata
│   └── aarc_registry.json        # AARC v1.1 artifact registry
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
│   └── 02_resolved.json          # Resolved AST
└── build.py                      # Build script
```

## Quick Start

```bash
# From the project root
uv run python examples/demo_report/build.py --output-ast --skip-hash-verify

# With hash verification (for production)
uv run python examples/demo_report/build.py --output-ast
```

## Pipeline Stages

### 1. Normalization

Parses the source Markdown, identifies semantic blocks (via `<!-- BEGIN/END -->` fences),
and enriches them with metadata from the normalization registry.

**Input:** `src/report.md` + `config/normalization_registry.json`
**Output:** `build/01_normalized.json`

### 2. Resolution

Replaces placeholder tokens (`[[COMPUTED:TABLE]]`, `[[COMPUTED:METRIC]]`, etc.) with
actual content from the artifact registry.

**Input:** Normalized AST + `config/aarc_registry.json`
**Output:** `build/02_resolved.json`

### 3. Transformation (Future)

Applies visibility filtering based on target (internal/external).

### 4. Presentation (Future)

Generates final output formats (HTML, PDF) via Pandoc.

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

| Format | Spec | Description |
|--------|------|-------------|
| `metric.json` | `metric.json@v1` | Single KPI value with label, unit |
| `table.simple.json` | `table.simple.json@v1` | Columns + rows structure |
| `table.pandoc.json` | `table.pandoc.json@v1` | Native Pandoc Table block |
| `image.png` | `figure.binary@v1` | Binary image with sidecar metadata |
