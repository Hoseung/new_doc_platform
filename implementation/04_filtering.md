# Filtering Stage Documentation

## Overview

The filtering stage is the fourth stage in the LitePub documentation pipeline. It transforms a resolved and validated AST into target-specific documents by applying a series of deterministic filters.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Normalization  │───▶│   Resolution    │───▶│   Validation    │───▶│   FILTERING     │
│                 │    │                 │    │                 │    │                 │
│ • Parse source  │    │ • Load payloads │    │ • Schema check  │    │ • Visibility    │
│ • Wrap computed │    │ • Validate      │    │ • Safety check  │    │ • Policy        │
│   blocks        │    │ • Emit AST      │    │ • Invariants    │    │ • Metadata      │
│                 │    │                 │    │                 │    │ • Presentation  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

The filtering stage implements **monotonic condensation**:

```
Internal → External → Dossier
```

Downstream targets may only remove or redact content, never introduce new analytic results.

---

## Module Architecture

```
src/litepub_norm/filters/
├── __init__.py           # Public API exports
├── api.py                # Main pipeline API
├── context.py            # BuildContext dataclass
├── config.py             # FilterConfig with defaults
├── report.py             # FilterReport model
├── visibility.py         # Filter 1: Visibility
├── policy.py             # Filter 2: Policy tags
├── metadata_strip.py     # Filter 3: Metadata sanitization
├── presentation.py       # Filter 4: PDF/HTML transforms
└── utils/
    ├── wrappers.py       # Wrapper detection and manipulation
    ├── ast_walk.py       # AST traversal utilities
    ├── text_metrics.py   # Size estimation
    └── sectioning.py     # Appendix builder
```

---

## Core Modules

### context.py — BuildContext

The `BuildContext` is an immutable dataclass that captures the build environment for filter operations.

```python
@dataclass(frozen=True)
class BuildContext:
    build_target: BuildTarget = "internal"   # "internal" | "external" | "dossier"
    render_target: RenderTarget = "pdf"      # "pdf" | "html" | "md" | "rst"
    strict: bool = True                      # Forced True for external/dossier
    project_root: str = "."                  # Root path for relative links
    artifact_base_url: str | None = None     # Base URL for externalized artifacts
```

**Key behaviors:**
- Immutable (frozen dataclass) — cannot be modified after creation
- External/dossier targets automatically force `strict=True`
- Serializable to JSON for debugging

**Usage:**
```python
from litepub_norm.filters import BuildContext

# For internal PDF build
context = BuildContext(build_target="internal", render_target="pdf")

# For external HTML build
context = BuildContext(
    build_target="external",
    render_target="html",
    project_root="/path/to/project",
)

# Serialize for debugging
print(context.to_json())
```

---

### config.py — FilterConfig

The `FilterConfig` dataclass contains all configuration for the filter pipeline. All settings are deterministic (no randomness or time-dependent values).

```python
@dataclass(frozen=True)
class FilterConfig:
    # Visibility ordering (lower = more restricted)
    visibility_order: dict[str, int]

    # Forbidden policies per build target
    forbidden_policies: dict[BuildTarget, frozenset[str]]

    # Attributes to strip per build target
    strip_attrs_external: frozenset[str]
    strip_attrs_dossier: frozenset[str]

    # Protected attributes (never stripped)
    protected_attrs: frozenset[str]  # {id, role, kind, visibility, policies}

    # Presentation thresholds
    thresholds: PresentationThresholds

    # Appendix options
    appendix: AppendixOptions
```

**Default forbidden policies:**
| Target | Forbidden Tags |
|--------|----------------|
| internal | (none) |
| external | `internal-only`, `draft`, `wip` |
| dossier | `internal-only`, `draft`, `wip`, `verbose` |

**Default strip attributes:**
| Target | Stripped Keys |
|--------|---------------|
| internal | (none) |
| external | `producer`, `run_id`, `dataset_fingerprint`, `config_fingerprint`, `artifact_uri`, `sha256`, `source`, `schema` |
| dossier | All external keys + `lock`, `bind-to` |

**Presentation thresholds:**
```python
@dataclass(frozen=True)
class PresentationThresholds:
    pdf_code_max_lines: int = 50
    pdf_code_max_chars: int = 3000
    pdf_code_preview_lines: int = 5
    appendix_threshold_blocks: int = 5
    appendix_threshold_chars: int = 2000
    html_fold_threshold_blocks: int = 5
    html_fold_threshold_chars: int = 2000
```

**Usage:**
```python
from litepub_norm.filters import FilterConfig, PresentationThresholds

# Use defaults
config = FilterConfig()

# Custom thresholds
config = FilterConfig(
    thresholds=PresentationThresholds(
        pdf_code_max_lines=100,
        appendix_threshold_blocks=10,
    )
)
```

---

### report.py — FilterReport

The `FilterReport` tracks all actions taken during filter execution. It provides an audit trail for debugging and testing.

```python
@dataclass
class FilterReportEntry:
    semantic_id: str          # Affected wrapper ID
    action: str               # "removed", "stripped", "folded", "moved_to_appendix", etc.
    reason_code: str          # Stable code for testing (e.g., "VIS_REMOVED_INTERNAL_ONLY")
    message: str | None       # Human-readable description
    path: str | None          # AST path (e.g., "blocks[2]")
    details: dict | None      # Additional context

@dataclass
class FilterReport:
    entries: list[FilterReportEntry]
```

**Reason codes by filter:**

| Filter | Reason Codes |
|--------|--------------|
| Visibility | `VIS_REMOVED_INTERNAL_ONLY`, `VIS_REMOVED_EXTERNAL_ONLY` |
| Policy | `POL_REMOVED_TAG:<tag>` |
| Metadata | `META_STRIP_ATTRS` |
| Presentation (PDF) | `PRES_PDF_CODEBLOCK_EXTERNALIZED`, `PRES_PDF_MOVED_TO_APPENDIX` |
| Presentation (HTML) | `PRES_HTML_FOLDED`, `PRES_HTML_CODEBLOCK_FOLDED` |

**Usage:**
```python
# After filtering
ast, report = apply_filters(ast, config, context)

# Inspect report
print(f"Total actions: {len(report)}")

for entry in report.entries:
    print(f"[{entry.reason_code}] {entry.semantic_id}: {entry.message}")

# Filter by action type
removed = report.filter_by_action("removed")
print(f"Removed {len(removed)} wrappers")

# Serialize for logging
with open("filter_report.json", "w") as f:
    f.write(report.to_json())
```

---

### api.py — Pipeline API

The `api.py` module provides the main entry points for the filter pipeline.

#### `apply_filters()` — Full Pipeline

```python
def apply_filters(
    ast: dict[str, Any],
    config: FilterConfig | None = None,
    context: BuildContext | None = None,
) -> tuple[dict[str, Any], FilterReport]:
```

Applies all four filters in fixed order:
1. **Visibility** — removes wrappers not visible for build target
2. **Policy** — removes wrappers with forbidden policy tags
3. **Metadata strip** — removes provenance attributes
4. **Presentation** — transforms for PDF/HTML output

**Parameters:**
- `ast`: Resolved Pandoc AST (from resolution stage)
- `config`: Filter configuration (uses defaults if not provided)
- `context`: Build context (uses defaults if not provided)

**Returns:**
- Tuple of (filtered AST, merged report)

**Example:**
```python
from litepub_norm.filters import apply_filters, BuildContext, FilterConfig

# Basic usage with defaults
filtered_ast, report = apply_filters(resolved_ast)

# For external PDF build
context = BuildContext(build_target="external", render_target="pdf")
filtered_ast, report = apply_filters(resolved_ast, context=context)

# With custom config
config = FilterConfig(
    forbidden_policies={
        "internal": frozenset(),
        "external": frozenset({"draft", "wip", "internal-only", "confidential"}),
        "dossier": frozenset({"draft", "wip", "internal-only", "confidential", "verbose"}),
    }
)
filtered_ast, report = apply_filters(resolved_ast, config, context)
```

#### `apply_filter()` — Single Filter

```python
def apply_filter(
    ast: dict[str, Any],
    filter_name: str,
    config: FilterConfig | None = None,
    context: BuildContext | None = None,
) -> tuple[dict[str, Any], FilterReport]:
```

Applies a single named filter. Useful for testing or custom pipelines.

**Parameters:**
- `ast`: Pandoc AST
- `filter_name`: One of `"visibility"`, `"policy"`, `"metadata_strip"`, `"presentation"`
- `config`: Filter configuration
- `context`: Build context

**Example:**
```python
from litepub_norm.filters import apply_filter, BuildContext

context = BuildContext(build_target="external")

# Apply only visibility filter
ast, report = apply_filter(ast, "visibility", context=context)

# Then apply only metadata strip
ast, report2 = apply_filter(ast, "metadata_strip", context=context)
```

---

## Filter Details

### Filter 1: Visibility

Removes wrappers based on visibility level and build target.

**Visibility ordering:** `internal < external < dossier`

| Build Target | Allowed Visibility Levels |
|--------------|---------------------------|
| internal | all (internal, external, dossier) |
| external | external, dossier |
| dossier | dossier only |

### Filter 2: Policy

Removes wrappers tagged with forbidden policy labels.

Policies are read from:
- `policies` attribute (comma-separated)
- Div classes

### Filter 3: Metadata Strip

Strips provenance attributes from wrappers for external/dossier outputs.

**Protected attributes (never stripped):** `id`, `role`, `kind`, `visibility`, `policies`

### Filter 4: Presentation

Transforms AST for specific output formats.

**PDF transformations:**
- T1: Externalize long code blocks → stub + preview + link
- T2: Move long "additional" sections → Appendix with stub

**HTML transformations:**
- T3: Fold long "additional" sections (in-place, collapsed)
- T4: Fold long code blocks (in-place, collapsed)

---

## Complete Example

```python
from litepub_norm import resolve, load_registry
from litepub_norm.filters import (
    apply_filters,
    BuildContext,
    FilterConfig,
)

# Load resolved AST (from previous stages)
registry = load_registry("aarc_registry.json")
resolved_ast = resolve(normalized_ast, registry)

# Configure filter for external PDF
context = BuildContext(
    build_target="external",
    render_target="pdf",
    project_root="/path/to/project",
    artifact_base_url="https://example.com/artifacts",
)

# Apply all filters
filtered_ast, report = apply_filters(resolved_ast, context=context)

# Log what happened
print(f"Filter actions: {len(report)}")
for entry in report.entries:
    print(f"  [{entry.action}] {entry.semantic_id}: {entry.reason_code}")

# The filtered_ast is now ready for Pandoc rendering
```

---

## Testing

Comprehensive tests are in `test/test_filters.py`:

```bash
uv run pytest test/test_filters.py -v
```

Test categories:
- **Visibility tests**: Build target visibility rules
- **Policy tests**: Forbidden tag removal
- **Metadata tests**: Attribute stripping
- **Presentation tests**: PDF/HTML transformations
- **Pipeline tests**: Filter ordering and determinism
- **Utility tests**: Wrapper detection and manipulation

---

## Design Principles

1. **Deterministic**: Same input always produces same output (no randomness, no timestamps in logic)
2. **Monotonic**: Downstream targets only remove content, never add
3. **Auditable**: Every action recorded in FilterReport with stable reason codes
4. **Immutable input**: Filters never modify the input AST (deep copy first)
5. **No network I/O**: All operations are local; links reference stable paths
