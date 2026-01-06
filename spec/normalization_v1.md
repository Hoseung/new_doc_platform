# AST Normalization Spec (v1)

## 1. Purpose

This document specifies how an **ingested Pandoc AST** (produced from `.md` or `.rst`) is transformed into the **Canonical AST** required by the Canonical Model & Contracts and AST Invariants.

Normalization exists to:

- make AST shape deterministic across front-end formats
- ensure computed/hybrid blocks have a consistent wrapper boundary
- enforce semantic identity placement and metadata defaults
- enable reliable validation, replacement, patching, and filtering
- preserve Markdown live-preview ergonomics while retaining strict canonical semantics

Normalization is not rendering. It MUST NOT introduce presentation/theming decisions.

---

## 2. Inputs, Outputs, and Stages

### 2.1 Input

- A Pandoc AST produced by Pandoc readers from:
    - Pandoc Markdown (`.md`)
    - reStructuredText (`.rst`)

### 2.2 Output

- A **Canonical AST** (Pandoc AST) that:
    - satisfies the AST invariants
    - contains explicit wrapper boundaries for identified blocks
    - has metadata completed from the analysis registry
    - is serializable to Pandoc JSON for diffing and inspection

### 2.3 Stages (Normalization context)

Normalization is a stage between:

1. **Ingested AST** (Pandoc output from `.md`/`.rst`)
2. **Normalized AST** (canonical wrappers + canonical keys + metadata completion)
3. **Resolved AST** (computed placeholders replaced with generated payload)
4. **Target AST** (filtered for internal/external/dossier)

This spec defines (1)→(2). It also defines preconditions needed for later resolution.

---

## 3. Normative References and Authority

### 3.1 Canonical Model & Contracts (Normative)

The Canonical Model & Contracts defines:

- what “canonical” means (Pandoc AST)
- semantic identity requirements
- roles and locking
- table/figure contracts
- Confluence sync and redaction policy

Normalization MUST implement these rules.

### 3.2 AST Invariants (Normative)

Normalization MUST produce ASTs that satisfy:

- wrapper boundaries
- ID uniqueness
- required metadata presence (after completion)
- ownership and visibility constraints (structural setup)

### 3.3 Markdown Front-End Authority (Normative)

For Markdown author intent, the **only authoritative document** is:

> Markdown Front-End Authoring Conventions (Semantic Intent Declaration for Canonical AST)
> 

This spec MUST NOT redefine Markdown authoring syntax.

If conflict exists, that Markdown conventions document governs author intent; this spec governs only AST canonicalization.

### 3.4 reStructuredText Front-End Authority (Normative)

For `.rst` author intent, the authoritative rules are:

- the project’s Authoring Conventions for `.rst` directives/macros (your `.rst` conventions doc)

This spec canonicalizes the Pandoc AST emitted by Pandoc’s `.rst` reader (and/or by a preprocessor) into the same canonical shapes used for `.md`.

---

## 4. Extensibility Model (Front-End Adapters)

Normalization is split into two conceptual layers:

1. **Front-end Adapter (format-specific)**
    
    Identifies semantic intent constructs (e.g., `.rst` directives, `.md` fences) and converts them into a common “semantic block candidate” representation in AST.
    
2. **Core Normalization (format-agnostic)**
    
    Enforces canonical wrapper shape, metadata completion, key normalization, and pre-resolution cleanup.
    

Future formats (e.g., AsciiDoc) are supported by adding a new adapter while keeping Core Normalization stable.

---

## 5. Canonical Attributes and Defaults

### 5.1 Canonical attributes

Reserved keys:

| key | meaning |
| --- | --- |
| `id` | semantic identifier (stored primarily as wrapper identifier) |
| `role` | `computed` / `authored` / `hybrid` |
| `kind` | specialization (e.g., `table`, `figure`, `metric`, `annotation`) |
| `source` | reference to analysis artifact |
| `schema` | schema or version for tables/metrics |
| `visibility` | `internal` / `external` / `dossier` |
| `lock` | `true` for computed blocks (default) |
| `bind-to` | binding target for annotations (if explicit binding is used) |
| `owner` | optional derived ownership id (derived; may be recomputed) |

### 5.2 Defaults

- If `role=computed` and `lock` absent → set `lock=true`
- If `role=hybrid` and `lock` absent → set `lock=false` (container editable; computed children remain locked)
- Visibility is not guessed by normalization unless provided by registry/policy.

### 5.3 “No guessing provenance”

Normalization MUST NOT invent missing `source` or `schema`.

If registry completion fails, validation fails (or warns only in draft mode; see §12.3).

---

## 6. Canonical Wrapper Boundary

### 6.1 Rule: all identified blocks have a wrapper `Div` (MUST)

For any identified semantic block, normalization MUST produce a wrapper `Div` with:

- `Div.identifier = <semantic-id>`
- `Div.attributes` include canonical metadata keys
- semantic payload is contained entirely inside the wrapper boundary

Rationale: replacement, patch rejection, and visibility filtering require a stable boundary.

### 6.2 Rule: IDs live on wrapper, not nested children (MUST)

If an ID is detected on a nested node (e.g., `Image`), normalization MUST lift it to the wrapper `Div`.

---

## 7. Front-End Adapter Rules (v1)

### 7.1 Markdown (`.md`) Adapter

### 7.1.1 Recognized Markdown semantic intent forms

As defined by **Markdown Front-End Authoring Conventions**, the adapter recognizes:

- HTML comment fences:
    
    `<!-- BEGIN <id> --> ... <!-- END <id> -->`
    
- Pandoc fenced Divs with `#<id>`:
    
    `::: {#<id>} ... :::`
    

The adapter MUST ignore any other “invented” markup patterns.

### 7.1.2 HTML comment fence parsing (MUST)

The adapter MUST:

- detect `BEGIN <id>` and matching `END <id>`
- treat the region between them as a semantic block body

Well-formedness requirements (MUST):

- every BEGIN has a matching END with same ID
- no overlaps
- v1: nesting is disallowed (BEGIN inside an open region is an error)

If malformed, validation fails.

### 7.1.3 Output of Markdown adapter (MUST)

Each semantic region becomes a wrapper `Div` candidate (if it’s not already a Div):

- identifier set to the semantic ID
- attributes initially empty (to be completed later)
- contents are the region body blocks

For Pandoc fenced Divs, the adapter treats them as already wrapped and passes them through as wrapper candidates.

---

### 7.2 reStructuredText (`.rst`) Adapter

The `.rst` adapter recognizes semantic intent from Pandoc's `.rst` reader output and/or from known directive patterns (depending on how you implement `.rst` directives).

v1 requirement (MUST):

- `.rst` constructs intended to represent computed/metric/hybrid blocks MUST become identifiable wrapper candidates in the ingested AST, either:
    - as `Div` nodes with identifiers, or
    - as detectable patterns that the adapter rewrites into wrapper `Div` candidates.

The adapter's goal is that `.rst` and `.md` converge to the same wrapper-candidate representation before Core Normalization.

### 7.2.1 Recognized RST Semantic Intent Forms

The adapter MUST recognize two forms of semantic block declaration:

1. **Custom litepub directives** (primary):
   ```rst
   .. computed-figure::
      :id: fig.example.v1
   ```
   Custom directives (`computed-figure`, `computed-table`, `metric`, `annotation`, `prose`) with `:id:` field.

2. **Standard RST directives with `:name:`** (secondary):
   ```rst
   .. figure:: path/to/image.png
      :name: fig.example.v1
   ```
   Standard RST directives (`figure`, `table`, `image`) with `:name:` attribute.

**Rationale**: Standard RST `:name:` is the idiomatic way to assign semantic identity in RST. Supporting it preserves RST's readability and allows authors to use familiar syntax. The `:name:` attribute is semantically equivalent to `:id:` in custom directives.

**Priority**: If both forms are present in the same document, both are recognized. The semantic ID uniqueness constraint (G3) applies regardless of which form is used.

---

## 8. Core Normalization (Format-Agnostic)

Core normalization takes wrapper candidates from adapters and produces the canonical wrapper forms.

### 8.1 Key normalization (MUST)

- Normalize reserved key spellings exactly (`visibility`, not typos).
- Remove duplicate keys; duplicates are validation failures.

### 8.2 Metadata completion via analysis registry (MUST)

For every wrapper `Div` with identifier `<id>`, normalization MUST consult the **analysis registry** (also called "normalization registry").

Registry completion injects:

- `role`
- `kind`
- `source` (required for computed)
- `schema` (required for computed tables/metrics)
- `visibility` (if provided by registry/policy)
- `lock` defaulting behavior (computed → true)

Failure modes:

- ID not found (in strict mode) → validation failure
- incomplete registry entry for computed content → validation failure
- contradictory author-specified attributes (if present) → validation failure

Note: author-specified metadata is discouraged. In v1, the system MAY ignore non-ID metadata from authoring forms and rely solely on registry.

### 8.2.1 Normalization Registry Schema (Normative)

The normalization registry is a JSON file mapping semantic IDs to their metadata:

```json
{
  "<semantic-id>": {
    "role": "computed | hybrid | authored",
    "kind": "table | figure | metric | annotation",
    "source": "path/to/artifact.json",
    "schema": "table.simple.json@v1",
    "visibility": "internal | external | dossier",
    "bind-to": "<target-semantic-id>"
  }
}
```

**Field definitions:**

| Field | Required | Description |
|-------|----------|-------------|
| `role` | Yes | Content role: `computed`, `hybrid`, or `authored` |
| `kind` | Yes | Content type: `table`, `figure`, `metric`, or `annotation` |
| `source` | For computed | Path to the artifact file (relative to registry or absolute) |
| `schema` | For computed tables/metrics | Payload schema identifier (e.g., `metric.json@v1`, `table.simple.json@v1`) |
| `visibility` | Optional | Visibility level; if absent, defaults to `internal` |
| `bind-to` | For annotations | Semantic ID of the target computed block this annotation binds to |

**Required fields by role:**

- `role=computed`: `role`, `kind`, `source`, `schema` (except figures which don't require `schema`)
- `role=hybrid`: `role`, `kind`
- `role=authored`: `role`, `kind`

**Example registry:**

```json
{
  "tbl.kpi.face.yaw_mae.v1": {
    "role": "computed",
    "kind": "table",
    "source": "artifacts/tables/yaw_mae.json",
    "schema": "table.simple.json@v1",
    "visibility": "external"
  },
  "fig.occlusion.confusion_matrix.v1": {
    "role": "computed",
    "kind": "figure",
    "source": "artifacts/figures/confusion_matrix.png",
    "visibility": "internal"
  },
  "tbl.kpi.face.yaw_mae.v1.annotation": {
    "role": "hybrid",
    "kind": "annotation",
    "bind-to": "tbl.kpi.face.yaw_mae.v1"
  }
}
```

### 8.3 Wrapper enforcement (MUST)

If a candidate is not a `Div`, wrap it in one.

If it is a `Div` but ID is not on the wrapper, lift it.

### 8.4 Role-based body cleanup (MUST)

### For `role=computed`

- Remove any manually-authored payload pretending to be computed truth:
    - tables
    - images intended as computed figures
    - numeric values formatted as final metrics
- Preserve caption/explanatory prose if present.
- Ensure the block remains replaceable as a unit.

### For `role=hybrid` (`kind=annotation`)

- Body must contain only prose blocks.
- Must be bound to a computed block via either:
    - registry rule, or
    - naming convention (e.g., `<target-id>.annotation`), or
    - explicit `bind-to` if supported

### For `role=authored`

- Preserve body as-is.

---

## 9. Placeholder Normalization (Pre-Resolution)

Normalization MUST inject placeholders into computed blocks to enable deterministic resolution.

**Required placeholders (normative for v1):**

- `[[COMPUTED:TABLE]]` — for `role=computed`, `kind=table`
- `[[COMPUTED:FIGURE]]` — for `role=computed`, `kind=figure`
- `[[COMPUTED:METRIC]]` — for `role=computed`, `kind=metric`

**Rules:**

- Placeholders are REQUIRED for all computed blocks in v1.
- Each computed block wrapper MUST contain exactly one placeholder token after normalization.
- Placeholders are not truth; they are compiler markers for the resolution stage.
- Placeholders MUST NOT survive into the final rendered target; resolution MUST replace them.
- If a placeholder survives to rendering, validation MUST fail.

**Rationale:** Mandatory placeholders ensure the resolution stage has a clear, unambiguous target for payload injection. This simplifies the resolver implementation and guarantees that every computed block is properly processed.

---

## 10. Ownership Normalization (Structural Setup)

Ownership is required to prevent orphaned computed content when prose is removed/hidden.

Normalization MUST prepare the AST so ownership can be enforced downstream by validation/filtering.

### 10.1 Ownership Model (Normative)

Every computed or hybrid block MUST have an owner. Ownership determines what happens to a block when its context is removed.

**Ownership hierarchy (in priority order):**

1. **Explicit binding** (`bind-to` attribute): The block is owned by the specified target ID
2. **Naming convention**: Annotations with ID `<target>.annotation` are owned by `<target>`
3. **Explicit prose owner**: Blocks nested inside a `prose.*` wrapper are owned by that prose block
4. **Structural ownership**: Blocks are owned by their nearest enclosing section (Header-delimited scope)

### 10.2 Ownership Computation Algorithm

```
function compute_owner(block, ast):
    # Priority 1: Explicit bind-to attribute
    if block.attributes.has("bind-to"):
        return block.attributes["bind-to"]

    # Priority 2: Naming convention for annotations
    if block.id.endswith(".annotation"):
        return block.id.removesuffix(".annotation")

    # Priority 3: Enclosing prose owner
    for ancestor in block.ancestors():
        if ancestor.id and ancestor.id.startswith("prose."):
            return ancestor.id

    # Priority 4: Nearest enclosing section
    for ancestor in block.ancestors():
        if ancestor.type == "Header":
            return section_id_for(ancestor)

    # Fallback: document root (independent)
    return None  # Block is independent
```

### 10.3 Orphan Handling (Normative)

When an owner is removed (by visibility or policy filtering), all blocks it owns MUST also be removed.

**Orphan removal rules:**

- If a prose owner block is removed → remove all owned computed/hybrid blocks
- If a computed block is removed → remove all bound annotations
- If a section is removed → remove all structurally-owned blocks within it

**Independent blocks:**

Blocks without an owner (or with `independent=true`) are not subject to orphan removal. They are only removed by their own visibility/policy settings.

### 10.4 Annotation Binding

Annotations are bound to computed content by:

- **Registry binding**: `bind-to` field in normalization registry (highest priority)
- **Naming convention**: Strip `.annotation` suffix to find target (e.g., `tbl.kpi.v1.annotation` → `tbl.kpi.v1`)
- **Explicit attribute**: `bind-to` attribute on the annotation wrapper

**Binding validation:**

- Binding target MUST exist in the document
- Binding target MUST be a computed block
- If binding target is removed, annotation MUST also be removed

### 10.5 Derived `owner` Attribute

Normalization MAY add a derived `owner=<id>` attribute to blocks for convenience. This attribute:

- Is computed, not authored
- May be recomputed at any pipeline stage
- Is stripped during metadata sanitization for external targets
- Should not be relied upon for correctness (ownership can always be recomputed from structure)

---

## 11. Determinism

Normalization MUST be deterministic:

- Same ingested AST + same registry + same config → same normalized AST
- Attribute serialization should be canonicalized for stable JSON diffs

---

## 12. Validation Interaction

### 12.1 Normalization does not “forgive”

Normalization may restructure and clean up bodies, but it MUST NOT silently accept contract violations.

Violations (duplicate IDs, malformed fences, missing required registry metadata) are validation failures.

### 12.2 Severity

- MUST violations → build failure
- SHOULD violations → warnings (configurable as failure for external/dossier targets)

### 12.3 Draft vs Release mode (recommended)

To support LLM-assisted annotation and human iteration:

- **Draft mode**: unknown IDs may be warnings (internal-only)
- **Release mode**: unknown IDs are failures (external/dossier)

This does not weaken invariants; it changes when you enforce them.

---

## 13. Known Future Extensions (Non-normative)

- Add AsciiDoc adapter that produces wrapper candidates
- Allow nested semantic regions (requires explicit nesting rules)
- Add explicit `bind-to` for Markdown annotations (comment syntax)
- Multi-file composition (includes) while maintaining ID uniqueness and ownership
- Richer “caption vs body” separation for figures/tables

---

## 14. Summary

- Pandoc AST is canonical.
- `.md` and `.rst` are ingestion formats.
- Markdown author intent is defined **only** in the Markdown Front-End Authoring Conventions document.
- Normalization converts front-end intent into canonical wrapper `Div`s, completes metadata via registry, enforces determinism, and prepares for resolution/visibility/patching.

---

## 15. Implementation Reference

For implementation details, module organization, and code examples, see:

- **[implementation/01_normalization.md](../implementation/01_normalization.md)** — Detailed implementation guide covering adapters, registry, and core normalization