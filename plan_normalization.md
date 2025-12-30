# Plan.md — AST Normalization & Adapters (v1)

## Goal

Implement a deterministic AST normalization pipeline that ingests `.md` and `.rst` documents, identifies semantic blocks, completes metadata via an analysis registry, and outputs a **Canonical (Normalized) Pandoc AST** suitable for later resolution/filtering.

This plan includes a minimal **Normalization Harness** and golden unit tests for both `.md` and `.rst`.

---

## Non-Goals (v1)

- Rendering (HTML/PDF), theming, LaTeX templates
- Confluence sync / patch application
- Full “resolution” of computed artifacts into tables/figures (only placeholders at normalization stage)
- Adversarial / fuzz testing (later)

---

## Inputs (Spec Documents)

The repo must include these as authoritative references for agents:

- `spec/Canonical_Model_And_Contracts.md`
- `spec/AST_Invariants.md`
- `spec/AST_Normalization_Spec_v1.md`
- `spec/Markdown_Front_End_Authoring_Conventions.md`
- `spec/reST_Front_End_Authoring_Conventions.md`

**Authority rule**: Markdown author intent must only be taken from `spec/Markdown_Front_End_Authoring_Conventions.md`.

---

## Repository Skeleton
repo/
spec/
...
src/litepub_norm/
init.py
harness.py
registry.py
ast_types.py # optional helper abstractions
md_adapter.py
rst_adapter.py
core_normalize.py
serialize.py
errors.py
tests/
data/
golden_minimal.md
golden_minimal.rst
registry.json
expected_normalized_md.json
expected_normalized_rst.json
test_golden_md.py
test_golden_rst.py
test_smoke_harness.py
pyproject.toml
README.md

---

## Key Design Decisions (must follow)

1. **Pandoc AST is canonical**: all pipeline operations happen on AST, serialized as Pandoc JSON.
2. **Author intent is minimal**: authors provide only semantic IDs + optional prose; provenance/schema/visibility come from registry.
3. **Two Markdown authoring forms** are equivalent:
   - HTML comment fences (primary)
   - Pandoc fenced Divs (secondary)
4. **Normalization output** must produce wrapper `Div`s for identified blocks, with metadata completed from the registry.
5. **Computed blocks are locked by default** (`lock=true` injected).
6. **v1 constraint**: nested HTML comment fences are disallowed (hard error).

---

## Milestones

### M0 — Repo bootstrapping (0.5 day)
- Initialize repo and add `spec/` documents.
- Add `pyproject.toml` with dependencies:
  - `panflute` (or direct Pandoc JSON manipulation)
  - `pypandoc` or calling `pandoc` CLI
  - `pytest`
- Confirm `pandoc` is available in dev environment.

Deliverable:
- `pytest -q` runs with empty/placeholder tests.

---

### M1 — Define core data model + error handling (0.5–1 day)

Implement:
- `errors.py`:
  - `NormalizationError`
  - `FenceMismatchError`, `FenceOverlapError`, `UnknownSemanticIdError`, `RegistryIncompleteError`, etc.
- `registry.py`:
  - Load registry JSON
  - `resolve(id) -> dict` (role/kind/source/schema/visibility/etc.)
  - strict vs draft mode option

Deliverable:
- Unit tests for registry resolution, missing fields, strict mode behavior.

---

### M2 — Build the Normalization Harness (1 day)

**This is the most important piece**: a stable, testable driver that clarifies responsibility boundaries.

Implement `harness.py` with functions:

- `parse_to_pandoc_ast(text: str, fmt: str) -> dict`
  - Use Pandoc to parse `.md` or `.rst` into Pandoc JSON.
  - Normalize/ignore `pandoc-api-version` differences in tests if needed.

- `adapt(fmt: str, ast: dict) -> dict`
  - For `.md`: call `md_adapter.apply(ast)`
  - For `.rst`: call `rst_adapter.apply(ast)`

- `normalize(ast: dict, registry: Registry, mode: str = "strict") -> dict`
  - Call `core_normalize.apply(ast, registry, mode)`

- `serialize(ast: dict) -> str`
  - Deterministic JSON serialization: stable key ordering and attribute ordering.

Deliverable:
- `tests/test_smoke_harness.py`: parse->adapt->normalize runs without crashing for a tiny input.

---

### M3 — Implement Markdown adapter (1–1.5 days)

File: `md_adapter.py`

Responsibilities:
1. Identify HTML comment fences:
   - `<!-- BEGIN <id> -->`
   - `<!-- END <id> -->`
2. Convert fenced regions into wrapper `Div` candidates:
   - `Div.identifier = <id>`
   - `Div.attributes = []` initially
   - `Div.contents = blocks captured`
3. Remove fence markers from AST.
4. v1: reject nested/overlapping fences.
5. Pass through Pandoc fenced Divs (already `Div` nodes) as wrapper candidates.

Notes:
- Pandoc may represent HTML comments as `RawBlock` or `RawInline`. Handle both.
- Parsing must be block-accurate: fences should operate at block level.

Deliverable:
- Golden test `test_golden_md.py` passes using `golden_minimal.md` + `registry.json`.

---

### M4 — Implement reStructuredText adapter (1–2 days)

File: `rst_adapter.py`

Responsibilities:
1. Detect directive blocks corresponding to:
   - `computed-table`
   - `computed-figure`
   - `metric`
   - `annotation`
   - `prose` (optional for v1)
2. Extract `:id:` field from directive.
3. Produce wrapper `Div` candidates:
   - `Div.identifier = <id>`
   - `Div.contents = directive body blocks`
4. Ensure no provenance metadata is required from the author.

Important:
- Pandoc’s `.rst` reader might not preserve directives in a neat structure by default.
  - If directives degrade into plain text, implement a minimal preprocessor:
    - Convert known directives into a temporary syntax Pandoc preserves (e.g., fenced Div or HTML comment fences) before Pandoc parsing.
  - Prefer not to build a full parser; only support the known directive patterns in this spec.

Deliverable:
- Golden test `test_golden_rst.py` passes using `golden_minimal.rst` + `registry.json`.

---

### M5 — Core normalization (format-agnostic) (1–2 days)

File: `core_normalize.py`

Responsibilities:
1. Enforce wrapper boundary:
   - every identified block must be a `Div` with identifier = semantic ID
2. Complete metadata via registry:
   - inject `role`, `kind`, `source`, `schema`, `visibility`, `lock`
3. Apply defaults:
   - computed => `lock=true` unless specified
4. Role-based cleanup:
   - computed: strip any authored table/image/numeric payload inside wrapper (keep prose)
   - hybrid/annotation: ensure prose-only
5. Placeholder injection (recommended):
   - add `[[COMPUTED:TABLE]]` for computed tables
   - add `[[COMPUTED:METRIC]]` for metrics
   - do not require placeholder for annotation
6. Deterministic ordering:
   - stable attribute ordering for serialization/diff

Deliverable:
- Both golden tests pass with stable normalized JSON skeletons.

---

## Testing Strategy (v1)

### Golden tests (must have)
- `tests/test_golden_md.py`
- `tests/test_golden_rst.py`

Assertions should focus on invariants, not full JSON equality:
- 3 wrapper Divs exist with correct identifiers
- metadata completed as expected
- `lock=true` injected for computed
- no comment fence remnants remain
- placeholders present (if enabled)

### Snapshot files
- `tests/data/expected_normalized_md.json`
- `tests/data/expected_normalized_rst.json`

Snapshot testing is allowed, but prefer invariant assertions to reduce brittleness.

---

## Open Implementation Choice (record decision early)

### Parsing strategy
Choose one:

A) Use `pypandoc` to call pandoc and return JSON  
B) Use subprocess `pandoc -t json`

A is simpler to integrate; B is simpler to debug.

### AST manipulation library
Choose one:

A) Manipulate raw Pandoc JSON dicts directly (recommended for strictness)  
B) Use panflute objects and convert back to JSON

Direct JSON manipulation avoids hidden transforms.

Record the choice in `README.md`.

---

## Done Criteria (v1)

- `pytest` passes locally.
- Markdown adapter:
  - handles comment fences
  - rejects malformed/nested fences
- reST adapter:
  - recognizes the directive forms or uses a minimal preprocessor
- Core normalization:
  - produces canonical wrapper Divs
  - injects registry metadata + defaults
  - injects placeholders (if enabled)
- Normalized AST serializes deterministically.

---

## Next Step After v1 (optional but recommended)

Once adapters + normalization harness are stable, immediately add:
- a “resolve stage” skeleton (`resolver.py`) that replaces placeholders with generated payload from mocked analysis artifacts
- draft vs release mode validation behavior
- one adversarial test file per adapter (malformed fences, unknown IDs)

But do not block v1 on this.

---
