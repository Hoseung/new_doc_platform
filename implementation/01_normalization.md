# Implementation Summary: AST Normalization (Phase 1)

## Overview

This document summarizes the normalization stage implementation for the documentation platform. The normalization pipeline transforms `.md` and `.rst` source files into a **Canonical Pandoc AST** with completed metadata from an analysis registry.

## Pipeline Flow

```
Source (.md/.rst)
      ↓
   Parse (Pandoc → JSON AST)
      ↓
   Adapt (format-specific → wrapper Div candidates)
      ↓
   Normalize (metadata completion, defaults, placeholders)
      ↓
Canonical AST (JSON)
```

## Module Structure

```
src/litepub_norm/
├── __init__.py          # Package exports
├── errors.py            # Custom exceptions
├── registry.py          # Semantic ID → metadata lookup
├── md_adapter.py        # Markdown HTML comment fence → Div
├── rst_adapter.py       # RST directive preprocessing
├── core_normalize.py    # Format-agnostic normalization
├── serialize.py         # Deterministic JSON output
└── harness.py           # Pipeline orchestration
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pandoc interface | `pypandoc` library | Simpler integration than subprocess |
| AST manipulation | Raw dict manipulation | Avoids hidden transforms from panflute |
| RST handling | Preprocess to HTML fences | Pandoc doesn't preserve custom directives |

## Key Components

### 1. Registry (`registry.py`)

Resolves semantic IDs to metadata:

```python
registry = Registry.from_file("registry.json")
metadata = registry.resolve("tbl.kpi.face.yaw_mae.v1")
# → {"role": "computed", "kind": "table", "source": "...", ...}
```

**Modes:**
- `strict=True`: Raises `UnknownSemanticIdError` for missing IDs
- `strict=False` (draft): Returns empty dict, allows iteration

### 2. Markdown Adapter (`md_adapter.py`)

Converts HTML comment fences to wrapper Divs:

```markdown
<!-- BEGIN tbl.kpi.face.yaw_mae.v1 -->
Caption text here.
<!-- END tbl.kpi.face.yaw_mae.v1 -->
```

**Challenges solved:**
- Pandoc may emit END fence as `RawInline` inside a `Para` (when no blank line before END)
- Solution: `_extract_end_fence_from_para()` splits Para and extracts the fence

**Constraints (v1):**
- Nested fences are disallowed → `FenceOverlapError`
- Mismatched BEGIN/END → `FenceMismatchError`

### 3. RST Adapter (`rst_adapter.py`)

Preprocesses RST directives before Pandoc parsing:

```rst
.. computed-table::
   :id: tbl.kpi.face.yaw_mae.v1

   Caption text.
```

Becomes:

```rst
.. raw:: html

   <!-- BEGIN tbl.kpi.face.yaw_mae.v1 -->

Caption text.

.. raw:: html

   <!-- END tbl.kpi.face.yaw_mae.v1 -->
```

This allows reuse of the MD adapter logic for fence processing.

### 4. Core Normalizer (`core_normalize.py`)

Format-agnostic transformations:

1. **Metadata completion**: Inject `role`, `kind`, `source`, `schema`, `visibility` from registry
2. **Default application**: `lock=true` for computed blocks
3. **Placeholder injection**: `[[COMPUTED:TABLE]]`, `[[COMPUTED:METRIC]]`, etc.
4. **Body cleanup**: Remove manually-authored payload from computed blocks

**Output Div structure:**
```json
{
  "t": "Div",
  "c": [
    ["semantic-id", [], [
      ["role", "computed"],
      ["kind", "table"],
      ["source", "analysis/metrics/yaw.json"],
      ["schema", "yaw_error_v1"],
      ["visibility", "internal"],
      ["lock", "true"]
    ]],
    [/* body blocks */]
  ]
}
```

### 5. Harness (`harness.py`)

Main entry points:

```python
from litepub_norm import normalize_file, normalize_text

# From file
ast = normalize_file("report.md", "registry.json")

# From text
ast = normalize_text(md_content, "markdown", registry)
```

## Error Handling

| Exception | Trigger |
|-----------|---------|
| `FenceMismatchError` | BEGIN/END IDs don't match, or unclosed fence |
| `FenceOverlapError` | Nested fences (disallowed in v1) |
| `UnknownSemanticIdError` | ID not in registry (strict mode) |
| `RegistryIncompleteError` | Missing required fields for computed block |
| `DuplicateIdError` | Same semantic ID appears multiple times |

## Test Coverage

```
test/
├── test_smoke_harness.py    # Basic pipeline tests
├── test_golden_md.py        # MD normalization golden tests
└── test_golden_rst.py       # RST normalization golden tests
```

**Golden test assertions:**
- Correct number of wrapper Divs with expected IDs
- Metadata completed from registry
- `lock=true` for computed blocks
- Placeholders injected
- Prose preserved
- No fence remnants in output

## Test Data

```
data/
├── golden_minimal.md              # MD test input
├── golden_minimal.rst             # RST test input
├── registry.json                  # Test registry
├── expected_normalized_md.json    # Expected MD output
└── expected_normalized_rst.json   # Expected RST output
```

## Usage Example

```python
from litepub_norm import normalize_file
from litepub_norm.serialize import serialize

# Normalize a markdown file
ast = normalize_file("docs/report.md", "registry/registry.json")

# Serialize to JSON
json_output = serialize(ast, indent=2)

# Or save directly
from litepub_norm.serialize import serialize_to_file
serialize_to_file(ast, "ast/report.normalized.json")
```

## Next Steps (Phase 2)

The normalization stage is complete. The following stages will be implemented next:

1. **Resolver**: Replace placeholders with actual computed content from analysis artifacts
2. **Validator**: Enforce AST invariants and contracts
3. **Filter**: Produce target-specific documents (internal/external/dossier)
4. **Renderer**: HTML/PDF output with theming

## References

- `spec/normalization_v1.md` - Normalization specification
- `spec/authoring_convention_md.md` - Markdown authoring conventions
- `spec/authoring_convention_rst.md` - RST authoring conventions
- `plan_normalization.md` - Original implementation plan
