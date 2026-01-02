# Authoring Conventions

*(Semantic Intent Declaration for Canonical AST)*

## Purpose

This document defines how authors express **minimal semantic intent** in Markdown (`.md`) and reStructuredText (`.rst`) so that documents can be:

- deterministically updated from analysis results,
- versioned and diffed meaningfully,
- redacted and condensed safely,
- synchronized with external presentation systems.

Authors do **not** encode metadata or provenance.

They declare **semantic identity and scope only**.

All authoring constructs defined here are transformed during normalization into a **canonical Pandoc AST**, where full metadata is injected from the analysis registry.

---

## 0. Core Principle

Authoring syntax expresses **semantic intent**, not implementation details.

- Authors declare **what this block refers to** using a semantic ID.
- The system (normalization + registry) supplies:
    - role (`computed`, `hybrid`, `authored`)
    - kind (`table`, `figure`, `metric`, `annotation`)
    - source, schema, visibility, lock
- The canonical AST is fully explicit.
- The authoring syntax is intentionally minimal and readable.

This preserves live-preview ergonomics while enabling strict machine contracts.

---

## 1. Semantic Blocks (Abstract Definition)

A **semantic block** is a contiguous region of content that:

- is identified by a **semantic ID**, and
- represents either:
    - a computed artifact,
    - authored prose with ownership semantics, or
    - a hybrid annotation bound to computed content.

Semantic blocks are declared using the **authoring forms** defined below.

All forms are equivalent after normalization—both Markdown and RST converge to the same canonical Pandoc AST.

---

## 2. Supported Authoring Forms

### 2.1 Markdown: HTML Comment Fences (Primary)

This is the **preferred authoring syntax** for Markdown.

```markdown
<!-- BEGIN <semantic-id> -->
...optional prose...
<!-- END <semantic-id> -->
```

Properties:

- Invisible in live Markdown rendering
- Minimal visual noise
- Easy for humans and LLMs to read and edit
- Treated as compiler directives, not content

---

### 2.2 Markdown: Pandoc Fenced Divs (Secondary)

Pandoc fenced Divs are supported as an **alternative authoring form**.

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

### 2.3 RST: Custom Litepub Directives (Primary)

For reStructuredText, custom directives with `:id:` field are the primary form:

```rst
.. computed-figure::
   :id: fig.occlusion.confusion_matrix.front.v2

   Confusion matrix for front-facing camera occlusion detection.
```

Supported custom directives:
- `.. computed-table::` — for generated tables
- `.. computed-figure::` — for generated figures
- `.. metric::` — for scalar/structured values
- `.. annotation::` — for commentary on computed content
- `.. prose::` — for prose with ownership semantics

---

### 2.4 RST: Standard Directives with `:name:` (Alternative)

For authors who prefer standard RST syntax, or when integrating existing RST documents, semantic identity can be declared using the `:name:` attribute:

#### Figures

```rst
.. figure:: figures/confusion_matrix.png
   :name: fig.occlusion.confusion_matrix.front.v2

   Confusion matrix for front-facing camera occlusion detection.
```

#### Tables

```rst
.. table::
   :name: tbl.kpi.face.yaw_mae.v1

   +---------+---------+
   | Col A   | Col B   |
   +=========+=========+
   | ...     | ...     |
   +---------+---------+
```

**Equivalence**: The `:name:` attribute in standard RST directives is semantically equivalent to the `:id:` field in custom litepub directives. Both produce identical canonical AST after normalization.

---

## 3. Why RST Processing Differs from Markdown

### The Problem

When Pandoc parses source files, it needs to preserve semantic markers so the pipeline can find them later.

**Markdown**: Pandoc's MD reader preserves HTML comments as `RawBlock`/`RawInline` nodes:

```
Source:  <!-- BEGIN fig.test -->
AST:     {"t": "RawBlock", "c": ["html", "<!-- BEGIN fig.test -->"]}
```

The HTML comments survive parsing → adapter can find and wrap them.

**RST**: Pandoc's RST reader does NOT preserve custom directives. They get lost or converted to something unusable. For standard directives like `.. figure::`, Pandoc puts the `:name:` ID on the **inner Image element**, not on a wrapper block:

```json
{
  "t": "Figure",
  "c": [
    ["", [], []],           // Figure itself has NO ID
    [...caption...],
    [{"t": "Image", "c": [["fig:test", [], []], ...]}]  // ID buried inside
  ]
}
```

### The Solution: Text-Level Preprocessing

The RST adapter runs `preprocess_rst()` **before** Pandoc parsing to wrap directives with HTML comment fences:

```rst
.. raw:: html

   <!-- BEGIN fig:test -->

.. figure:: image.png
   :name: fig:test
   ...

.. raw:: html

   <!-- END fig:test -->
```

After Pandoc parsing, the adapter finds these fences and creates a **wrapper Div** containing the entire figure block, enabling:
- Block-level visibility filtering
- Metadata injection
- Proper resolution of computed content

### Processing Flow Comparison

| Step | Markdown | RST |
|------|----------|-----|
| 1 | — | `preprocess_rst()` wraps directives in HTML fences |
| 2 | Pandoc parses MD | Pandoc parses preprocessed RST |
| 3 | AST has `RawBlock` with HTML comments | AST has `RawBlock` with HTML comments |
| 4 | `md_adapter.apply()` wraps in Divs | `rst_adapter.apply()` → calls `md_adapter.apply()` |

After preprocessing, RST and MD converge to the same AST pattern.

---

## 4. General Rules (All Semantic Blocks)

For any semantic block:

- `<semantic-id>` is **mandatory**
- No other attributes are required or expected at authoring time
- Encoding metadata (`source`, `schema`, `visibility`, `lock`, etc.) in source is discouraged
- Normalization + registry resolution complete all missing metadata

If a semantic ID cannot be resolved during validation, the build fails (or warns in draft mode).

---

## 5. Computed Blocks

Computed blocks represent quantitative artifacts generated from analysis results.

Authors declare **only the ID and optional explanatory prose**.

### 5.1 Computed Tables

**Markdown:**
```markdown
<!-- BEGIN tbl.kpi.face.yaw_mae.v1 -->
Mean Absolute Error of face yaw estimation across yaw angles.
<!-- END tbl.kpi.face.yaw_mae.v1 -->
```

**RST (custom directive):**
```rst
.. computed-table::
   :id: tbl.kpi.face.yaw_mae.v1

   Mean Absolute Error of face yaw estimation across yaw angles.
```

**RST (standard directive):**
```rst
.. table::
   :name: tbl.kpi.face.yaw_mae.v1

   +-------+-------+
   | ...   | ...   |
   +-------+-------+
```

Rules:
- Authors MUST NOT write table rows manually (they will be replaced)
- Any prose inside the block is treated as caption or explanation

---

### 5.2 Computed Figures

**Markdown:**
```markdown
<!-- BEGIN fig.occlusion.confusion_matrix.front.v2 -->
Confusion matrix for front-facing camera occlusion detection.
<!-- END fig.occlusion.confusion_matrix.front.v2 -->
```

**RST (custom directive):**
```rst
.. computed-figure::
   :id: fig.occlusion.confusion_matrix.front.v2

   Confusion matrix for front-facing camera occlusion detection.
```

**RST (standard directive):**
```rst
.. figure:: figures/confusion_matrix.png
   :name: fig.occlusion.confusion_matrix.front.v2

   Confusion matrix for front-facing camera occlusion detection.
```

Rules:
- Caption prose is optional and editable
- No image paths or rendering parameters are authored (for custom directives)
- For standard RST `.. figure::`, the image path is required by RST syntax but will be validated/replaced

---

### 5.3 Metric Blocks

Metric blocks represent scalar or small structured values.

**Markdown:**
```markdown
<!-- BEGIN metric.face.yaw_mae.v1 -->
Mean Absolute Error of face yaw estimation (degrees).
<!-- END metric.face.yaw_mae.v1 -->
```

**RST:**
```rst
.. metric::
   :id: metric.face.yaw_mae.v1

   Mean Absolute Error of face yaw estimation (degrees).
```

Rules:
- Descriptive text is authored prose
- Numeric values are injected programmatically
- Rendering (inline vs block) depends on target and renderer

---

## 6. Prose Blocks

### 6.1 Ordinary Prose (Default)

Most prose requires no special syntax.

```
The yaw estimation error increases at extreme angles due to partial self-occlusion.
```

- No ID
- Fully editable
- No ownership semantics

---

### 6.2 Prose Owner Blocks (Rare, Explicit)

Only use when prose must **own or control** computed content.

**Markdown:**
```markdown
<!-- BEGIN prose.yaw_explanation -->
The yaw estimation error increases at extreme angles due to partial self-occlusion.
<!-- END prose.yaw_explanation -->
```

**RST:**
```rst
.. prose::
   :id: prose.yaw_explanation

   The yaw estimation error increases at extreme angles due to partial self-occlusion.
```

Semantics after normalization:
- `role=authored`
- Eligible to own dependent computed blocks
- If removed or hidden, owned computed blocks are also removed

Most prose SHOULD NOT use this.

---

## 7. Hybrid / Annotation Blocks

Hybrid blocks attach editable commentary to computed content.

**Markdown:**
```markdown
<!-- BEGIN tbl.kpi.face.yaw_mae.v1.annotation -->
Interpretation:
The error increases for extreme yaw angles due to occlusion.
<!-- END tbl.kpi.face.yaw_mae.v1.annotation -->
```

**RST:**
```rst
.. annotation::
   :id: tbl.kpi.face.yaw_mae.v1.annotation

   Interpretation:
   Error increases beyond ±40° yaw due to occlusion.
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

## 8. RST Syntax Comparison

| Aspect | Custom directive (`:id:`) | Standard RST (`:name:`) |
|--------|---------------------------|-------------------------|
| Content | Body is caption only; no payload | Syntactically complete but replaced |
| Image path | Not required | Required (will be replaced) |
| Table rows | Forbidden | Allowed (will be replaced) |

**When to use which:**

| Use Case | Recommended Form |
|----------|------------------|
| New documents designed for this pipeline | Custom directives (`:id:`) |
| Existing RST documents being integrated | Standard directives (`:name:`) |
| Documents that must also render outside this pipeline | Standard directives (`:name:`) |

---

## 9. Ownership and Visibility (Author Perspective)

Authors do **not** manually control visibility in source files.

Ownership rules:
- By default, a computed block belongs to its enclosing section
- Explicit prose owner blocks override structural ownership
- Hybrid annotations are bound to their target computed blocks

Visibility is determined by:
- the analysis registry,
- the build target (`internal`, `external`, `dossier`),
- monotonic condensation rules.

---

## 10. Prohibited Author Actions

Authors MUST NOT:

- Write manual tables or numeric results inside computed blocks
- Encode metadata (`source`, `schema`, `visibility`, `lock`) in source files
- Use prose placement alone to imply identity
- Edit computed content in presentation systems (e.g., Confluence)

Violations result in validation failure, not silent correction.

---

## 11. Mental Model for Writers

Authors should think:

> "I name what this result is.
>
> The system knows **where it comes from** and **how it is rendered**."

If this holds, the document remains coherent under automation.

---

## 12. Why This Design Works

- Markdown and RST remain readable and WYSIWYG-friendly
- Semantic identity is explicit but lightweight
- Metadata is centralized, auditable, and versioned
- AST invariants are enforceable
- LLMs can safely annotate without inventing truth
- Both formats converge to identical canonical AST

---

## Status

This document defines the **complete front-end authoring contract** for both Markdown and reStructuredText.

- **Markdown**: HTML comment fences are primary; Pandoc fenced Divs are secondary
- **RST**: Custom directives with `:id:` are primary; standard directives with `:name:` are secondary

All downstream tooling operates on the canonical AST produced after normalization.
