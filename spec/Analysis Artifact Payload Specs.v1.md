# Analysis Artifact Payload Specs — v1 (Spec Pack)

## 0. Purpose

These specs define **payload formats** emitted by the analysis pipeline and consumed by the documentation platform resolver.

They are **type-level** contracts (a small set), not per-artifact templates.

Each registry entry includes:

- `format`: concrete encoding label (e.g., `table.simple.json`)
- `spec`: versioned payload spec ID (e.g., `table.simple.json@v1`)
- `uri`: location of the payload
- `sha256`: integrity of payload bytes

---

## 1. Common requirements (all payloads)

### 1.1 Encoding

- All JSON payloads MUST be valid JSON and encoded in **UTF-8**.
- JSON strings MUST be valid Unicode.
- Producers SHOULD normalize human text to **Unicode NFC** for stability across tools and platforms.
- Newlines SHOULD be `\n`.

### 1.2 Determinism

- Payload content MUST be reproducible from the analysis inputs declared by the pipeline.
- No randomized ordering unless explicitly stabilized (e.g., sorting keys/rows deterministically).

### 1.3 Safety policy (applies when payload contains Pandoc content)

If a payload includes Pandoc blocks/inlines (e.g., `table.pandoc.json@v1`):

- Raw content (`RawInline`, `RawBlock`) MUST NOT appear unless the build profile explicitly enables it.
- Embedded `Div` IDs MUST NOT be present (semantic IDs belong to document wrappers, not payloads).

---

## 2. `metric.json@v1`

### 2.1 Intent

Represents a computed scalar (or single numeric value) with a human-readable label and optional unit/notes.

### 2.2 File naming

- Recommended: `metrics/<semantic_id>.json` or any deterministic naming convention.

### 2.3 Payload schema (normative)

A payload MUST be a JSON object with:

### Required

- `label` (string, non-empty)
- `value` (number)

### Optional

- `unit` (string)
- `lower_is_better` (boolean)
- `notes` (array of strings)
- `format` (string): formatting hint for rendering only (non-semantic)
- `meta` (object): freeform machine metadata (non-semantic)

### 2.4 Example (valid)

```json
{
  "label": "Face yaw MAE",
  "value": 3.72,
  "unit": "deg",
  "lower_is_better": true,
  "format": "{value:.2f} {unit}",
  "notes": ["N=12345", "filtered: occlusion<0.2"],
  "meta": {
    "population": "front_ir_night",
    "aggregation": "mean_abs"
  }
}

```

### 2.5 Resolver validation (required)

- `label` exists and is a string with length ≥ 1
- `value` is a finite JSON number (no NaN/Inf; JSON cannot encode these anyway)
- If present:
    - `notes` is array of strings
    - `meta` is an object
    - `lower_is_better` is boolean

### 2.6 Resolution output (informative)

Resolver injects a canonical AST representation, typically:

- a small table (Label | Value) or
- a paragraph with emphasized label and code-styled value
    
    (implementation choice; must be deterministic).
    

---

## 3. `table.simple.json@v1`

### 3.1 Intent

A rectangular table (no merged cells) with explicit columns and row data.

### 3.2 Payload schema (normative)

A payload MUST be a JSON object with:

### Required

- `columns` (non-empty array)
- `rows` (array)

### Optional

- `caption` (string)
- `notes` (array of strings)
- `meta` (object)

Each `columns[i]` MUST be an object with:

- Required:
    - `key` (string identifier)
- Optional:
    - `label` (string)
    - `unit` (string)
    - `dtype` (one of `string|int|float|bool`)

Each `rows[j]` MUST be an object mapping column keys to values.

Allowed cell value types:

- `string | number | boolean | null`

### 3.3 Example (valid)

```json
{
  "caption": "Mean Absolute Error of face yaw estimation across yaw angles.",
  "columns": [
    {"key": "yaw_deg", "label": "Yaw (deg)", "unit": "deg", "dtype": "int"},
    {"key": "mae_deg", "label": "MAE (deg)", "unit": "deg", "dtype": "float"}
  ],
  "rows": [
    {"yaw_deg": -60, "mae_deg": 4.2},
    {"yaw_deg": -45, "mae_deg": 3.6},
    {"yaw_deg": -30, "mae_deg": 3.1}
  ],
  "notes": ["N=12345", "filter: occlusion<0.2"]
}

```

### 3.4 Resolver validation (required)

Structural:

- `columns` exists and has ≥ 1 item
- each column has a `key` string, and keys are unique
- `rows` exists and is an array

Cross-field invariants (in code, not just JSON schema):

- **Row key set must match columns**:
    - Strict mode: `set(row.keys()) == set(column_keys)`
    - Permissive internal mode: missing keys are treated as `null`, extra keys forbidden (recommended)
- Type checks:
    - If `dtype` present:
        - `int` ⇒ value is integer number (or null)
        - `float` ⇒ value is number (or null)
        - `bool` ⇒ boolean (or null)
        - `string` ⇒ string (or null)

Safety:

- Total size limits enforced by build profile (max rows/cols/cells/text length)

### 3.5 Resolution output (informative)

Resolver converts payload into a canonical Pandoc `Table` block with:

- header row derived from `columns[*].label` or `key`
- body rows derived from `rows`
- caption if provided

---

## 4. `table.pandoc.json@v1`

### 4.1 Intent

A rich table supporting merged cells, hierarchical headers, and any layout expressible as a Pandoc `Table` node.

This is the “escape hatch” for complex tables without inventing a bespoke spec.

### 4.2 Payload shape (normative)

The payload file MUST encode **exactly one** Pandoc `Table` block as JSON.

Two allowed representations (choose one for your implementation):

### Option A (recommended): “Pandoc JSON fragment”

A JSON object that is a single Pandoc block:

- `{"t": "Table", "c": ... }`

### Option B: “Wrapper object”

```json
{
  "pandoc_version": "3.x",
  "block": { "t": "Table", "c": ... }
}

```

Pick **one** representation and standardize it. (Option A is simplest.)

### 4.3 What is allowed inside the table (policy)

By default (safe mode):

- Allow common inline content: `Str`, `Space`, `Emph`, `Strong`, `Code`, `Link`, `LineBreak`, etc.
- Disallow:
    - `RawInline`, `RawBlock`
    - nested wrapper `Div` blocks
    - placeholder tokens like `[[COMPUTED:...]]`

Internal mode may allow more, but do it explicitly.

### 4.4 Resolver validation (required)

- Payload parses as JSON
- Payload is a single Pandoc `Table` block
- Table geometry invariants must hold:
    - spans are positive
    - spans don’t exceed bounds
    - no overlapping merged regions
    - (optional) no holes in the grid
- Content safety policy enforced for build target
- Size limits enforced (rows/cols/cells)

### 4.5 Resolution output

Resolver injects the `Table` block as-is (after normalization/safety checks), preserving structure like merged cells.

---

## 5. `figure.binary@v1`

### 5.1 Intent

A computed figure stored as a binary or vector image file, referenced by the registry.

### 5.2 Allowed formats (normative)

Allowed figure file formats MUST be a configured set, typically:

- `image.png`
- `image.jpg`
- `image.webp`
- `image.svg`
- `image.pdf` (only if your renderers support it)

### 5.3 Resolver validation (required)

- File exists at `uri`
- Hash matches `sha256`
- File extension/declared format is allowed for this build profile
- Size limits may apply (max bytes)

### 5.4 Resolution output

Resolver injects a canonical image node (Pandoc `Image`/`Figure` style), with caption/alt from sidecar if provided.

---

## 6. `figure.meta.json@v1` (optional sidecar)

### 6.1 Intent

Provides human-facing metadata for a figure without changing the computed pixels/vectors.

### 6.2 Payload schema (normative)

JSON object with:

### Optional

- `caption` (string)
- `alt` (string)
- `notes` (array of strings)
- `meta` (object) — non-semantic machine metadata

Example:

```json
{
  "caption": "Confusion matrix under front occlusion.",
  "alt": "Heatmap confusion matrix for yaw bins.",
  "notes": ["Front camera, IR, night condition"],
  "meta": {"colormap": "viridis"}
}

```

### 6.3 Resolver validation (required)

- If present:
    - `caption` is string
    - `alt` is string
    - `notes` is array of strings
    - `meta` is object

---

## 7. Spec identifiers and compatibility

### 7.1 Spec ID format

`<format>@v<major>`

Examples:

- `metric.json@v1`
- `table.simple.json@v1`
- `table.pandoc.json@v1`
- `figure.binary@v1`
- `figure.meta.json@v1`

### 7.2 Breaking changes

Any breaking change requires bumping the major version:

- `@v2`, etc.