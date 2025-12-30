# Authoring Conventions — Markdown Front-end

*(Semantic Intent Declaration for Canonical AST)*

## Purpose

This document defines how authors express **minimal semantic intent** in Markdown so that documents can be:

- deterministically updated from analysis results,
- versioned and diffed meaningfully,
- redacted and condensed safely,
- synchronized with external presentation systems.

Authors do **not** encode metadata.

They declare **identity and scope only**.

All authoring syntax defined here is transformed during normalization into a **canonical Pandoc AST**, where full metadata is injected from the analysis registry.

---

## 0. Core Principle

Markdown authoring syntax expresses **semantic intent**, not implementation details.

- Authors declare **what this block refers to** using a semantic ID.
- The system (normalization + registry) supplies:
    - role (`computed`, `hybrid`, `authored`)
    - kind (`table`, `figure`, `metric`, `annotation`)
    - source, schema, visibility, lock
- The canonical AST is fully explicit.
- The authoring syntax is intentionally minimal and readable.

This preserves Markdown’s live-preview ergonomics while enabling strict machine contracts.

---

## 1. Semantic Blocks (Abstract Definition)

A **semantic block** is a contiguous region of Markdown that:

- is identified by a **semantic ID**, and
- represents either:
    - a computed artifact,
    - authored prose with ownership semantics, or
    - a hybrid annotation bound to computed content.

Semantic blocks are declared using one of the supported **authoring forms** below.

All forms are equivalent after normalization.

---

## 2. Supported Authoring Forms

### 2.1 HTML Comment Fences (Primary, Recommended)

This is the **preferred authoring syntax** for Markdown.

```markdown
<!-- BEGIN<semantic-id> -->
...optional prose...
<!-- END<semantic-id> -->
```

Properties:

- Invisible in live Markdown rendering
- Minimal visual noise
- Easy for humans and LLMs to read and edit
- Treated as compiler directives, not content

This form SHOULD be used by default.

---

### 2.2 Pandoc Fenced Divs (Secondary, Optional)

Pandoc fenced Divs are supported as an **alternative authoring form**, primarily for advanced users.

```markdown
::: {#<semantic-id>}
...optional prose...
:::
```

Properties:

- Parsed directly by Pandoc into `Div` nodes
- More verbose and visually intrusive
- Functionally equivalent to HTML comment fences after normalization

This form SHOULD be avoided in casual authoring.

---

## 3. General Rules (All Semantic Blocks)

For any semantic block:

- `<semantic-id>` is **mandatory**
- No other attributes are required or expected at authoring time
- Encoding metadata (`source`, `schema`, `visibility`, `lock`, etc.) in Markdown is discouraged
- Normalization + registry resolution complete all missing metadata

If a semantic ID cannot be resolved during validation, the build fails (or warns in draft mode).

---

## 4. Computed Blocks

Computed blocks represent quantitative artifacts generated from analysis results.

Authors declare **only the ID and optional explanatory prose**.

### 4.1 Computed Tables

### Authoring (HTML comment form)

```markdown
<!-- BEGIN tbl.kpi.face.yaw_mae.v1 -->
Mean Absolute Error of face yaw estimation across yaw angles.
<!-- END tbl.kpi.face.yaw_mae.v1 -->
```

Rules:

- Authors MUST NOT write table rows manually
- Any prose inside the block is treated as caption or explanation
- The table itself is generated programmatically

During normalization and resolution:

- The ID is resolved via the analysis registry
- The block becomes `role=computed`, `kind=table`, `lock=true`
- The body is replaced with a generated `Table` node

---

### 4.2 Computed Figures

```markdown
<!-- BEGIN fig.occlusion.confusion_matrix.front.v2 -->
Confusion matrix for front-facing camera occlusion detection.
<!-- END fig.occlusion.confusion_matrix.front.v2 -->
```

Rules:

- Caption prose is optional and editable
- No image paths or rendering parameters are authored
- Visual appearance is controlled by the rendering/theming layer

---

### 4.3 Metric Blocks

Metric blocks represent scalar or small structured values.

```markdown
<!-- BEGIN metric.face.yaw_mae.v1 -->
Mean Absolute Error of face yaw estimation (degrees).
<!-- END metric.face.yaw_mae.v1 -->
```

Rules:

- Descriptive text is authored prose
- Numeric values are injected programmatically
- Rendering (inline vs block) depends on target and renderer

---

## 5. Prose Blocks

### 5.1 Ordinary Prose (Default)

Most prose requires no special syntax.

```markdown
The yaw estimation error increases at extreme angles due to partial self-occlusion.
```

- No ID
- Fully editable
- No ownership semantics

---

### 5.2 Prose Owner Blocks (Rare, Explicit)

Only use when prose must **own or control** computed content.

```markdown
<!-- BEGIN prose.yaw_explanation -->
The yaw estimation error increases at extreme angles due to partial self-occlusion.
<!-- END prose.yaw_explanation -->
```

Semantics after normalization:

- `role=authored`
- Eligible to own dependent computed blocks
- If removed or hidden, owned computed blocks are also removed

Most prose SHOULD NOT use this.

---

## 6. Hybrid / Annotation Blocks

Hybrid blocks attach editable commentary to computed content.

```markdown
<!-- BEGIN tbl.kpi.face.yaw_mae.v1.annotation -->
Interpretation:
The error increases for extreme yaw angles due to occlusion.
<!-- END tbl.kpi.face.yaw_mae.v1.annotation -->
```

Rules:

- Annotation IDs conventionally use `.annotation` suffix
- Only prose is authored
- No computed payload is embedded

Semantics:

- `role=hybrid`, `kind=annotation`
- Bound to the referenced computed block
- Visibility is inherited
- Removed automatically if the bound block is removed

---

## 7. Ownership and Visibility (Author Perspective)

Authors do **not** manually control visibility in Markdown.

Ownership rules:

- By default, a computed block belongs to its enclosing section
- Explicit prose owner blocks override structural ownership
- Hybrid annotations are bound to their target computed blocks

Visibility is determined by:

- the analysis registry,
- the build target (`internal`, `external`, `dossier`),
- monotonic condensation rules.

---

## 8. Prohibited Author Actions

Authors MUST NOT:

- Write manual tables or numeric results inside computed blocks
- Encode metadata (`source`, `schema`, `visibility`, `lock`) in Markdown
- Use prose placement alone to imply identity
- Edit computed content in presentation systems (e.g., Confluence)

Violations result in validation failure, not silent correction.

---

## 9. Mental Model for Writers

Authors should think:

> “I name what this result is.
> 
> 
> The system knows **where it comes from** and **how it is rendered**.”
> 

If this holds, the document remains coherent under automation.

---

## 10. Why This Design Works

- Markdown remains readable and WYSIWYG-friendly
- Semantic identity is explicit but lightweight
- Metadata is centralized, auditable, and versioned
- AST invariants are enforceable
- LLMs can safely annotate without inventing truth

---

### Status

This document defines the **complete and consistent Markdown front-end contract**.

HTML comment fences are the **primary authoring form**.

Pandoc fenced Divs are an **equivalent but secondary form**.

All downstream tooling operates on the canonical AST produced after normalization.