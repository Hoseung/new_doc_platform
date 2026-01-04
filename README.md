# LitePub

**Deterministic, AST-centric documentation pipeline for Python teams**

LitePub generates multiple audience-specific documents (internal reports, external KPI reports, regulatory dossiers) from a single source, with quantitative content automatically injected from analysis artifacts.

## The Problem

When producing technical documentation from analysis results:

- **Copy-paste workflow**: Numbers are manually copied from notebooks to Word/Confluence, leading to version drift
- **Multiple audiences**: Internal reports, partner documents, and certification dossiers share content but require separate maintenance
- **Update overhead**: Every software update requires manually refreshing all affected documents
- **Tooling mismatch**: Existing solutions (Quarto, MyST, Typst) require Lua/JavaScript/custom languages, fragmenting Python-based analysis pipelines

## The Solution

LitePub treats documentation as a **compilation process**:

```
Analysis Scripts
    ↓
Artifacts (JSON tables, figures) + Registry
    ↓
Manuscript (.md/.rst) ← Authors write prose only
    ↓
Build Pipeline
    ↓
├── Internal Report (all content)
├── External KPI Report (external + dossier)
└── Dossier (dossier only)
```

**Key principles:**

1. **Semantic IDs link prose to data**: Authors declare `<!-- BEGIN tbl.kpi.yaw_mae.v1 -->`, the system fills in the table
2. **Single source, multiple outputs**: Visibility tags (`internal`, `external`, `dossier`) control what appears in each document
3. **Python-native**: All transformations are Python—use pandas, pytest, and your existing tools
4. **Deterministic builds**: Same inputs always produce identical outputs

## Quick Start

```python
from litepub_norm import normalize_file, resolve, Registry, load_registry
from litepub_norm.filters import apply_filters, BuildContext
from litepub_norm.render import render, default_pdf_config

# 1. Normalize: Parse manuscript and inject registry metadata
norm_registry = Registry.from_file("normalization_registry.json")
normalized_ast = normalize_file("report.md", norm_registry)

# 2. Resolve: Replace placeholders with artifact content
aarc_registry = load_registry("aarc_registry.json", artifact_root="artifacts/")
resolved_ast = resolve(normalized_ast, aarc_registry)

# 3. Filter: Produce audience-specific document
context = BuildContext(build_target="external", render_target="pdf")
filtered_ast, report = apply_filters(resolved_ast, context=context)

# 4. Render: Generate output
config = default_pdf_config()
render(filtered_ast, context, config, "report_external.pdf")
```

## Authoring Example

Authors write manuscripts with semantic placeholders:

```markdown
## Face Detection Performance

<!-- BEGIN tbl.face.yaw_mae.v1 -->
This table shows Mean Absolute Error by yaw angle.
Higher errors at extreme angles (±60°) are expected due to self-occlusion.
<!-- END tbl.face.yaw_mae.v1 -->

<!-- BEGIN tbl.face.yaw_mae.v1.annotation -->
**Interpretation**: The MAE increase at extreme angles is acceptable
for the target use case (frontal gaze monitoring).
<!-- END tbl.face.yaw_mae.v1.annotation -->
```

The table content is automatically injected from analysis artifacts. Authors never copy-paste numbers.

## Visibility Model

Content is tagged with visibility levels that form a strict subset hierarchy:

```
Internal ⊇ External ⊇ Dossier
```

| Level | Included In | Use Case |
|-------|-------------|----------|
| `internal` | Internal only | Debug data, experimental analysis |
| `external` | Internal + External | Official metrics for partners |
| `dossier` | All three | Safety-critical metrics for certification |

This ensures internal-only content can never accidentally leak to external documents.

## Installation

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

**Requirements**: Python 3.10+, Pandoc 3.0+

## Pipeline Architecture

```
Authored Source (.md/.rst)
    ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Adapters   │───▶│ Normalizer  │───▶│  Resolver   │───▶│  Validator  │
│             │    │             │    │             │    │             │
│ md → Div    │    │ + Registry  │    │ + Artifacts │    │ Safety +    │
│ rst → Div   │    │ metadata    │    │ payloads    │    │ Contracts   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                               ↓
                                                        ┌─────────────┐
                                                        │   Filters   │
                                                        │             │
                                                        │ Visibility  │
                                                        │ Policy      │
                                                        │ Presentation│
                                                        └─────────────┘
                                                               ↓
                                                        ┌─────────────┐
                                                        │  Renderers  │
                                                        │             │
                                                        │ HTML / PDF  │
                                                        └─────────────┘
```

## HTML Theming

Four built-in themes for HTML output:

| Theme | Description | Best For |
|-------|-------------|----------|
| `base` | Minimal clean layout | Starting point for customization |
| `sidebar_docs` | Fixed left sidebar with TOC | API docs, reference guides |
| `topbar_classic` | Top navigation bar | Language/library docs |
| `book_tutorial` | Chapter navigation with page TOC | Tutorials, books, courses |

```python
from litepub_norm.render import themed_html_config, render

# Single-page HTML with sidebar theme
config = themed_html_config("sidebar_docs")
result = render(filtered_ast, context, config, "document.html")

# Multi-page site with book theme
config = themed_html_config("book_tutorial", mode="site", split_level=2)
result = render(filtered_ast, context, config, "output_dir/")
```

## PDF Theming

Three theme archetypes for PDF output:

| Archetype | Description | Best For |
|-----------|-------------|----------|
| `std-report` | Standard technical report | Internal documentation |
| `corp-report` | Corporate branding template | Partner deliverables |
| `academic-paper` | Academic paper format | Publications, dossiers |

```python
from litepub_norm.render import themed_pdf_config, render

config = themed_pdf_config("corp-report")
result = render(filtered_ast, context, config, "report.pdf")
```

## Running Tests

```bash
# All tests
uv run pytest test/ -v

# Specific test file
uv run pytest test/test_validators.py -v

# With coverage
uv run pytest test/ --cov=src/litepub_norm
```

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](spec/user_guide_mental_model.md) | Why the system works this way |
| [Architecture](spec/architecture.md) | System design overview |
| [Authoring Conventions](spec/authoring_conventions.md) | How to write manuscripts |
| [AST Invariants](spec/ast_invariants.md) | Structural contracts |
| [Error Codes](spec/error_codes.md) | Troubleshooting build failures |

### Implementation Guides

| Stage | Spec | Implementation |
|-------|------|----------------|
| Normalization | [spec](spec/normalization_v1.md) | [impl](implementation/01_normalization.md) |
| Resolution | [spec](spec/Resolution%20Spec.v1.md) | [impl](implementation/02_resolution.md) |
| Validation | [spec](spec/ast_invariants.md) | [impl](implementation/03_validation.md) |
| Filtering | [spec](spec/filter_design.md) | [impl](implementation/04_filtering.md) |
| Rendering | [spec](spec/rendering_stage_specification.md) | [impl](implementation/05_rendering.md) |

## Why Python-Native?

| Tool | Issue |
|------|-------|
| Quarto | Requires Lua filters; can't directly use pandas or debug in Python |
| MyST | JavaScript ecosystem; requires Node.js runtime |
| Typst | Custom scripting language; can't import torch/pandas |

LitePub keeps everything in Python:

- Debug document transformations with pdb
- Test rendering logic with pytest
- Use pandas DataFrames directly in artifact generation
- Integrate with existing Python CI/CD pipelines

## License

[Add license information]
