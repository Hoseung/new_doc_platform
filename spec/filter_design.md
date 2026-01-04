# Filtering Stage — Concept & Filter Specs (v1)

## 1. Purpose

Filtering is the stage that turns a **resolved canonical AST** into a **target-specific document AST** by removing, transforming, or sanitizing content according to build rules.

Normalization and Resolution establish *semantic correctness* (IDs, wrappers, injected payloads).

Filtering establishes *audience/target correctness* (what is shown, how it is shaped, what metadata is exposed).

Filtering MUST be:

- **Deterministic**: same input AST + same filter config ⇒ same output AST
- **Composable**: multiple filters can be applied in a fixed pipeline order
- **Auditable**: filtering decisions are explainable and reportable

---

## 2. Concept: What is a Filter?

A filter is a pure(ish) function:

```bash
Filter: (AST, FilterConfig, BuildContext) -> (AST, FilterReport)
```

A filter operates primarily on **semantic wrapper `Div`s** (the stable identity boundary), and may also operate on:

- blocks inside wrappers (presentation shaping)
- metadata/attributes on wrappers (sanitization)

### 2.1 Why filters operate on wrappers

Wrappers are your stable semantic units:

- they carry the semantic ID (`id`)
- they carry injected metadata (`role`, `kind`, `visibility`, `policies`, `lock`, provenance)
- they define an atomic unit for removal/transformation

So, filtering should avoid “string-based editing” and prefer **AST structural operations**.

---

## 3. Inputs to Filtering

### 3.1 Required inputs

- **Resolved AST** (placeholders already replaced)
- **Build Target**: `internal | external | dossier`
- **Render Target**: `pdf | html | md | rst` (the intended backend)
- **Filter Config**: thresholds and policies (see §7)

### 3.2 Required wrapper attributes

Each semantic wrapper `Div` MUST have:

- `id` (semantic ID)
- `role`: `authored | computed | hybrid`
- `kind`: `table | metric | figure | annotation | ...`
- `visibility`: `internal | external | dossier`
- `policies`: list of strings (can be empty)
- provenance attributes (optional but strongly recommended):
    - e.g. `producer`, `run_id`, `dataset_fingerprint`, `artifact_uri`, etc.

---

## 4. Filtering Pipeline Order (v1)

Filtering is applied in a fixed order to avoid surprises:

1. **Visibility Filter** (removal)
2. **Policy Filter** (removal)
3. **Metadata Strip Filter** (sanitization)
4. **Presentation Filter** (transformation)

Rationale:

- Remove first (visibility/policy).
- Strip metadata before presentation transforms (so external artifacts don’t accidentally embed internal links/provenance).
- Presentation last (it depends on what survived).

---

## 5. Filter Report (required)

Every filter MUST emit a report entry per change:

- semantic_id (if applicable)
- action: `kept | removed | transformed | stripped`
- reason_code (stable string)
- human-readable message (optional)
- location/path (optional)

A combined report is a list of entries in pipeline order.

This report is used for:

- CI checks (dossier must not strip required items silently)
- audits (why was something removed)
- debugging (which thresholds triggered appendix moves)

---

## 6. Filter Interface for Developers

### 6.1 Minimal Python shape (conceptual)

- Each filter implements:
    - `apply(ast, config, context) -> (ast, report)`
- Filters MUST be deterministic and side-effect free, except writing an optional report artifact.

### 6.2 What “deterministic” means in practice

- No dependence on wall-clock time
- No unordered iteration over dicts without sorting
- Stable ordering of moved blocks (appendix ordering must be deterministic)

---

## 7. BuildContext and FilterConfig

### 7.1 BuildContext

- `build_target`: internal | external | dossier
- `render_target`: pdf | html | md | rst
- `strict`: bool (external/dossier always strict)
- `project_root`: used to compute stable relative links when needed

### 7.2 FilterConfig (v1)

- visibility levels ordering:
    - internal < external < dossier (monotonic condensation)
- policy rules:
    - per target: forbidden policy tags
- metadata strip rules:
    - per target: which attributes to remove
- presentation thresholds:
    - `code_block_max_lines_pdf`
    - `code_block_max_chars_pdf`
    - `appendix_move_threshold_chars`
    - `appendix_move_threshold_blocks`
    - `html_fold_threshold_chars`
    - `html_fold_threshold_blocks`
- optional allowlists:
    - which block types may be folded/moved

---

# 8. Filter Spec 1 — Visibility Filter

## 8.1 Purpose

Remove semantic wrapper blocks not allowed for the build target.

## 8.2 Inputs

- Wrapper attribute: `visibility`
- BuildContext: `build_target`

## 8.3 Rules (normative)

- Each wrapper has a `visibility` level in `{internal, external, dossier}`.
- Build target defines `max_visibility`:
    - internal: allow all
    - external: allow external + dossier
    - dossier: allow dossier only
- A wrapper is **kept** iff `wrapper.visibility >= build_target` under the ordering:
    - internal < external < dossier
    - (i.e., dossier is the most public/strict)

> Equivalent view:
> 
> - internal build includes everything
> - external build excludes internal-only
> - dossier build excludes internal-only and external-only

## 8.4 Removal semantics

- Removal is **atomic** at wrapper level:
    - remove the wrapper `Div` and its entire contents
    - remove any bound annotations that target a removed wrapper (if annotations are separate wrappers)

## 8.5 Report codes

- `VIS_REMOVED_INTERNAL_ONLY`
- `VIS_REMOVED_EXTERNAL_ONLY`

## 8.6 Test checklist

- [ ]  internal build keeps all
- [ ]  external build removes internal-only wrappers
- [ ]  dossier build keeps only dossier-visible wrappers
- [ ]  removed wrapper implies its annotations are removed as well

---

# 9. Filter Spec 2 — Policy Filter

## 9.1 Purpose

Remove content based on policy tags regardless of visibility.

Examples:

- experimental content
- confidential internal data
- PII risk markers

## 9.2 Inputs

- Wrapper attribute: `policies: [string]`
- FilterConfig: forbidden policies per build target

## 9.3 Rules (normative)

- Each wrapper may declare zero or more policy tags.
- FilterConfig provides a forbidden set for the build target.
- A wrapper is removed if `wrapper.policies ∩ forbidden != ∅`.

## 9.4 Default policy sets (suggested)

- internal: forbidden = {} (or minimal)
- external: forbidden includes:
    - `internal_confidential`
    - `customer_confidential`
    - `pii_risk`
    - `experimental`
- dossier: forbidden includes everything external forbids, plus:
    - `non_reproducible`
    - `manual_override`
    - `debug_only`

## 9.5 Report codes

- `POL_REMOVED_TAG:<tag>`

## 9.6 Test checklist

- [ ]  single forbidden tag removes wrapper
- [ ]  multiple tags logs each matched reason or at least one deterministic primary reason
- [ ]  policy removal is atomic and removes bound annotations

---

# 10. Filter Spec 3 — Metadata Strip Filter

## 10.1 Purpose

Sanitize AST by removing internal/provenance attributes for external-facing outputs.

This filter does NOT remove content; it removes **metadata**.

## 10.2 Inputs

- Wrapper attributes on `Div`
- FilterConfig: strip profile by build target

## 10.3 Rules (normative)

- For `internal` build:
    - preserve provenance attributes by default
- For `external` and `dossier` builds:
    - remove or redact provenance attributes, including (suggested list):
        - `producer`
        - `run_id`
        - `dataset_id`
        - `dataset_fingerprint`
        - `config_fingerprint`
        - `artifact_uri`
        - `sha256`
        - any absolute paths
        - git repo URLs and commit hashes (optional: keep commit hash only if allowed)
- Semantic identity MUST remain:
    - `id` MUST NOT be removed
    - minimal role/kind/visibility/policies MUST remain (for traceability and consistent rendering)

## 10.4 Report codes

- `META_STRIP_ATTR:<key>`
- `META_REDACT_ATTR:<key>` (if you redact instead of remove)

## 10.5 Test checklist

- [ ]  internal keeps provenance
- [ ]  external strips provenance but keeps semantic IDs
- [ ]  dossier strips provenance and also strips any unsafe URLs/paths if present

---

# 11. Filter Spec 4 — Presentation Filter

## 11.1 Purpose

Transform the AST to improve readability and usability per render target.

This filter is **not** about correctness; it is about:

- conciseness in PDF
- navigability in HTML
- preventing huge blocks from dominating main narrative

Presentation filter MUST remain deterministic and MUST NOT change computed truth.

## 11.2 Supported transformations (v1)

### T1) PDF: Replace long code blocks with a hyperlink stub

For `render_target == pdf`:

- If a `CodeBlock` exceeds thresholds:
    - `max_lines` OR `max_chars`
- Replace with a stub block sequence:
    1. short paragraph: “Code snippet moved to external link”
    2. a link (URL) to the code artifact (e.g., Gist)
    3. optionally include first N lines as preview (deterministic N)

### Requirements for the link target

To keep determinism, the link must be derived from stable build artifacts:

- Preferred: link to a file published by your build system (static site or artifact store)
- If using Gist:
    - the pipeline must provide a stable URL in BuildContext (do not create network resources inside filtering)

**Rule:** filtering MUST NOT perform network operations.

Report code:

- `PRES_PDF_CODEBLOCK_EXTERNALIZED`

### T2) PDF: Move very long “additional” sections into Appendix

For `render_target == pdf`:

- Identify blocks/sections tagged as `additional` (choose one mechanism):
    - wrapper policy tag `additional`
    - or a wrapper attribute `presentation=additional`
    - or a dedicated `Div` class `additional`
- If such a block exceeds thresholds:
    - `appendix_move_threshold_chars` or `appendix_move_threshold_blocks`
- Replace in place with a summary stub:
    - 1–3 paragraph summary (either authored or auto-generated by a deterministic summarizer module)
    - link/reference to appendix section anchor
- Append full content to an Appendix section at end:
    - Ensure deterministic ordering of moved items (e.g., document order)

Report code:

- `PRES_PDF_MOVED_TO_APPENDIX`

> Note: “summary” should be deterministic.
v1 recommended: require an authored summary block; otherwise insert a fixed stub like:
“Content moved to Appendix: <title>”.
> 

### T3) HTML: Fold long additional content

For `render_target == html`:

- For blocks tagged `additional` that exceed thresholds:
    - wrap content in a foldable container (implementation-dependent):
        - e.g., `Div` with class `foldable` and a title
- Keep content in place but collapsed by default.

Report code:

- `PRES_HTML_FOLDED`

### T4) HTML: Fold long code blocks

For `render_target == html`:

- If code block exceeds thresholds:
    - keep code in place
    - wrap in foldable container (collapsed)
    - optionally add “copy” UI later in rendering stage

Report code:

- `PRES_HTML_CODEBLOCK_FOLDED`

## 11.3 Transformation invariants

- Computed payload must not be edited (only relocated/wrapped)
- Semantic wrapper IDs remain unchanged
- Moved content must remain referenceable (anchors stable)
- No network I/O inside filter

## 11.4 Appendix mechanism (normative)

- Appendix is a top-level section appended at end:
    - title: “Appendix” (or configurable)
- Each moved item becomes a sub-section:
    - title derived deterministically:
        - wrapper ID + first heading found, or wrapper ID alone
- Each stub inserted in main body links to appendix anchor:
    - stable anchor derived from semantic ID:
        - e.g., `#appendix-tbl-kpi-face-yaw-mae-v1`

## 11.5 Report codes

- `PRES_PDF_CODEBLOCK_EXTERNALIZED`
- `PRES_PDF_MOVED_TO_APPENDIX`
- `PRES_HTML_FOLDED`
- `PRES_HTML_CODEBLOCK_FOLDED`

## 11.6 Test checklist

- [ ]  PDF: long code becomes stub + link; code removed from main body
- [ ]  PDF: additional content moved to appendix; stub inserted; ordering stable
- [ ]  HTML: additional content wrapped as foldable; content preserved
- [ ]  HTML: long code wrapped as foldable
- [ ]  no network calls occur in filtering

---

## 12. Integration & Testing Strategy

### 12.1 Where filters run

Pipeline (simplified):

```bash
Normalize -> Resolve -> Validate -> Filter -> Render
```

Filters should run after validation, because:

- filters assume resolved, safe AST
- validation ensures payload cannot hide unsafe nodes

### 12.2 Golden tests (recommended)

Create fixtures:

- a resolved AST with:
    - internal/external/dossier wrappers
    - policy tags
    - provenance attrs
    - long code blocks
    - additional blocks

Test matrix:

- internal/pdf
- external/pdf
- dossier/pdf
- internal/html
- external/html

Assertions:

- stable diffs
- report contains expected reason codes
- appendix anchors stable
- provenance stripped where required

---

## 13. Extension points (for developers)

Developers may add new filters by:

- operating on wrapper `Div`s
- emitting report entries
- avoiding network I/O
- maintaining determinism

Suggested future filters (not v1):

- link rewriting (convert repo-relative links to published URLs)
- reference integrity checks (all appendix stubs have targets)
- de-duplication of repeated figures/tables in multi-target builds

# Deliverables

I need a filter that redacts the internal performance analysis report into external KPI document, and then to a audit-grade dossier. During so, no new computed content is needed. It’s a monotonic down-sizing process. → visibility filters

## What filters can act on

Thanks to AST, you can filter at multiple semantic levels:

1. **Block-level**: remove or keep whole semantic wrappers (`Div` with ID)
2. **Inline-level**: redact specific text spans (dangerous/annoying; use sparingly)
3. **Metadata-level**: keep content but strip attributes/provenance
4. **Asset-level**: keep a figure reference but swap/blur/remove the binary (rare but sometimes needed)

- v1 filters operate only on **wrapper `Div`s** (and their attached annotation/prose blocks), plus optional attribute stripping.
- inline redaction is out-of-scope for v1 unless you truly need it.

---

## 14. Implementation Reference

For implementation details, module organization, and code examples, see:

- **[implementation/04_filtering.md](../implementation/04_filtering.md)** — Filter stage implementation guide