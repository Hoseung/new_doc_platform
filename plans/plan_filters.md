```md
# Development Plan — Filtering Stage (v1) for AI Coders

This plan implements four filters over a **resolved + validated canonical Pandoc AST**:

1) Visibility Filter (remove wrappers)
2) Policy Filter (remove wrappers)
3) Metadata Strip Filter (sanitize wrapper attrs)
4) Presentation Filter (transform layout for PDF/HTML)

Primary success criteria:
- Deterministic output AST
- Clear filter report for every change
- No network I/O
- Subset property across targets (dossier ⊆ external ⊆ internal)

---

## 0. Deliverables

### D0. Code artifacts
- `filters/` package with four filters + shared utilities
- `filter_config.py` for config dataclasses and defaults
- `filter_report.py` for report model + serializer
- `tests/` with golden fixtures + unit tests

### D1. Spec artifacts
- `docs/04_filtering.md` (already written)
- `docs/filters/` with minimal per-filter notes (optional)

### D2. Example fixtures
- `tests/fixtures/resolved_ast_sample.json`
- `tests/fixtures/filter_config_sample.json`
- expected outputs:
  - `expected_internal_pdf.json`
  - `expected_external_pdf.json`
  - `expected_dossier_pdf.json`
  - `expected_internal_html.json`
  - `expected_external_html.json`

---

## 1. Suggested Python module skeleton

```
```
docplatform/

filters/
__init__.py
api.py                  # apply_filters(ast, config, context)
context.py              # BuildContext dataclass
config.py               # FilterConfig + defaults
report.py               # FilterReport + entries

utils/
__init__.py
ast_walk.py           # traverse blocks/divs, stable paths
wrappers.py           # wrapper detection + attribute helpers
sectioning.py         # find sections/headings, appendix builder
hashing.py            # stable anchor IDs
text_metrics.py       # char/line counters, block size estimation
visibility.py
policy.py
metadata_strip.py
presentation.py


tests/
test_filter_visibility.py
test_filter_policy.py
test_filter_metadata_strip.py
test_filter_presentation_pdf.py
test_filter_presentation_html.py
test_filter_pipeline_order.py
fixtures/

```

Notes:
- Filters operate on **semantic wrapper Divs**. Keep AST operations centralized in `utils/wrappers.py`.
- Produce stable “paths” (string) to nodes for reporting.

---

## 2. Common foundations (must do first)

### Task 2.1 — BuildContext
Create `BuildContext`:
- `build_target`: `internal|external|dossier`
- `render_target`: `pdf|html|md|rst`
- `strict`: bool (force True for external/dossier)
- `project_root`: str (for stable link generation)
- optional: `artifact_base_url`: str (if you later publish code snippets)

Acceptance checklist:
- [ ] context is immutable (dataclass frozen)
- [ ] can be serialized for debugging

### Task 2.2 — FilterConfig
Create `FilterConfig` with:
- visibility ordering map
- forbidden policies per build target
- metadata strip allow/deny lists per build target
- presentation thresholds:
  - `pdf_code_max_lines`, `pdf_code_max_chars`, `pdf_code_preview_lines`
  - `appendix_threshold_blocks`, `appendix_threshold_chars`
  - `html_fold_threshold_blocks`, `html_fold_threshold_chars`
- appendix options:
  - appendix title
  - anchor prefix

Acceptance checklist:
- [ ] defaults exist
- [ ] config is deterministic (no callables with randomness/time)
- [ ] config supports overriding via JSON/YAML later

### Task 2.3 — FilterReport model
Implement:
- `FilterReportEntry(semantic_id, action, reason_code, message?, path?)`
- `FilterReport(entries: list[...])`
- `merge()` to append reports in pipeline order
- `to_json()` for test assertions

Acceptance checklist:
- [ ] stable ordering equals actual filter application order
- [ ] reason codes are stable strings (no dynamic timestamps)

### Task 2.4 — Wrapper utilities
Implement functions:
- `iter_wrappers(ast) -> iterator[(div_node, path)]`
- `get_wrapper_id(div) -> str|None`
- `get_wrapper_attr(div, key)`
- `set_wrapper_attr(div, key, value)` / `del_wrapper_attr(div, key)`
- `is_semantic_wrapper(div)` (has id attr or matches your normalization marker)
- `get_visibility(div)` returns enum or default
- `get_policies(div)` returns list[str] (empty if missing)
- `is_additional(div)` (policy tag or class/attr)

Acceptance checklist:
- [ ] wrapper detection matches your normalization output
- [ ] no changes outside wrapper unless presentation filter

---

## 3. Filter pipeline API

### Task 3.1 — `apply_filters()`
Create `filters/api.py`:

`apply_filters(ast, filter_config, build_context) -> (ast, FilterReport)`

Pipeline order:
1) visibility
2) policy
3) metadata_strip
4) presentation

Acceptance checklist:
- [ ] order fixed and tested
- [ ] each filter returns (ast, report)
- [ ] report is merged deterministically

---

## 4. Filter 1 — Visibility Filter

### Objective
Remove wrappers not allowed by build target.

### Implementation tasks
- Define visibility ordering: `internal < external < dossier`
- Determine allowed vis for target:
  - internal: allow all
  - external: allow external + dossier
  - dossier: allow dossier only
- Traverse wrappers in document order:
  - if wrapper.visibility is below allowed: remove wrapper node

### Edge rules
- Removing a wrapper should also remove bound annotations if they exist as separate wrappers:
  - simplest v1: if annotation wrapper has `target=<id>`, remove it when target removed
  - if you don’t have that yet: skip, but add TODO and tests later

### Report reason codes
- `VIS_REMOVED_INTERNAL_ONLY`
- `VIS_REMOVED_EXTERNAL_ONLY`

Acceptance checklist
- [ ] internal build keeps all
- [ ] external removes internal-only wrappers
- [ ] dossier keeps dossier-only
- [ ] removal is atomic at wrapper level
- [ ] report includes semantic_id + path

Tests
- [ ] wrapper removal preserves surrounding AST structure
- [ ] stable ordering of remaining nodes

---

## 5. Filter 2 — Policy Filter

### Objective
Remove wrappers tagged with forbidden policy labels.

### Implementation tasks
- From config, load forbidden policy set for build target
- For each wrapper:
  - `policies = get_policies(div)`
  - if intersection non-empty: remove wrapper

### Reason codes
- `POL_REMOVED_TAG:<tag>` (choose deterministic tag if multiple):
  - recommended: sort tags and pick first, and also store full list in message

Acceptance checklist
- [ ] forbidden tags remove wrapper even if visibility allows it
- [ ] deterministic selection of primary tag for reason_code
- [ ] report contains tag(s)

Tests
- [ ] single tag removal
- [ ] multiple tags deterministic reason
- [ ] interaction with visibility filter (pipeline order)

---

## 6. Filter 3 — Metadata Strip Filter

### Objective
Strip provenance/internal metadata from wrappers for external/dossier outputs.

### Implementation tasks
- Define strip rules in config:
  - `strip_attrs_external`: list of keys or prefix patterns
  - `strip_attrs_dossier`: stricter list
- For build_target == internal: default no stripping
- For external/dossier:
  - iterate wrapper attributes:
    - never remove: `id`, `role`, `kind`, `visibility`, `policies`
    - remove: provenance keys (producer/run_id/dataset_fingerprint/config_fingerprint/artifact_uri/sha256/etc.)
    - remove or redact unsafe URLs/absolute paths in remaining attrs (optional)

### Reason codes
- `META_STRIP_ATTR:<key>` per removed key (or group into one entry per wrapper; choose one)
  - recommended: one report entry per wrapper with `message` listing stripped keys, for compactness

Acceptance checklist
- [ ] internal keeps provenance
- [ ] external strips configured keys
- [ ] dossier strips configured keys (superset of external)
- [ ] semantic identity remains intact
- [ ] deterministic ordering of stripped keys in report

Tests
- [ ] provenances removed
- [ ] protected keys remain
- [ ] report matches expected keys removed

---

## 7. Filter 4 — Presentation Filter

Presentation filter transforms AST for PDF/HTML conciseness.

### v1 scope
Implement 4 transformations:
- PDF: externalize long code blocks into link stubs
- PDF: move long additional sections to Appendix with stub
- HTML: fold long additional sections
- HTML: fold long code blocks

No network I/O; link targets must be computed from context/config.

---

### 7.1 Shared utilities for presentation

#### Task 7.1.1 — Size metrics
Implement:
- `count_codeblock_lines(codeblock) -> int`
- `count_codeblock_chars(codeblock) -> int`
- `estimate_block_chars(block) -> int` (best-effort)
- `estimate_div_blocks(div) -> int`

Acceptance checklist:
- [ ] deterministic (pure string lengths)
- [ ] works on your Pandoc block representation

#### Task 7.1.2 — Appendix builder
Implement:
- `ensure_appendix_section(ast, title="Appendix") -> (ast, appendix_path, anchor)`
- `append_to_appendix(ast, appendix_path, subsection_title, blocks, anchor_id)`

Anchor ID policy:
- deterministic from wrapper id:
  - `appendix-<semantic_id>` with safe slugging

Acceptance checklist:
- [ ] appendix created only once
- [ ] deterministic subsection ordering (document order)
- [ ] anchors stable and conflict-free

#### Task 7.1.3 — Foldable wrapper mechanism for HTML
Decide a representation (renderer must support it). v1 recommended:
- wrap content in `Div` with class `foldable` and attrs:
  - `data-title`
  - `data-collapsed=true`

This stays inside AST and renderer handles it.

Acceptance checklist:
- [ ] fold wrapper deterministic
- [ ] does not change semantic IDs of content

---

### 7.2 PDF Transformation T1 — Externalize long code blocks

#### Rules
If `render_target == pdf`:
- For each `CodeBlock`:
  - if lines > `pdf_code_max_lines` OR chars > `pdf_code_max_chars`:
    - replace with stub blocks:
      1) Para: “Code snippet omitted from PDF. See: <link>”
      2) Link block (or Para with Link inline)
      3) Optional preview: first `pdf_code_preview_lines` lines

Link computation (deterministic):
- Use `context.artifact_base_url` + stable identifier derived from AST path or hash of content
- If base_url absent: link to a local repo-relative path `code_snippets/<hash>.txt` (generated elsewhere in pipeline)

Important: filter must not create/upload gists. It may only reference stable locations.

Report code:
- `PRES_PDF_CODEBLOCK_EXTERNALIZED`

Acceptance checklist:
- [ ] CodeBlock replaced deterministically
- [ ] Preview lines deterministic
- [ ] No network I/O
- [ ] Report includes size info

Tests:
- [ ] code block over threshold replaced
- [ ] code block under threshold unchanged

---

### 7.3 PDF Transformation T2 — Move long "additional" blocks to Appendix

#### Identification of "additional"
Choose one (must be consistent):
- wrapper has policy tag `additional`
- OR wrapper attr `presentation=additional`
- OR wrapper class contains `additional`

#### Rules
If `render_target == pdf`:
- For each wrapper marked additional:
  - if block count > `appendix_threshold_blocks` OR char estimate > `appendix_threshold_chars`:
    - move entire wrapper Div to Appendix as a subsection
    - replace original location with stub:
      - Para: “Moved to Appendix: <link>”
      - optionally include authored summary if present; otherwise fixed stub

Report code:
- `PRES_PDF_MOVED_TO_APPENDIX`

Acceptance checklist:
- [ ] moved content preserved exactly
- [ ] stub inserted exactly once
- [ ] appendix anchor stable
- [ ] ordering stable

Tests:
- [ ] moved and linked
- [ ] multiple additional items keep original document order in appendix

---

### 7.4 HTML Transformation T3 — Fold long additional blocks

If `render_target == html`:
- for additional wrappers exceeding thresholds:
  - wrap content in foldable Div (collapsed)
  - keep in place

Report code:
- `PRES_HTML_FOLDED`

Acceptance checklist:
- [ ] content preserved
- [ ] fold wrapper deterministic
- [ ] no relocation

---

### 7.5 HTML Transformation T4 — Fold long code blocks

If `render_target == html`:
- for CodeBlock exceeding thresholds:
  - wrap in foldable Div (collapsed)
  - keep code as-is

Report code:
- `PRES_HTML_CODEBLOCK_FOLDED`

Acceptance checklist:
- [ ] no externalization in HTML
- [ ] code remains copyable in HTML renderer later

---

## 8. Test Plan (comprehensive checklist)

### 8.1 Unit tests per filter
- [ ] visibility: removes correct wrappers
- [ ] policy: removes correct wrappers and reports tag
- [ ] metadata: strips keys and keeps protected attrs
- [ ] presentation(pdf): externalizes code; moves additional to appendix
- [ ] presentation(html): folds code; folds additional

### 8.2 Pipeline order test
- [ ] create a fixture where:
  - wrapper is internal-only AND policy-tagged
  - ensure removal reason consistent with pipeline order
  - (visibility removes first, so policy should not see it)

### 8.3 Determinism tests
- [ ] run filter twice; output AST identical (json string equality after normalization)
- [ ] report identical

### 8.4 Regression fixtures (goldens)
For each scenario:
- internal/pdf
- external/pdf
- dossier/pdf
- internal/html
- external/html

Assert:
- [ ] expected AST equals golden
- [ ] expected report equals golden

---

## 9. Milestones

### M1 — Foundations complete
- BuildContext + FilterConfig + FilterReport + wrapper utilities + pipeline api

### M2 — Removal filters complete
- Visibility + Policy implemented and tested

### M3 — Sanitization complete
- Metadata strip implemented and tested

### M4 — Presentation complete
- Appendix move + PDF code externalize + HTML fold implemented and tested

### M5 — Integrated goldens
- Golden fixtures for all target combinations + determinism checks

---

## 10. Non-goals (explicitly out of scope for v1)
- Inline-level redaction (PII scrubbing inside prose)
- Network operations (creating gists, uploading assets)
- Reordering content for narrative flow (beyond appendix move)
- Automatic summarization using an LLM inside the build (unless you provide a deterministic summarizer)

---
