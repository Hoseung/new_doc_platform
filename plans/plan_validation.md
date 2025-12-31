# Validator Development Plan (AST-first, strict where it matters)

This plan covers two complementary validators:

1) **Payload Validator**: validates analysis artifacts before emission (what you already have).
2) **Document AST Validator**: validates the final resolved AST after placeholder replacement.

Goal: make invalid states **impossible**, keep failures **loud and localized**, and avoid per-artifact bespoke rules.

---

## 0. Validation philosophy

### 0.1 Two kinds of strictness
- **Safety strict (always ON)**: prevents injection/escape, non-determinism, and malformed structures that can corrupt rendering.
- **Completeness strict (profile-based)**: missing artifacts can be warnings in internal/draft but MUST fail in external/dossier.

### 0.2 Profiles
Define profiles that control severity and limits:

- `internal_dev` (lenient completeness, strict safety, high limits)
- `internal_ci` (strict completeness for regressions, strict safety)
- `external` (strict completeness, strict safety, tighter limits)
- `dossier` (strictest, tightest limits, no raw)

---

## 1. Refactor target architecture

### 1.1 Separate modules
- `validator/payload/*`: per-spec payload validators (metric/table_simple/table_pandoc/figure_meta)
- `validator/document/*`: whole-document AST invariants (post-resolution)
- `validator/pandoc_walk.py`: one generic walker used everywhere

### 1.2 Unified error model
Create a single error type:
- `ValidationError(code, message, semantic_id=None, ast_path=None, spec=None, hint=None)`

Include:
- `code`: stable string for tests (e.g., `VAL_METRIC_VALUE_BOOL`)
- `semantic_id`: semantic ID when available
- `ast_path`: a stable pointer string (block path, div path)
- `hint`: “how to fix” text

---

## 2. Payload Validator Plan (improvements)

### 2.1 Common checks (all payloads)
Checklist:
- [ ] JSON payload is valid UTF-8 JSON (if json-based)
- [ ] Strings are valid Unicode (Python will guarantee) and SHOULD be normalized to NFC upstream (optional warning)
- [ ] Reject extremely large payloads early (file-size guard before parse) for DOS prevention
- [ ] All numeric fields reject NaN/Inf (float-only edge)
- [ ] Policy: decide whether to reject unknown top-level keys:
  - Option A: allow `meta` only
  - Option B: allow extra fields in internal, reject in dossier

Implementation notes:
- Always check `isinstance(x, bool)` before number checks (bool is int).

---

## 3. Metric Validator (`metric.json@v1`)

### 3.1 Required strict checks
Checklist:
- [ ] Payload is an object
- [ ] `label`: non-empty string (strip)
- [ ] `value`: number BUT NOT bool
- [ ] `value`: reject NaN/Inf
- [ ] `unit` if present: non-empty string OR allow empty string (choose one)
- [ ] `lower_is_better` if present: bool
- [ ] `notes` if present: list[str]
- [ ] `meta` if present: object

### 3.2 Format string constraints (recommended)
Checklist:
- [ ] `format` if present: string length <= N (e.g., 200)
- [ ] allow only `{value}` and `{unit}` tokens (no `.format()` mini-language)
- [ ] forbid newline in `format` (optional)
- [ ] forbid braces other than `{value}`/`{unit}` (optional)

### 3.3 Tests
Checklist:
- [ ] `value=True` fails (bool-as-number bug)
- [ ] `value=float('nan')` fails if it appears (via python payload injection tests)
- [ ] `label=""` fails
- [ ] `notes=[1,2]` fails
- [ ] `format="{value:.2f}"` passes only if policy allows (if you disallow, test fail)

---

## 4. Simple Table Validator (`table.simple.json@v1`)

### 4.1 Core structure checks
Checklist:
- [ ] Payload is an object
- [ ] `columns`: list with >=1
- [ ] each column is object
- [ ] `key`: string matches identifier regex
- [ ] column keys are unique
- [ ] `rows`: list
- [ ] each row is object

### 4.2 Row/column key policy (you MUST choose)
Pick one and enforce consistently:

**Policy S (Strict rectangular):**
- [ ] For every row: `set(row.keys()) == set(column_keys)`

**Policy P (Permissive but deterministic):**
- [ ] Extra keys forbidden
- [ ] Missing keys allowed but treated as `null` during emission
- [ ] In validator: either
  - [ ] allow missing keys, OR
  - [ ] normalize missing -> null in a pre-validation normalization step

### 4.3 Dtype enforcement (recommended)
If `dtype` exists, enforce it:
Checklist:
- [ ] `int`: value is int and NOT bool (or null)
- [ ] `float`: value is number and NOT bool (or null); reject NaN/Inf
- [ ] `bool`: value is bool (or null)
- [ ] `string`: value is str (or null)

### 4.4 Size limits (profile based)
Checklist:
- [ ] max rows
- [ ] max columns
- [ ] max cells (rows*cols)
- [ ] max per-cell string length (optional)
- [ ] max total string bytes (optional)

### 4.5 Optional strictness
Checklist:
- [ ] reject unknown top-level keys (except `meta`) in dossier
- [ ] caption/notes types validated if present

### 4.6 Tests
Checklist:
- [ ] duplicate column keys fails
- [ ] row has extra key fails
- [ ] row missing key fails (Policy S) OR passes (Policy P) with deterministic normalization
- [ ] dtype mismatch fails
- [ ] bool in numeric dtype fails
- [ ] huge table triggers size limit

---

## 5. Pandoc Table Payload Validator (`table.pandoc.json@v1`)

### 5.1 Critical improvement: implement a generic Pandoc walker
Your current traversal is incomplete. Replace “manual recursion into Para/Plain only” with a generic walker.

Checklist:
- [ ] `walk_pandoc(node, context)` visits every node recursively
- [ ] Each node has either:
  - [ ] dict with `"t"` and optional `"c"`, OR
  - [ ] list of nodes
  - [ ] primitive
- [ ] Walker knows whether it is in Block or Inline context (or infer per `"t"`)

### 5.2 Node type allowlist enforcement (safe mode)
You already have SAFE type sets; enforce them.

Checklist (safe mode, `allow_raw_pandoc=False`):
- [ ] Reject `RawInline`, `RawBlock` always
- [ ] Reject `Div` always (payload must not smuggle wrappers)
- [ ] Reject any node whose `"t"` not in allowlist for its context
- [ ] Ensure walker reaches all nested lists (BulletList/OrderedList/DefinitionList/Table cells etc.)

Checklist (allow-raw mode):
- [ ] Still reject `Div`
- [ ] Allow RawInline/RawBlock only if config says so
- [ ] Still traverse everything to find disallowed types

### 5.3 Structural checks (Table/Row/Cell)
Checklist:
- [ ] Root is exactly one block with `t == "Table"`
- [ ] Table structure is well-formed per your Pandoc JSON dialect:
  - [ ] has expected `c` structure
  - [ ] TableHead/TableBody/TableFoot exist as expected (or accept variants if needed)
- [ ] Each Row has `t=="Row"` and correct fields
- [ ] Each Cell has `t=="Cell"` and correct fields
- [ ] `rowspan >= 1`, `colspan >= 1`

### 5.4 Geometry checks (recommended for merged cells)
Compute a grid occupancy model.

Checklist:
- [ ] Infer column count from colspecs or from max row expansion
- [ ] For each row, simulate placement of cells left-to-right:
  - [ ] Ensure `colspan` does not exceed remaining columns
  - [ ] Mark occupied cells in a grid (rowspan extends to future rows)
- [ ] Overlap forbidden: a grid position cannot be occupied twice
- [ ] Optional: no holes (each row’s columns fully covered after expansion)
- [ ] Ensure total expanded cell count <= limit

### 5.5 Safety beyond raw
Checklist:
- [ ] Disallow Images inside table unless explicitly allowed
- [ ] Disallow Links with unsafe URL schemes (optional policy) in dossier
- [ ] Disallow HTML attributes/classes/IDs in Attr (recommended):
  - [ ] Cell Attr identifier must be empty
  - [ ] Row/Table Attr must not include IDs/classes
  - [ ] Or: allow only whitelisted attributes

### 5.6 Tests
Checklist:
- [ ] RawInline buried in BulletList inside cell is detected and rejected (safe mode)
- [ ] Unknown node type rejected (safe mode)
- [ ] Div rejected always
- [ ] rowspan=0 fails
- [ ] Overlapping spans fails (geometry)
- [ ] Out-of-bounds span fails

---

## 6. Figure Meta Validator (`figure.meta.json@v1`)

Checklist:
- [ ] payload is object
- [ ] caption/alt if present: string
- [ ] notes if present: list[str]
- [ ] meta if present: object
- [ ] optional: reject unknown keys in dossier

Tests:
- [ ] notes not list[str] fails
- [ ] caption non-string fails

---

## 7. Document AST Validator (post-resolution)

This is the missing “strict AST verification” layer.

### 7.1 Placeholder elimination
Checklist:
- [ ] No placeholder tokens remain anywhere (`[[COMPUTED:*]]`)
- [ ] Computed wrappers contain no placeholder-only blocks

### 7.2 Wrapper discipline
Checklist:
- [ ] Wrapper IDs unique across document
- [ ] All computed payload blocks appear only inside a computed wrapper `Div`
- [ ] Each computed wrapper contains exactly one computed payload “primary block”:
  - metric: 1 Table block (your chosen form)
  - figure: Image/Figure block(s)
  - table: Table block
- [ ] Locked computed wrappers contain no authored edits to computed payload (if you support lock semantics)

### 7.3 Role/kind consistency
Checklist:
- [ ] Wrapper attribute `kind` matches the injected payload kind
- [ ] Wrapper attribute `role` is consistent (computed/hybrid/authored)
- [ ] Annotation wrappers (if any) bind to existing target IDs

### 7.4 Global safety scan
Checklist:
- [ ] If `allow_raw_pandoc=False`: document contains no RawInline/RawBlock anywhere
- [ ] No `Div` nodes exist inside payloads that aren’t wrappers (optional)
- [ ] No unexpected IDs inside inner nodes (optional)

### 7.5 Target-specific policy checks
Checklist:
- [ ] External/dossier builds contain no internal-only blocks (visibility monotonicity)
- [ ] Dossier builds enforce stricter size limits

### 7.6 Tests
Checklist:
- [ ] leftover placeholder fails
- [ ] computed table block found outside wrapper fails
- [ ] raw block anywhere fails in dossier
- [ ] duplicate semantic IDs fail

---

## 8. Implementation steps (recommended order)

### Step 1 — Fix numeric type bug immediately
- [ ] Reject bool for numeric fields in metric and table dtype checks.

### Step 2 — Implement the generic Pandoc walker
- [ ] Replace current partial recursion with full traversal.
- [ ] Enforce allowlists in safe mode.

### Step 3 — Strengthen table.simple invariants
- [ ] Choose missing-keys policy and enforce.
- [ ] Enforce dtype checks (optional but recommended).

### Step 4 — Add post-resolution AST validator
- [ ] Placeholder elimination
- [ ] Wrapper discipline + ID uniqueness
- [ ] Global safety scan

### Step 5 — Geometry for table.pandoc (if you need merged cells correctness)
- [ ] Add overlap/out-of-bounds checks
- [ ] Add expanded-size caps

---

## 9. “Definition of Done” (Validator)

- [ ] Every payload spec has a validator that is strict on safety and determinism.
- [ ] Pandoc payload validation cannot be bypassed by nesting content in untraversed nodes.
- [ ] Document AST validator guarantees no unresolved placeholders and enforces wrapper discipline.
- [ ] Validation behavior is controlled by profiles; dossier/external are fail-fast.
- [ ] Error messages include semantic ID + location and suggest a fix.
- [ ] Tests cover the bool-as-number bug and at least one “hidden RawInline” case.

---
