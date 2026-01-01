# Authoring Conventions — reStructuredText Front-End

*(Semantic Intent Declaration for Canonical AST)*

## Purpose

This document defines how authors express **minimal semantic intent** when writing documents in **reStructuredText (`.rst`)**, so that documents can be:

- deterministically updated from analysis outputs,
- versioned and diffed meaningfully,
- redacted and condensed safely,
- synchronized with external presentation systems.

Authors do **not** encode metadata or provenance.

They declare **semantic identity and scope only**.

All `.rst` authoring constructs defined here are transformed during normalization into a **canonical Pandoc AST**, where full metadata is injected programmatically.

---

## 0. Core Principle

reStructuredText authoring syntax expresses **semantic intent**, not implementation metadata.

- Authors declare **what this block refers to** using a semantic ID.
- The system (analysis registry + normalization) supplies:
    - role (`computed`, `hybrid`, `authored`)
    - kind (`table`, `figure`, `metric`, `annotation`)
    - source, schema, visibility, lock
- The canonical AST is fully explicit.
- The authoring syntax is intentionally minimal and readable.

This preserves `.rst`’s readability and structure while maintaining strict machine contracts.

---

## 1. Semantic Blocks (Abstract Definition)

A **semantic block** is a region of content that:

- is identified by a **semantic ID**, and
- represents either:
    - a computed artifact,
    - authored prose with ownership semantics, or
    - a hybrid annotation bound to computed content.

Semantic blocks are declared using `.rst` directives defined in this document.

---

## 2. General Rule (All Identified Blocks)

Any block with semantic meaning MUST declare a **semantic ID**.

Rules:

- The semantic ID is mandatory.
- No other metadata is required or expected at authoring time.
- Inline metadata (e.g., source paths, schema names, visibility) is discouraged.
- All metadata is resolved during normalization via the analysis registry.

If a semantic ID cannot be resolved later, validation fails.

---

## 3. Computed Blocks

Computed blocks represent quantitative artifacts generated from analysis results.

Authors declare **only identity and optional explanatory prose**.

Two syntactic forms are supported: custom litepub directives and standard RST directives.

---

### 3.1 Computed Tables

#### Custom directive syntax (primary)

```
.. computed-table::
   :id: tbl.kpi.face.yaw_mae.v1

   Mean Absolute Error of face yaw estimation across yaw angles.

```

Rules:

- Authors MUST NOT write table rows manually.
- Any body content is treated as caption or explanatory prose.
- The actual table is generated programmatically.

---

### 3.2 Computed Figures

#### Custom directive syntax (primary)

```
.. computed-figure::
   :id: fig.occlusion.confusion_matrix.front.v2

   Confusion matrix for front-facing camera occlusion detection.

```

Rules:

- No image paths or rendering parameters are authored.
- Caption prose is optional and editable.
- Visual appearance is handled entirely downstream.

---

### 3.3 Standard RST Syntax (Alternative)

For authors who prefer standard RST syntax, or when integrating existing RST documents, semantic identity can be declared using the `:name:` attribute:

#### Figures

```
.. figure:: figures/confusion_matrix.png
   :name: fig.occlusion.confusion_matrix.front.v2

   Confusion matrix for front-facing camera occlusion detection.

```

#### Tables

```
.. table::
   :name: tbl.kpi.face.yaw_mae.v1

   +---------+---------+
   | Col A   | Col B   |
   +=========+=========+
   | ...     | ...     |
   +---------+---------+

```

**Equivalence**: The `:name:` attribute in standard RST directives is semantically equivalent to the `:id:` field in custom litepub directives. Both forms produce identical canonical AST after normalization.

**Behavior differences**:

| Aspect | Custom directive (`:id:`) | Standard RST (`:name:`) |
|--------|---------------------------|-------------------------|
| Content | Body is caption only; no payload | Syntactically complete but replaced |
| Image path | Not required | Required (will be replaced) |
| Table rows | Forbidden | Allowed (will be replaced) |

**When to use which**:

| Use Case | Recommended Form |
|----------|------------------|
| New documents designed for this pipeline | Custom directives (`:id:`) |
| Existing RST documents being integrated | Standard directives (`:name:`) |
| Documents that must also render outside this pipeline | Standard directives (`:name:`) |

**Note**: When using standard `.. figure::` directives, the image path is required by RST syntax. For computed figures, the path should reference the actual artifact location (e.g., `figures/example.png`). The resolution stage will validate that the referenced file exists.

---

### 3.4 Metric Blocks

Metric blocks represent scalar or small structured values.

```
.. metric::
   :id: metric.face.yaw_mae.v1

   Mean Absolute Error of face yaw estimation (degrees).

```

Rules:

- Descriptive text is authored prose.
- Numeric values are injected programmatically.
- Rendering (inline vs block) is target-dependent.

---

## 4. Prose Blocks

### 4.1 Ordinary Prose (Default)

Most prose requires no special syntax.

```
The yaw estimation error increases at extreme angles due to partial self-occlusion.

```

- No semantic ID
- Fully editable
- No ownership semantics

---

### 4.2 Prose Owner Blocks (Rare, Explicit)

Use only when prose must **own or control** computed content.

```
.. prose::
   :id: prose.yaw_explanation

   The yaw estimation error increases at extreme angles due to partial self-occlusion.

```

Semantics:

- Classified as `role=authored`
- Eligible to own dependent computed blocks
- Removal or hiding of this block removes owned computed blocks

Most prose SHOULD NOT use this.

---

## 5. Hybrid / Annotation Blocks

Hybrid blocks attach editable commentary to computed content.

```
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

- Classified as `role=hybrid`, `kind=annotation`
- Bound to the referenced computed block
- Visibility is inherited
- Removed automatically if the bound block is removed

---

## 6. Ownership and Visibility (Author Perspective)

Authors do **not** manually control visibility in `.rst`.

Ownership rules:

- By default, computed blocks belong to their enclosing section
- Explicit prose owner blocks override structural ownership
- Hybrid annotations are bound to their target computed blocks

Visibility is determined by:

- the analysis registry,
- the build target (`internal`, `external`, `dossier`),
- monotonic condensation rules.

---

## 7. Prohibited Author Actions

Authors MUST NOT:

- Write manual table data inside computed blocks
- Encode provenance, schema, or visibility in directives
- Imply semantic identity via prose placement alone
- Edit computed content in presentation systems

Violations cause validation failure, not silent correction.

---

## 8. Mental Model for Authors (Corrected)

Authors should think:

> “I name what this result means.
> 
> 
> The system knows **how it is produced**, **how it is rendered**, and **when it updates**.”
> 

Authors do **not** describe where data comes from.

They reference meaning; the pipeline handles provenance.

---

## 9. Relationship to Markdown Authoring

- `.rst` and `.md` are **semantically equivalent front-ends**
- Differences are purely syntactic
- Both converge to the same canonical Pandoc AST
- All downstream behavior (validation, replacement, redaction) is identical

---

## 10. Why This Design Works

- `.rst` remains readable and structured
- Semantic identity is explicit but lightweight
- Metadata is centralized and auditable
- AST invariants remain enforceable
- LLM-assisted annotation is possible without corrupting truth

---

### Status

This document defines the **authoritative reStructuredText front-end contract**.

Any change to semantic intent rules MUST be reflected here and in the Markdown Front-End Authoring Conventions.