# Canonical Model & Contracts

**Pandoc AST as Canonical Representation**

---

## 1. Purpose

This document defines the **canonical representation**, **identity model**, and **update contracts** for the documentation operating system.

Its goals are:

- Deterministic generation of quantitative elements from analysis outputs
- Stable semantic identity for tables and figures across revisions and transports
- Safe round-tripping through external presentation systems (e.g., Confluence)
- Controlled human / LLM edits that do not corrupt quantitative truth

This document defines **what must be true** of documents and transformations, independent of implementation details.

---

## 2. Canonical Representation

- The canonical representation of all documents is the **Pandoc AST**.
- Source formats (`.rst`, `.md`, etc.) are treated as ingestion formats only.
- All transformations, validation, filtering, and synchronization operate on the AST.
- The canonical AST must be serializable into Pandoc JSON for inspection, diffing, and validation.

---

## 3. Semantic Identity

### **3.1 Rationale**

- Git provides version history, not semantic identity.
- Stable semantic identifiers are required to:
    - update quantitative elements across document revisions
    - synchronize with external presentation systems (e.g., Confluence)
    - distinguish meaning from layout and ordering

### **3.2 Identified Elements**

The following elements must carry semantic IDs:

- Computed tables
- Computed figures
- Metric blocks (where a metric definition or value is presented)
- Optionally, sections/headings for stable anchors

### **3.3 Semantic ID Properties**

A semantic ID must be:

- Stable across minor edits and reordering
- Unique within the document
- Human-readable and deterministic
- Explicitly versioned when meaning or structure changes

Example:

```
tbl.kpi.face.yaw_mae.v1
fig.occlusion.confusion_matrix.front.v2

```

### 3.4 Where IDs Live in Pandoc AST

Semantic IDs are stored using Pandoc-supported identifiers and attributes.

Preferred storage:

- Native element identifiers (where supported)
- Otherwise, wrapper containers (`Div` / `Span`) with attributes

**Canonical attributes:**

| Attribute | Meaning |
| --- | --- |
| `id` | Semantic identifier (required) |
| `role` | `computed` | `authored` | `hybrid` |
| `source` | Reference to analysis artifact (required for computed) |
| `schema` | Table schema or metric version (required for computed tables) |
| `visibility` | `internal` | `external` | `dossier` |
| `lock` | `true` for computed blocks (default) |

---

## 4. Content Roles and Locking

All document content is classified as one of:

- **Authored**: human-written prose
- **Computed**: generated deterministically from analysis results
- **Hybrid**: computed core with explicitly defined annotation zones

### **4.1 Locking Rules**

- Computed blocks are **locked by default**
- Locked blocks are always regenerated and overwrite downstream edits
- Edits to locked blocks may be *detected and flagged* during ingestion, but are never preserved
- Locking exists to protect semantic correctness, not to restrict presentation styling

---

## 5. Table Contract

### **5.1 Table Generation Model**

- All computed tables are generated as complete units from analysis outputs
- Partial updates, row-level edits, or append-only behavior are **not supported**

### **5.2 Validation Requirements**

Each computed table must declare:

- Semantic ID
- Schema (column names, units, types)
- Source analysis artifact
- Completeness invariant (table must be fully generated or rejected)

If a table cannot be generated fully and consistently, the build must fail.

This enforces the principle:

> Partial correctness is worse than no result.
> 

---

## 6. Figure Contract

### **6.1 Semantic Nature of Figures**

- Figures are semantic representations of analysis results, not fixed visual artifacts
- Exact pixel reproduction is not required or expected

### **6.2 Figure Identity**

Each computed figure must declare:

- Semantic ID
- Source analysis artifact
- Semantic role (what the figure represents)

### **6.3 Non-Contractual Properties**

The following are explicitly *not* part of the canonical contract:

- Color palette
- Aspect ratio
- Resolution
- Typography
- Layout

These belong to the presentation/theming layer.

---

## 7. Confluence Synchronization Policy

> **Note**: This section defines the policy contract for Confluence synchronization. Implementation of the sync mechanism is **deferred to a future version**. The policy is documented here to establish the contract that any future implementation must follow.

- Confluence is a **presentation front-end**, not the canonical source
- Canonical documents live in the repository and AST
- Confluence edits are treated as **patch proposals**

**Allowed Patches**

- Edits to authored prose
- Comments or annotations in designated zones

**Disallowed Patches**

- Modifications to computed tables
- Modifications to computed figures
- Changes that violate visibility or redaction rules

**Patch Handling**

- Illegal edits may be detected and reported
- Computed blocks are always overwritten during regeneration
- LLMs may assist in applying prose patches, but only within allowed zones

---

## 8. Redaction and Visibility Contract

Visibility filtering is driven by explicit metadata (`visibility`) and build targets.

The system enforces **monotonic condensation**:

```
Internal →External → Dossier
```

Downstream documents may not introduce new analytical results absent upstream.

---

## 9. Validation Requirements

The build pipeline must validate:

- absence of duplicate semantic IDs
- presence of required metadata for computed blocks
- rejection of Confluence patches touching locked blocks
- compliance with visibility and redaction rules

Validation failures are build failures, not warnings.

---

## 10. Related Documents

- **[ast_invariants.md](ast_invariants.md)** — Detailed AST invariants by pipeline stage
- **[normalization_v1.md](normalization_v1.md)** — Normalization specification
- **[filter_design.md](filter_design.md)** — Visibility and policy filtering