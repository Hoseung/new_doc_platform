# Validation Stage Documentation

## Overview

The validation stage is a critical sub-phase within the resolution stage of the LitePub documentation pipeline. Its purpose is to ensure that computed artifacts (metrics, tables, figures) loaded from external sources conform to their declared schemas and meet safety requirements before being embedded into the document AST.

Validation sits between **loading** (reading payload files from disk) and **emission** (converting payloads to Pandoc AST nodes):

```
Load → Validate → Emit
```

There are two complementary validators:

1. **Payload Validators**: Validate analysis artifacts before emission
2. **Document AST Validator**: Validate the final resolved AST after placeholder replacement

## Role in the Pipeline

The full LitePub pipeline consists of four stages:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Normalization  │───▶│   Resolution    │───▶│ Transformation  │───▶│  Presentation   │
│                 │    │                 │    │                 │    │                 │
│ • Parse source  │    │ • Load payloads │    │ • Target-       │    │ • Pandoc output │
│ • Wrap computed │    │ • VALIDATE ◀────│    │   specific      │    │ • HTML, PDF,    │
│   blocks        │    │ • Emit AST      │    │   transforms    │    │   DOCX          │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

Validation ensures that:
1. **Data Integrity**: Payloads match their declared schemas
2. **Type Safety**: Field types are correct and values are within expected bounds
3. **Content Safety**: No dangerous or unexpected content escapes into the document
4. **Size Control**: Tables and other structures don't exceed configured limits

## Validation Philosophy

### Two Kinds of Strictness

- **Safety strict (always ON)**: Prevents injection/escape, non-determinism, and malformed structures that can corrupt rendering
- **Completeness strict (profile-based)**: Missing artifacts can be warnings in internal/draft but MUST fail in external/dossier

### Profiles

Profiles control severity and limits:

| Profile | Completeness | Safety | Limits |
|---------|--------------|--------|--------|
| `internal` | lenient | strict | high |
| `external` | strict | strict | tighter |
| `dossier` | strictest | strict | tightest, no raw |

---

## Implementation Architecture

### Validator Modules

```
src/litepub_norm/resolver/validators/
├── __init__.py              # Public API exports
├── metric_v1.py             # metric.json@v1
├── table_simple_v1.py       # table.simple.json@v1
├── table_pandoc_v1.py       # table.pandoc.json@v1
├── figure_v1.py             # figure.meta.json@v1
├── pandoc_walk.py           # Generic Pandoc AST walker
└── document.py              # Post-resolution document validator
```

### Error Model

All validation errors use a unified error type with stable codes:

```python
class ValidationError(ResolutionError):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,        # Stable code for tests (e.g., VAL_METRIC_VALUE_BOOL)
        semantic_id: str | None = None, # Artifact ID
        path: str | None = None,        # File path
        spec: str | None = None,        # Payload spec
        ast_path: str | None = None,    # Location in AST
        hint: str | None = None,        # How to fix
    )
```

Error codes follow the pattern `VAL_{SPEC}_{FIELD}_{ERROR}`:
- `VAL_METRIC_VALUE_BOOL` - Boolean used as metric value
- `VAL_TABLE_DTYPE_MISMATCH` - Cell value doesn't match declared dtype
- `VAL_PANDOC_RAWINLINE_FORBIDDEN` - Raw content in safe mode
- `VAL_DOC_UNRESOLVED_PLACEHOLDER` - Placeholder token not replaced

---

## Payload Validators

### 1. Metric Validator (`metric.json@v1`)

**Purpose**: Validates scalar computed values with labels and optional units.

**Required Fields**:

| Field | Type | Constraint |
|-------|------|------------|
| `label` | string | Non-empty, whitespace-only rejected |
| `value` | number | Must be finite (no NaN, no ±Infinity), **NOT bool** |

**Optional Fields**:

| Field | Type | Notes |
|-------|------|-------|
| `unit` | string | Can be empty string for dimensionless values |
| `format` | string | Format hint with `{value}` and `{unit}` tokens only |
| `lower_is_better` | boolean | Performance direction hint |
| `notes` | array[string] | Additional context |
| `meta` | object | Machine metadata (non-semantic) |

**Critical Validation: Bool-as-Number Bug**:

```python
# CRITICAL: Check bool BEFORE number, since bool is subclass of int
if isinstance(value, bool):
    raise ValidationError(
        "Metric.value must be a number, not a boolean",
        code="VAL_METRIC_VALUE_BOOL",
        ...
    )
```

**Format String Validation** (strict mode):
- Only `{value}` and `{unit}` tokens allowed
- Max length 200 characters
- No newlines

---

### 2. Simple Table Validator (`table.simple.json@v1`)

**Purpose**: Validates structured tabular data in a portable column-row format.

**Required Fields**:

| Field | Type | Constraint |
|-------|------|------------|
| `columns` | array[object] | Non-empty, unique keys |
| `rows` | array[object] | Keys must match column definitions |

**Column Schema**:

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `key` | string | Yes | Valid identifier: `^[a-zA-Z_][a-zA-Z0-9_]*$` |
| `label` | string | No | Human-readable header |
| `unit` | string | No | Unit of measurement |
| `dtype` | enum | No | One of: `"string"`, `"int"`, `"float"`, `"bool"` |

**Row/Column Key Policy**:

Two policies available via `strict_keys` parameter:

| Policy | Parameter | Behavior |
|--------|-----------|----------|
| **S (Strict rectangular)** | `strict_keys=True` | All rows must have all column keys |
| **P (Permissive)** | `strict_keys=False` | Missing keys allowed (treated as null) |

Extra keys (not in column definitions) are always rejected.

**Dtype Enforcement**:

When `dtype` is specified, values are validated:

```python
elif dtype == "int":
    # CRITICAL: Check bool BEFORE int (bool is subclass of int)
    if isinstance(value, bool):
        raise ValidationError(
            f"Table.rows[{row_idx}].{key}: expected int, got bool",
            code="VAL_TABLE_DTYPE_BOOL_AS_INT",
            ...
        )
```

| dtype | Accepts | Rejects |
|-------|---------|---------|
| `string` | str | int, float, bool |
| `int` | int | bool, float, str |
| `float` | int, float | bool, str, NaN, Inf |
| `bool` | bool | int, float, str |

**Size Limits** (configurable via `ResolutionLimits`):

| Limit | Default | Check |
|-------|---------|-------|
| `max_table_cols` | 100 | `len(columns) > limit` |
| `max_table_rows` | 10000 | `len(rows) > limit` |
| `max_table_cells` | 200000 | `len(columns) * len(rows) > limit` |

---

### 3. Pandoc Table Validator (`table.pandoc.json@v1`)

**Purpose**: Validates native Pandoc Table AST blocks with safety checks.

**Structure Validation**:

A Pandoc Table has the following structure:
```
{"t": "Table", "c": [Attr, Caption, ColSpecs, TableHead, [TableBody], TableFoot]}
```

**Generic Pandoc Walker**:

The validator uses a generic AST walker (`pandoc_walk.py`) that ensures **complete traversal**—no content can bypass validation by being nested in untraversed nodes.

```python
def walk_pandoc(
    node: Any,
    callback: Callable[[Any, WalkContext], None],
    semantic_id: str,
    *,
    context: NodeContext = NodeContext.BLOCK,
    path: str = "",
    depth: int = 0,
) -> None:
```

The walker traverses:
- All block types (Para, Plain, BulletList, OrderedList, DefinitionList, BlockQuote, etc.)
- All inline types (Str, Emph, Strong, Link, Image, Span, etc.)
- Table structures (TableHead, TableBody, TableFoot, Row, Cell)

**Content Safety Policy**:

| Type | Default | With `allow_raw_pandoc=True` |
|------|---------|------------------------------|
| `RawInline` | ❌ Forbidden | ✅ Allowed |
| `RawBlock` | ❌ Forbidden | ✅ Allowed |
| `Div` | ❌ **Always forbidden** | ❌ **Always forbidden** |

**Allowed Inline Types** (safe mode):
```
Str, Space, SoftBreak, LineBreak, Emph, Underline, Strong, Strikeout,
Superscript, Subscript, SmallCaps, Code, Math, Link, Image, Span, Quoted, Cite, Note
```

**Allowed Block Types** (in cells):
```
Plain, Para, CodeBlock, BlockQuote, BulletList, OrderedList,
DefinitionList, Header, HorizontalRule, LineBlock
```

**Geometry Validation**:

| Check | Error Code |
|-------|------------|
| RowSpan ≥ 1 | `VAL_PANDOC_ROWSPAN_INVALID` |
| ColSpan ≥ 1 | `VAL_PANDOC_COLSPAN_INVALID` |
| ColSpan doesn't exceed table width | `VAL_PANDOC_COLSPAN_OVERFLOW` |

**Test: Hidden RawInline Detection**:

```python
def test_raw_inline_in_bullet_list_detected(self):
    """RawInline buried in BulletList inside cell is detected and rejected."""
    bullet_list = {
        "t": "BulletList",
        "c": [
            [{"t": "Plain", "c": [{"t": "RawInline", "c": ["html", "<b>hidden</b>"]}]}]
        ],
    }
    table = self._make_simple_table([[bullet_list]])
    config = ResolutionConfig(allow_raw_pandoc=False)
    with pytest.raises(ValidationError) as exc_info:
        validate_table_pandoc_v1(table, "test.table", config)
    assert "RAWINLINE" in exc_info.value.code
```

---

### 4. Figure Metadata Validator (`figure.meta.json@v1`)

**Purpose**: Validates optional metadata sidecar files for binary figures.

**Note**: The binary image itself is not validated (only hash-verified). Validation applies to the `.meta.json` sidecar.

**Optional Fields**:

| Field | Type | Notes |
|-------|------|-------|
| `caption` | string | Figure caption |
| `alt` | string | Accessibility text |
| `notes` | array[string] | Additional notes |
| `meta` | object | Machine metadata |

**Behavior for Missing Sidecar**:
```python
def validate_figure_meta_v1(payload: dict[str, Any] | None, semantic_id: str) -> None:
    if payload is None:
        return  # No sidecar is valid
```

---

## Document AST Validator (Post-Resolution)

**Purpose**: Validates invariants that must hold after resolution is complete.

**Location**: `src/litepub_norm/resolver/validators/document.py`

### Checks

| Check | Error Code | Description |
|-------|------------|-------------|
| Placeholder elimination | `VAL_DOC_UNRESOLVED_PLACEHOLDER` | No `[[COMPUTED:*]]` tokens remain |
| Unique semantic IDs | `VAL_DOC_DUPLICATE_ID` | Each wrapper has unique ID |
| Wrapper discipline | `VAL_DOC_MISSING_KIND` | Computed wrappers have `kind` attribute |
| Visibility policy | `VAL_DOC_VISIBILITY_VIOLATION` | Internal content not in external builds |
| Raw content | `VAL_DOC_RAWBLOCK_FORBIDDEN` | No raw content when disallowed |

### Usage

```python
from litepub_norm.resolver.validators import validate_resolved_document

result = validate_resolved_document(
    ast,
    config,
    check_placeholders=True,
    check_wrappers=True,
    check_raw_content=True,
    check_visibility=True,
    fail_fast=True,  # Raise on first error
)

if not result.valid:
    for error in result.errors:
        print(f"[{error.code}] {error}")
```

---

## Safety Considerations

### Why Content Safety Matters

Documents in LitePub are built from multiple sources:
1. Authored content (trusted)
2. Computed artifacts from analysis pipelines (semi-trusted)
3. External references (untrusted)

The validation stage is a **security boundary** that prevents malicious or buggy payloads from:

- Injecting arbitrary HTML via `RawInline`/`RawBlock`
- Creating XSS attacks in web-rendered documents
- Embedding malicious LaTeX commands in PDF output
- Consuming excessive resources via oversized tables

### Defense in Depth

| Layer | Protection |
|-------|------------|
| **Hash Verification** | Payload hasn't been modified (integrity) |
| **Schema Validation** | Payload matches declared structure (correctness) |
| **Content Safety** | Payload doesn't contain dangerous elements (security) |
| **Size Limits** | Payload doesn't exhaust resources (availability) |
| **Document Validation** | Final AST meets all invariants (completeness) |

---

## Testing Validation

Comprehensive tests are in `test/test_validators.py`:

```python
class TestMetricValidator:
    def test_value_bool_fails(self):
        """value=True fails (bool-as-number bug)."""
        payload = {"label": "Test", "value": True}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_VALUE_BOOL"

class TestPandocTableValidator:
    def test_raw_inline_in_bullet_list_detected(self):
        """RawInline buried in BulletList inside cell is detected and rejected."""
        # Tests that the generic walker finds hidden content
        ...

class TestDocumentValidator:
    def test_leftover_placeholder_fails(self):
        """Leftover placeholder fails."""
        ...
```

---

## Configuration Reference

Validation behavior is controlled by `ResolutionConfig`:

```python
@dataclass(frozen=True)
class ResolutionConfig:
    target: BuildTarget = "internal"
    strict: bool = True               # Fail on validation errors
    allow_raw_pandoc: bool = False    # Allow RawBlock/RawInline
    limits: ResolutionLimits = ...    # Size limits for tables
```

```python
@dataclass(frozen=True)
class ResolutionLimits:
    max_table_cells: int = 200_000
    max_table_rows: int = 10_000
    max_table_cols: int = 100
    max_text_len: int = 5_000_000
    max_image_bytes: int = 50_000_000
```

---

## Summary

The validation stage provides critical safety layers:

1. **Type Checking**: Ensures payloads have correct field types (including bool-as-number detection)
2. **Value Validation**: Catches invalid values (NaN, missing required fields)
3. **Dtype Enforcement**: Validates cell values match declared column types
4. **Safety Enforcement**: Blocks dangerous content (RawBlock, RawInline, Div)
5. **Geometry Validation**: Validates table cell spanning
6. **Resource Protection**: Size limits prevent oversized artifacts
7. **Document Invariants**: Post-resolution validation ensures no placeholders remain

Without validation, the pipeline would blindly embed any content from artifact files, creating security vulnerabilities and potential runtime errors in downstream stages.
