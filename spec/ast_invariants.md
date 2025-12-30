# AST Invariants

## 0. Purpose

This document defines **AST invariants**: properties that must always hold for the canonical Pandoc AST at specific stages of the pipeline. They are **NOT negotiable**.

Invariants are used to:

- prevent semantic drift during transformations
- enforce identity and locking rules
- make Confluence round-tripping safe
- guarantee monotonic redaction (internal → external → dossier)
- ensure deterministic replacement of computed elements

Violations of MUST-level invariants are **build failures**.

---

## 1. Pipeline Stages and When Invariants Apply

We define four canonical stages:

1. **Ingested AST**: parsed from `.rst` (or other front-ends) into Pandoc AST
2. **Normalized AST**: canonicalized structural form (IDs, wrappers, attribute normalization)
3. **Resolved AST**: computed placeholders replaced by generated content
4. **Target AST**: filtered for a build target (internal / external / dossier) and ready to render / publish

Each invariant specifies the stage(s) where it must hold.

---

## 2. Global Structural Invariants

### G1. Canonical AST is valid Pandoc AST (MUST)

**Applies:** Ingested, Normalized, Resolved, Target

- The AST must be parseable and serializable via Pandoc JSON without loss of required attributes.

**Rationale:** if the AST cannot round-trip, your pipeline can’t be trusted.

---

### G2. Attribute schema is normalized (MUST)

**Applies:** Normalized, Resolved, Target

- Attribute keys used by this system are normalized (e.g., exact spelling, casing).
- Unknown keys are permitted but must not conflict with reserved keys.

**Reserved keys:** `id`, `role`, `source`, `schema`, `visibility`, `lock`, optionally `kind`, `bind`.

**Rationale:** prevents silent contract drift (“visiblity” bugs are brutal).

---

### G3. No duplicate semantic IDs within a document scope (MUST)

**Applies:** Normalized, Resolved, Target

- For all elements that carry `id`, the `id` values must be unique within the document.

**Rationale:** identity collisions make updates nondeterministic.

---

### G4. Semantic IDs are stable strings (MUST)

**Applies:** Normalized, Resolved, Target

- `id` must be a non-empty string matching a strict pattern.
- `^[a-z][a-z0-9_.-]*\.v[0-9]+$`
    - Start with a lowercase letter (a-z)
    - Then any combination of lowercase letters, numbers, underscores, dots, or hyphens (can be empty too)
    - End with `.v` followed by a version number (one or more digits)

**Rationale:** reduces accidental breakage and improves tooling compatibility.

---

## 3. Role and Locking Invariants

### R1. Every identified quantitative element has a role (MUST)

**Applies:** Normalized, Resolved, Target

- Any element with `id` that represents a quantitative element (table, figure, metric) must have `role ∈ {computed, authored, hybrid}`.
- For computed elements, `lock` is implicitly true unless explicitly set.

**Rationale:** prevents ambiguous interpretation during regeneration and patching.

---

### R2. Computed blocks are locked and replaceable (MUST)

**Applies:** Normalized, Resolved, Target

- For `role=computed`: `lock=true` must hold.
- Computed blocks must be declared in a way that makes them fully replaceable as a unit (i.e., a wrapper `Div` boundary exists).

**Rationale:** enables unconditional overwrite and prevents partial corruption.

---

### R3. Hybrid blocks declare explicit editable zones (MUST)

**Applies:** Normalized, Resolved, Target

- For `role=hybrid`, the AST must explicitly separate:
    - computed sub-block(s) and
    - authored annotation zone(s)
- Editable zones must be identifiable by attributes (e.g., `role=authored` child or `kind=annotation`).

**Rationale:** prevents LLM/humans from editing computed content “by accident”.

---

### R4. Authored blocks must not contain computed metadata (SHOULD)

**Applies:** Normalized

- Pure prose blocks should not carry `source`, `schema`, or `lock` attributes unless explicitly intended.

**Rationale:** keeps metadata from leaking everywhere and confusing diff/patch logic.

---

## 4. Computed Element Invariants

### C1. Computed elements must declare provenance (MUST)

**Applies:** Normalized, Resolved, Target

For `role=computed` elements:

- `source` is required (reference to analysis artifact)
- `schema` is required for tables and metrics
- `visibility` is required if the element is visibility-controlled at block-level

**Rationale:** enables traceability and validation that “truth came from analysis”.

---

### C2. Computed table placeholders must be empty or marked (MUST)

**Applies:** Normalized

- Before resolution, computed table blocks must not contain author-written table rows.
- They may contain an explicit placeholder token or an empty body.

**Rationale:** prevents authors from accidentally creating “semi-computed” tables.

---

### C3. Resolution produces exactly one authoritative computed payload (MUST)

**Applies:** Resolved

- Each computed placeholder must resolve to exactly one generated payload:
    - tables resolve to a single `Table` node (plus optional caption text)
    - figures resolve to a single `Image` node or an equivalent figure container
    - metrics resolve to a single value representation (inline or block), as defined by the metric contract

**Rationale:** eliminates ambiguous partial generation.

---

### C4. Computed payload must remain within wrapper boundary (MUST)

**Applies:** Resolved, Target

- Generated content must be contained entirely within the wrapper element that carries the semantic ID.

**Rationale:** makes replacement and patch rejection reliable.

---

### **C5. Ownership Invariant (MUST)**

Every computed block must either:

- be structurally contained within a prose scope (section or block), or
- explicitly declare itself as independent

If a prose scope is removed, filtered, or hidden, all computed blocks owned by that scope must also be removed.

Computed blocks without an owner must be explicitly marked as `independent=true`.

**Rationale:** A prose owns relevant computed blocks. Ownership reveals semantics

---

## 5. Visibility and Redaction Invariants

### V1. Visibility values are from the allowed set (MUST)

**Applies:** Normalized, Resolved, Target

- If `visibility` is present, it must be one of: `internal`, `external`, `dossier`.

**Rationale:** prevents accidental “external-ish” leaks.

---

### V2. Monotonic condensation holds (MUST)

**Applies:** Target

For targets `internal`, `external`, `dossier`:

- A downstream target must not contain a computed element whose `id` is absent from upstream targets unless explicitly whitelisted as “downstream-only” (default: disallowed).
- Practically: `IDs(dossier) ⊆ IDs(external) ⊆ IDs(internal)` for computed elements.

**Rationale:** enforces your core information-flow contract.

---

### V3. No internal-only computed element survives external/dossier builds (MUST)

**Applies:** Target

- Any `visibility=internal` block must be removed from `external` and `dossier` targets.
- The removal must not leave dangling references (see V4).

**Rationale:** stops leakage.

---

### V4. Reference integrity after filtering (MUST)

**Applies:** Target

- After visibility filtering, internal cross-references must remain valid:
    - no links to removed anchors (unless link is also removed)
    - no references to removed figures/tables (unless replaced with a controlled placeholder)

**Rationale:** prevents broken “compiled” documents.

---

## 6. Confluence Patch Invariants

### P1. Patch application cannot modify locked blocks (MUST)

**Applies:** Normalized (during patch application)

- If an inbound Confluence-derived AST differs from canonical AST inside any `lock=true` block, patch application must fail (or at minimum flag and drop those hunks; choose one and enforce it consistently).

**Rationale:** you want “computed truth is immutable” to be a hard law.

---

### P2. Patch application is limited to allowed zones (MUST)

**Applies:** Normalized (during patch application)

- Only `role=authored` blocks and explicitly defined annotation zones may be changed by patches or LLM-generated edits.

**Rationale:** prevents “LLM helpfully rewrote a KPI label” disasters.

---

### P3. Patch must preserve semantic IDs and metadata (MUST)

**Applies:** Normalized (during patch application)

- A patch must not:
    - add/remove/change `id` values of existing computed elements
    - change `source`, `schema`, `visibility`, `role`, `lock` of computed elements

**Rationale:** identity and provenance are part of truth.

---

## 7. Determinism Invariants

### D1. Normalization is deterministic (MUST)

**Applies:** Normalized

- Given the same input document, normalization produces byte-stable Pandoc JSON (after canonical ordering of attributes, etc.).

**Rationale:** makes diffs meaningful and automation trustworthy.

---

### D2. Resolution is deterministic given analysis artifacts (MUST)

**Applies:** Resolved

- Given the same canonical AST + the same analysis artifacts, the resolved AST is semantically identical (allowing theming differences downstream).

**Rationale:** ensures the system behaves like a compiler, not a slot machine.

---

## 8. Validation Severity Policy

- MUST invariant violation → build failure
- SHOULD invariant violation → build warning (may be configured as failure for external/dossier targets)
- Any violation affecting visibility/redaction → always failure for external/dossier targets

---

## 9. Appendix: Recommended Normalization Rules (Non-normative)

- Canonicalize attribute ordering for stable JSON diffs
- Normalize whitespace-only nodes (remove empty paragraphs)
- Wrap computed elements in a `Div` if the front-end cannot attach attributes directly
- Enforce that `id` lives on the wrapper boundary, not on nested children