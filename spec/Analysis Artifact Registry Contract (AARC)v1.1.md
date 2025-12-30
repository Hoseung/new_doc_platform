# Analysis Artifact Registry Contract (AARC) — v1.1

---

## 1. Purpose

This contract defines the interface between:

- **Analysis pipeline** (produces computed artifacts), and
- **Documentation platform** (resolves semantic IDs into canonical Pandoc AST).

The registry is a **symbol table** mapping a **semantic ID** (e.g., `tbl.kpi.face.yaw_mae.v1`) to:

1. **artifact location** (URI/path),
2. **integrity** (hash),
3. **payload spec** (type-level contract), and
4. **provenance** sufficient to trace how/where it was produced.

The registry must contain **just enough** to make resolution **deterministic, auditable, and reproducible**, without embedding presentation concerns.

---

## 2. Design principles

### 2.1 Determinism

Given the same:

- registry snapshot
- artifact store (artifact_root)
- document AST (semantic IDs)

Resolution must produce the same resolved AST (modulo intended normalization).

### 2.2 Pipeline reality: graphs, not single “test cases”

Artifacts may summarize multiple runs/conditions/datasets.

Therefore, per-entry provenance must not force fake singular attribution (e.g., one `test_case_id`).

### 2.3 Type-level specs only

The contract uses a **small set** of versioned payload specs (e.g., `metric.json@v1`).

**Do not** create bespoke schema files per semantic ID.

---

## 3. Registry format and encoding

### 3.1 File format

- Registry MUST be JSON.
- Registry MAY be one file or multiple files, but the build must reference **one registry snapshot**.

### 3.2 Text encoding and multilingual support (Korean included)

- JSON text MUST be valid Unicode.
- In practice, JSON files MUST be encoded as **UTF-8** (this is the internet standard and fully supports Korean).
- To avoid “looks identical but differs bytewise” issues, producers SHOULD normalize strings to **Unicode NFC** (recommended) and avoid control characters.

> If you’re worried about Korean: UTF-8 is not a limitation—UTF-8 is the standard Unicode encoding and represents Hangul perfectly. The real foot-gun is inconsistent normalization (NFC vs NFD) and inconsistent newline handling.
> 

---

## 4. Registry top-level schema

```json
{
"registry_version":"aarc-1.1",
"generated_at":"2025-12-30T12:03:11Z",
"artifact_root":"artifacts/run_2025-12-30/",
"run":{ ...},
"entries":[ ...]
}
```

### Required fields

- `registry_version` (string): must be `aarc-1.1`
- `generated_at` (RFC3339 string)
- `artifact_root` (string): base for resolving relative `uri`s (can be local path or remote prefix)
- `run` (object): run-level provenance
- `entries` (array): artifact entries

---

## 5. Run-level provenance (`run`) — required

Run provenance answers: **“What execution produced this snapshot?”**

```json
{
"run_id":"run_2025-12-30T12-03-11Z_abc123",
"test_id":"EuroNCAP_DMS_2026_YAW_ANGLE_SWEEP",
"pipeline":{"name":"dms-eval-pipeline","version":"0.8.4"},
"code":{
"repo":"git@company:icms/eval.git",
"commit":"abc123def456",
"dirty":false
},
"inputs":{
"dataset_id":"ds_2025-12-15_front_ir_v3",
"dataset_fingerprint":"sha256:....",
"config_fingerprint":"sha256:...."
}
}

```

### Required fields

- `run_id` (string): unique per pipeline execution
- `test_id` (string): external identity of the evaluation/test set (your “test ID” anchor)
- `pipeline.name`, `pipeline.version`
- `code.commit`, `code.dirty`
- `inputs.dataset_fingerprint`, `inputs.config_fingerprint`

### Optional fields

- `code.repo`
- `inputs.dataset_id`
- additional fields under `inputs` (allowed)

---

## 6. Entry model (`entries[]`)

Each entry maps **one semantic ID** to **one artifact payload**.

```json
{
"id":"tbl.kpi.face.yaw_mae.v1",
"artifact_type":"table",
"format":"table.simple.json",
"spec":"table.simple.json@v1",
"uri":"tables/yaw_mae.json",
"sha256":"sha256:....",
"origin":{ ...},
"related":[ ...],
"meta":{ ...}
}

```

### 6.1 Required fields

- `id` (string): semantic ID
- `artifact_type` (enum): `"table" | "metric" | "figure"`
- `format` (string): concrete payload format identifier (see §7)
- `spec` (string): versioned payload spec (type-level contract)
- `uri` (string): payload location (relative to `artifact_root` unless absolute URI)
- `sha256` (string): checksum of the payload file bytes
- `origin.producer` (string): the final producing script/module/component

### 6.2 Optional fields

- `origin` (object): see below (producer required; other fields optional)
- `related` (array): links to inputs/lineage (recommended for aggregates)
- `meta` (object): extra machine-readable metadata (must not be required by resolver)

---

## 7. Payload specs and formats

### 7.1 Tables (two-tier)

### A) Simple rectangular table

Use when you don’t need merged cells.

- `artifact_type`: `"table"`
- `format`: `"table.simple.json"`
- `spec`: `"table.simple.json@v1"`
- `uri`: points to JSON

**Contract (high-level)**

- `columns[]` define keys and optional labels/units/dtypes
- `rows[]` is a list of row objects mapping column keys to primitive values
- Resolver validates:
    - column keys are unique
    - every row matches the column key set (strictness configurable)
    - dtype hints (if provided) are respected

### B) Rich table (merged cells / hierarchical headers / complex layout)

Use when you need partial merged cells or any Pandoc-table-expressible structure.

- `artifact_type`: `"table"`
- `format`: `"table.pandoc.json"`
- `spec`: `"table.pandoc.json@v1"`
- `uri`: points to JSON

**Contract (high-level)**

- The JSON file MUST represent **exactly one Pandoc `Table` block** (not an entire document).
- Wrapper `Div` and semantic ID live in the document AST, not inside the payload.
- Resolver validates:
    - payload parses as a single `Table` block
    - table geometry is coherent (no invalid/overlapping spans)
    - content safety policy (e.g., forbid raw HTML/LaTeX blocks unless enabled)

> This format is your “escape hatch” that still stays canonical: it’s literally a Pandoc Table node.
> 

---

### 7.2 Metrics

- `artifact_type`: `"metric"`
- `format`: `"metric.json"`
- `spec`: `"metric.json@v1"`
- `uri`: JSON payload

**Contract (high-level)**

- Must contain numeric `value` and a human label.
- Optional unit, notes, and metadata.
- Resolver validates type correctness and produces a canonical AST representation.

---

### 7.3 Figures

Figures are non-textual artifacts.

- `artifact_type`: `"figure"`
- `format`: one of:
    - `"image.png" | "image.jpg" | "image.webp" | "image.svg" | "image.pdf"` (allow only what your renderers support)
- `spec`: `"figure.binary@v1"`
- `uri`: points to the binary image/vector file
- `sha256`: checksum of the binary bytes

### Optional sidecar metadata

If you want captions/alt text/notes:

- `meta_uri` (string), `meta_sha256` (string)
- `meta_spec`: `"figure.meta.json@v1"`

Sidecar is JSON and validated as such.

---

## 8. Provenance per entry (`origin`) and aggregation (`related`)

### 8.1 `origin` object

`origin.producer` is REQUIRED. Everything else is optional.

```json
"origin":{
"producer":"eval_yaw.py",
"tool":"python",
"command":"python eval_yaw.py --config cfg.yaml",
"timestamp":"2025-12-30T12:00:02Z"
}

```

### 8.2 `related` links (recommended for aggregates)

Use `related` to describe lineage without pretending there was one “test case”.

```json
"related":[
{"type":"dataset","id":"ds_2025-12-15_front_ir_v3"},
{"type":"artifact","id":"metric.face.yaw_mae.by_angle.v1"},
{"type":"run","id":"run_2025-12-29T03-10-11Z_def999"}
]

```

**Rules**

- `related` is optional.
- `related` MUST NOT be required by the resolver to inject payload.
- `related` exists for traceability, debugging, and audits.

---

## 9. URI resolution rules

Given:

- `artifact_root`
- `entry.uri`

Resolution behavior:

- If `uri` is absolute (e.g., `s3://...`, `https://...`, `/abs/path/...`) use as-is.
- Otherwise, resolve by joining `artifact_root` + `uri` using POSIX-style rules.

Registry MUST NOT depend on process working directory.

---

## 10. Integrity rules (hashes)

- `sha256` MUST match the exact bytes of the referenced payload file.
- If sidecar metadata exists, `meta_sha256` MUST match it too.
- Hash mismatch is a build failure in strict profiles.

---

## 11. Validation profiles (consumer behavior)

The documentation platform SHOULD support profiles per build target:

### 11.1 Internal profile (exploration-friendly)

- Missing artifact: warn or fail depending on config (default: warn in dev builds)
- Spec validation: enabled for known specs; experimental formats allowed only if explicitly marked (optional policy)
- Size limits: higher thresholds

### 11.2 External / Dossier profile (audit-friendly)

- Missing artifact: **fail**
- Hash mismatch: **fail**
- Spec validation: **required**
- For rich tables: geometry + safety checks enforced strictly
- Size limits: conservative thresholds

---

## 12. Registry invariants (must always hold)

- Each `entries[*].id` must be unique.
- `artifact_type`, `format`, `spec` must be known and compatible:
    - e.g., `artifact_type="table"` must not claim `format="metric.json"`
- All required fields must be present.
- JSON must be parseable and Unicode-valid.

---

## 13. Minimal complete example (v1.1)

```json
{
"registry_version":"aarc-1.1",
"generated_at":"2025-12-30T12:03:11Z",
"artifact_root":"artifacts/run_2025-12-30/",
"run":{
"run_id":"run_2025-12-30T12-03-11Z_abc123",
"test_id":"EuroNCAP_DMS_2026_YAW_ANGLE_SWEEP",
"pipeline":{"name":"dms-eval-pipeline","version":"0.8.4"},
"code":{"commit":"abc123def456","dirty":false},
"inputs":{"dataset_fingerprint":"sha256:1111...","config_fingerprint":"sha256:2222..."}
},
"entries":[
{
"id":"tbl.kpi.face.yaw_mae.v1",
"artifact_type":"table",
"format":"table.simple.json",
"spec":"table.simple.json@v1",
"uri":"tables/yaw_mae.json",
"sha256":"sha256:aaaa...",
"origin":{"producer":"eval_yaw.py"},
"related":[{"type":"dataset","id":"ds_2025-12-15_front_ir_v3"}]
},
{
"id":"tbl.summary.category_hierarchy.v1",
"artifact_type":"table",
"format":"table.pandoc.json",
"spec":"table.pandoc.json@v1",
"uri":"tables/category_hierarchy.table.json",
"sha256":"sha256:bbbb...",
"origin":{"producer":"make_hierarchy_table.py"}
},
{
"id":"metric.face.yaw_mae.v1",
"artifact_type":"metric",
"format":"metric.json",
"spec":"metric.json@v1",
"uri":"metrics/yaw_mae.json",
"sha256":"sha256:cccc...",
"origin":{"producer":"eval_yaw.py"}
},
{
"id":"fig.occlusion.confusion_matrix.front.v2",
"artifact_type":"figure",
"format":"image.png",
"spec":"figure.binary@v1",
"uri":"figures/occ_cm_front.png",
"sha256":"sha256:dddd...",
"origin":{"producer":"plot_confusion.py"},
"meta_uri":"figures/occ_cm_front.meta.json",
"meta_sha256":"sha256:eeee...",
"meta_spec":"figure.meta.json@v1"
}
]
}

```

---

## 14. What analysis pipeline developers must implement

**Required**

- Emit registry `aarc-1.1`
- Emit artifacts at declared URIs
- Compute sha256 for each emitted file
- Provide `origin.producer` for each entry
- Provide run-level `test_id`, `run_id`, commit, and input fingerprints

**Recommended**

- Use `related[]` to document aggregates
- Normalize strings to NFC
- Prefer `table.simple.json@v1` unless merged cells/hierarchies are needed