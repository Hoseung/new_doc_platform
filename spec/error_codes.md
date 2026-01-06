# Error Code Registry

This document provides a consolidated registry of all error codes used across the documentation pipeline. Error codes are stable identifiers that can be used in tests, monitoring, and debugging.

---

## Code Format

Error codes follow the pattern `{STAGE}_{CATEGORY}_{ERROR}`:

- **Stage prefix**: Identifies which pipeline stage generates the error
- **Category**: Groups related errors
- **Error**: Specific error condition

---

## 1. Normalization Errors (`NORM_*`)

Errors during AST normalization (adapter and core normalization).

| Code | Description | Severity |
|------|-------------|----------|
| `NORM_FENCE_UNMATCHED` | BEGIN without matching END, or vice versa | MUST |
| `NORM_FENCE_OVERLAP` | Overlapping semantic block fences | MUST |
| `NORM_FENCE_NESTED` | Nested BEGIN inside open region (v1 disallowed) | MUST |
| `NORM_ID_UNKNOWN` | Semantic ID not found in registry (strict mode) | MUST/SHOULD |
| `NORM_ID_DUPLICATE` | Duplicate semantic ID in document | MUST |
| `NORM_REGISTRY_INCOMPLETE` | Required registry fields missing for computed block | MUST |

---

## 2. Resolution Errors (`RES_*`)

Errors during placeholder resolution.

| Code | Description | Severity |
|------|-------------|----------|
| `RES_ARTIFACT_NOT_FOUND` | Referenced artifact file does not exist | MUST |
| `RES_ARTIFACT_HASH_MISMATCH` | Artifact SHA256 doesn't match registry | MUST |
| `RES_PAYLOAD_PARSE_ERROR` | Artifact JSON is malformed | MUST |
| `RES_SCHEMA_MISMATCH` | Payload doesn't match declared schema | MUST |
| `RES_PLACEHOLDER_MISSING` | Computed block has no placeholder token | MUST |

---

## 3. Validation Errors (`VAL_*`)

Errors during payload and document validation. Organized by payload type.

### 3.1 Metric Validation (`VAL_METRIC_*`)

| Code | Description | Severity |
|------|-------------|----------|
| `VAL_METRIC_NOT_OBJECT` | Payload is not a JSON object | MUST |
| `VAL_METRIC_LABEL_TYPE` | Label is not a string | MUST |
| `VAL_METRIC_LABEL_EMPTY` | Label is empty string | MUST |
| `VAL_METRIC_VALUE_TYPE` | Value is not a number | MUST |
| `VAL_METRIC_VALUE_BOOL` | Value is boolean (bool-as-number bug) | MUST |
| `VAL_METRIC_VALUE_NONFINITE` | Value is NaN or Infinity | MUST |
| `VAL_METRIC_UNIT_TYPE` | Unit is not a string | MUST |
| `VAL_METRIC_FORMAT_TYPE` | Format is not a string | MUST |
| `VAL_METRIC_FORMAT_TOO_LONG` | Format exceeds max length | MUST |
| `VAL_METRIC_FORMAT_INVALID_TOKEN` | Format contains invalid token | MUST |
| `VAL_METRIC_FORMAT_NEWLINE` | Format contains newline | MUST |
| `VAL_METRIC_LOWER_IS_BETTER_TYPE` | lower_is_better is not boolean | MUST |
| `VAL_METRIC_NOTES_TYPE` | Notes is not an array | MUST |
| `VAL_METRIC_NOTES_ITEM_TYPE` | Notes item is not a string | MUST |
| `VAL_METRIC_META_TYPE` | Meta is not an object | MUST |

### 3.2 Simple Table Validation (`VAL_TABLE_*`)

| Code | Description | Severity |
|------|-------------|----------|
| `VAL_TABLE_NOT_OBJECT` | Payload is not a JSON object | MUST |
| `VAL_TABLE_COLUMNS_TYPE` | Columns is not an array | MUST |
| `VAL_TABLE_COLUMNS_EMPTY` | Columns array is empty | MUST |
| `VAL_TABLE_COLUMN_TYPE` | Column is not an object | MUST |
| `VAL_TABLE_COLUMN_KEY_TYPE` | Column key is not a string | MUST |
| `VAL_TABLE_COLUMN_KEY_EMPTY` | Column key is empty string | MUST |
| `VAL_TABLE_COLUMN_KEY_INVALID` | Column key has invalid characters | MUST |
| `VAL_TABLE_COLUMN_KEY_DUPLICATE` | Duplicate column key | MUST |
| `VAL_TABLE_COLUMN_LABEL_TYPE` | Column label is not a string | MUST |
| `VAL_TABLE_COLUMN_UNIT_TYPE` | Column unit is not a string | MUST |
| `VAL_TABLE_COLUMN_DTYPE_INVALID` | Invalid dtype value | MUST |
| `VAL_TABLE_ROWS_TYPE` | Rows is not an array | MUST |
| `VAL_TABLE_ROW_TYPE` | Row is not an object | MUST |
| `VAL_TABLE_ROW_EXTRA_KEYS` | Row has keys not in columns | MUST |
| `VAL_TABLE_ROW_MISSING_KEYS` | Row missing required column keys | MUST |
| `VAL_TABLE_CELL_TYPE` | Cell value has wrong type | MUST |
| `VAL_TABLE_DTYPE_MISMATCH` | Cell value doesn't match dtype | MUST |
| `VAL_TABLE_DTYPE_BOOL_AS_INT` | Boolean used where int expected | MUST |
| `VAL_TABLE_DTYPE_BOOL_AS_FLOAT` | Boolean used where float expected | MUST |
| `VAL_TABLE_DTYPE_FLOAT_NONFINITE` | Float cell is NaN or Infinity | MUST |
| `VAL_TABLE_EXCEEDS_MAX_ROWS` | Exceeds max row count | MUST |
| `VAL_TABLE_EXCEEDS_MAX_COLS` | Exceeds max column count | MUST |
| `VAL_TABLE_EXCEEDS_MAX_CELLS` | Exceeds max cell count | MUST |
| `VAL_TABLE_CAPTION_TYPE` | Caption is not a string | MUST |
| `VAL_TABLE_NOTES_TYPE` | Notes is not an array | MUST |
| `VAL_TABLE_NOTES_ITEM_TYPE` | Notes item is not a string | MUST |
| `VAL_TABLE_META_TYPE` | Meta is not an object | MUST |

### 3.3 Pandoc Table Validation (`VAL_PANDOC_*`)

| Code | Description | Severity |
|------|-------------|----------|
| `VAL_PANDOC_NOT_OBJECT` | Payload is not a JSON object | MUST |
| `VAL_PANDOC_NOT_TABLE` | Node is not a Table type | MUST |
| `VAL_PANDOC_TABLE_STRUCTURE` | Table has wrong structure | MUST |
| `VAL_PANDOC_COLSPECS_TYPE` | ColSpecs is not an array | MUST |
| `VAL_PANDOC_NO_COLUMNS` | Table has no columns | MUST |
| `VAL_PANDOC_BODIES_TYPE` | Bodies is not an array | MUST |
| `VAL_PANDOC_ROWSPAN_INVALID` | RowSpan < 1 | MUST |
| `VAL_PANDOC_COLSPAN_INVALID` | ColSpan < 1 | MUST |
| `VAL_PANDOC_COLSPAN_OVERFLOW` | ColSpan exceeds table width | MUST |
| `VAL_PANDOC_EXCEEDS_MAX_ROWS` | Exceeds max row count | MUST |
| `VAL_PANDOC_EXCEEDS_MAX_COLS` | Exceeds max column count | MUST |
| `VAL_PANDOC_EXCEEDS_MAX_CELLS` | Exceeds max cell count | MUST |
| `VAL_PANDOC_RAWBLOCK_FORBIDDEN` | RawBlock in safe mode | MUST |
| `VAL_PANDOC_RAWINLINE_FORBIDDEN` | RawInline in safe mode | MUST |
| `VAL_PANDOC_BLOCK_NOT_ALLOWED` | Block type not in allowlist | MUST |
| `VAL_PANDOC_INLINE_NOT_ALLOWED` | Inline type not in allowlist | MUST |
| `VAL_PANDOC_TOO_DEEP` | AST exceeds max nesting depth | MUST |

### 3.4 Figure Validation (`VAL_FIGURE_*`)

| Code | Description | Severity |
|------|-------------|----------|
| `VAL_FIGURE_NOT_OBJECT` | Payload is not a JSON object | MUST |
| `VAL_FIGURE_CAPTION_TYPE` | Caption is not a string | MUST |
| `VAL_FIGURE_ALT_TYPE` | Alt text is not a string | MUST |
| `VAL_FIGURE_NOTES_TYPE` | Notes is not an array | MUST |
| `VAL_FIGURE_NOTES_ITEM_TYPE` | Notes item is not a string | MUST |
| `VAL_FIGURE_META_TYPE` | Meta is not an object | MUST |

### 3.5 Document Validation (`VAL_DOC_*`)

| Code | Description | Severity |
|------|-------------|----------|
| `VAL_DOC_NO_BLOCKS` | Document has no content blocks | MUST |
| `VAL_DOC_DUPLICATE_ID` | Duplicate semantic ID in document | MUST |
| `VAL_DOC_MISSING_KIND` | Computed wrapper missing `kind` attribute | MUST |
| `VAL_DOC_UNRESOLVED_PLACEHOLDER` | Placeholder token not replaced | MUST |
| `VAL_DOC_RAWBLOCK_FORBIDDEN` | RawBlock forbidden for target | MUST |
| `VAL_DOC_RAWINLINE_FORBIDDEN` | RawInline forbidden for target | MUST |
| `VAL_DOC_VISIBILITY_VIOLATION` | Internal content in external build | MUST |
| `VAL_DOC_WRAPPER_STRUCTURE` | Invalid wrapper Div structure | MUST |
| `VAL_DOC_WRAPPER_EMPTY` | Empty wrapper Div | MUST |
| `VAL_DOC_WRAPPER_INVALID_PRIMARY` | Invalid primary content type | MUST |
| `VAL_DOC_WRAPPER_KIND_MISMATCH` | Content doesn't match kind | MUST |

---

## 4. Filter Report Codes

These are not errors but report codes documenting filter actions.

### 4.1 Visibility Filter (`VIS_*`)

| Code | Description | Action |
|------|-------------|--------|
| `VIS_REMOVED_INTERNAL_ONLY` | Removed internal-only block from external/dossier | removed |
| `VIS_REMOVED_EXTERNAL_ONLY` | Removed external-only block from dossier | removed |

### 4.2 Policy Filter (`POL_*`)

| Code | Description | Action |
|------|-------------|--------|
| `POL_REMOVED_TAG:<tag>` | Removed block with forbidden policy tag | removed |

### 4.3 Metadata Strip Filter (`META_*`)

| Code | Description | Action |
|------|-------------|--------|
| `META_STRIP_ATTRS` | Stripped provenance attributes from wrapper | stripped |
| `META_STRIP_ATTR:<key>` | Stripped specific attribute (alternative format) | stripped |
| `META_REDACT_ATTR:<key>` | Redacted rather than removed attribute | redacted |

### 4.4 Presentation Filter (`PRES_*`)

| Code | Description | Action |
|------|-------------|--------|
| `PRES_PDF_CODEBLOCK_EXTERNALIZED` | Replaced long code with external link | transformed |
| `PRES_PDF_MOVED_TO_APPENDIX` | Moved additional content to appendix | transformed |
| `PRES_HTML_FOLDED` | Wrapped additional content as foldable | transformed |
| `PRES_HTML_CODEBLOCK_FOLDED` | Wrapped long code as foldable | transformed |

---

## 5. Severity Levels

| Level | Meaning |
|-------|---------|
| **MUST** | Build fails immediately. No workaround. |
| **SHOULD** | Warning by default; configurable as failure for external/dossier targets. |

---

## 6. Implementation Reference

For error handling implementation details, see:

- **[implementation/03_validation.md](../implementation/03_validation.md)** — Validation error model and implementation
- **[implementation/04_filtering.md](../implementation/04_filtering.md)** — Filter report model and implementation
