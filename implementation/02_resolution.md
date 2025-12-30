# Resolution Stage Implementation

## Overview

The resolution stage replaces placeholder tokens in normalized AST with computed content from analysis artifacts. It follows the AARC v1.1 (Analysis Artifact Registry Contract) specification.

## Module Structure

```
src/litepub_norm/resolver/
├── __init__.py              # Public API exports
├── api.py                   # Top-level resolve() function
├── apply.py                 # Apply resolution plan to AST
├── config.py                # ResolutionConfig, ResolutionLimits
├── errors.py                # Error hierarchy
├── placeholders.py          # Placeholder detection
├── plan.py                  # Resolution plan builder
├── registry.py              # AARC v1.1 registry loader
├── loaders/                 # Payload loaders
│   ├── base.py              # Hash verification, JSON loading
│   ├── metric_v1.py         # metric.json@v1
│   ├── table_simple_v1.py   # table.simple.json@v1
│   ├── table_pandoc_v1.py   # table.pandoc.json@v1
│   └── figure_v1.py         # figure.binary@v1 + sidecar
├── validators/              # Payload validators
│   ├── metric_v1.py
│   ├── table_simple_v1.py
│   ├── table_pandoc_v1.py
│   └── figure_v1.py
└── emitters/                # Pandoc AST emitters
    ├── pandoc_builders.py   # Low-level node builders
    ├── metric_v1.py         # Emit metric as 2-col table
    ├── table_simple_v1.py   # Emit simple table
    ├── table_pandoc_v1.py   # Passthrough for Pandoc tables
    └── figure_v1.py         # Emit Figure block
```

## Supported Payload Types

| Spec | Format | Output |
|------|--------|--------|
| `metric.json@v1` | `{"label", "value", "unit"}` | 2-column Pandoc Table |
| `table.simple.json@v1` | `{"columns", "rows"}` | Pandoc Table |
| `table.pandoc.json@v1` | Pandoc Table block | Passthrough |
| `figure.binary@v1` | PNG/JPG/SVG + sidecar | Pandoc Figure |

## Key Components

### Registry (registry.py)

Loads AARC v1.1 registry JSON with:
- Run provenance (run_id, pipeline, code commit, inputs)
- Artifact entries with URI, hash, spec, origin

```python
@dataclass(frozen=True)
class RegistryEntry:
    id: str
    artifact_type: ArtifactType  # "metric" | "table" | "figure"
    format: str
    spec: str
    uri: str
    sha256: str
    origin_producer: str
    meta_uri: str | None = None
    meta_sha256: str | None = None
    meta_spec: str | None = None
```

### Resolution Plan (plan.py)

Builds a plan by scanning AST for computed wrapper Divs:

```python
@dataclass(frozen=True)
class ResolutionItem:
    semantic_id: str
    entry: RegistryEntry
    wrapper_index: int      # Index in top-level blocks
    placeholder_index: int  # Index within wrapper content
    placeholder: Placeholder
```

### Configuration (config.py)

```python
@dataclass(frozen=True)
class ResolutionConfig:
    target: BuildTarget = "internal"  # "internal" | "external" | "archive"
    strict: bool = True               # Enforce hash verification
    allow_raw_pandoc: bool = False    # Allow RawBlock/RawInline
    limits: ResolutionLimits = ...    # Size limits
```

## Pipeline Flow

```
Normalized AST + AARC Registry
         │
         ▼
    build_plan()
         │
    ┌────┴────┐
    │ For each ResolutionItem:
    │   1. Load payload (loaders/)
    │   2. Validate payload (validators/)
    │   3. Emit Pandoc block (emitters/)
    └────┬────┘
         │
         ▼
   apply_plan()
         │
    Replace placeholder blocks
         │
         ▼
    Resolved AST
```

## Usage

```python
from litepub_norm import normalize_text, resolve, load_registry, Registry

# Step 1: Normalize
norm_registry = Registry.from_dict({
    "metric.face.yaw_mae.v1": {
        "role": "computed",
        "kind": "metric",
        ...
    }
})
ast = normalize_text(markdown, "markdown", norm_registry)

# Step 2: Resolve
aarc_registry = load_registry("registry.json")
resolved = resolve(ast, aarc_registry)
```

## Error Handling

| Error | Cause |
|-------|-------|
| `RegistryError` | Missing entry, invalid registry format |
| `PayloadError` | File not found, invalid JSON, hash mismatch |
| `ValidationError` | Schema violation, size limits exceeded |
| `PlaceholderError` | Missing/multiple placeholders in wrapper |
| `KindMismatchError` | Wrapper kind != registry artifact_type |

## Hash Verification

When `config.strict=True`:
1. Compute SHA256 of payload file
2. Compare with `entry.sha256`
3. Raise `HashMismatchError` on mismatch

Format: `sha256:<hex_digest>`

## Tests

29 tests in `test/test_resolver.py` covering:
- Registry loading and path resolution
- All 4 payload pipelines (load/validate/emit)
- Resolution plan building
- Full resolve() API integration
- Error conditions

## Test Data

Uses `aarc_example_pack/` fixtures:
- `registry_demo_aarc_1_1.json` - 6 entries
- `artifacts/run_demo_2025-12-31/metrics/` - metric payloads
- `artifacts/run_demo_2025-12-31/tables/` - table payloads
- `artifacts/run_demo_2025-12-31/figures/` - figure + sidecar
