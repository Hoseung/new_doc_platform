# Resolution Spec — v1

## R1. What Resolution consumes

- **Input AST**: normalized, canonical Pandoc AST (semantic wrapper `Div`s exist; IDs on wrappers)
- **Analysis Artifact Registry**: `aarc-1.0` JSON snapshot + artifact_root
- **Build config**: target profile (`internal|external|dossier`) + strictness limits

## R2. What Resolution produces

- **Output AST**: same AST, but each computed block placeholder is replaced with computed payload nodes.

## R3. Wrapper invariants (non-negotiable)

- Computed content is injected **inside the semantic wrapper `Div`** (the one that carries `id`)
- The wrapper `Div` remains the stable identity boundary (attributes unchanged except optional provenance metadata)
- Authored prose inside wrapper remains untouched

## R4. Placeholder rules (v1 strict)

Inside each computed wrapper `Div`:

- exactly **one** placeholder token must exist (e.g., `[[COMPUTED:METRIC]]`)
- placeholder must be in a block that is “placeholder-only” (typically a `Para` whose inline text equals the token after trimming)
- 0 or >1 placeholders ⇒ build error

## R5. Metric injection canonical form (your decision)

For `metric.json@v1`, injection is a deterministic **2-column table**:

- Table has **1 row**:
    - col1: metric label (string)
    - col2: formatted value string:
        - if `format` exists: render it using `{value}` and `{unit}` (only those tokens; no eval)
        - else: `"{value} {unit}"` if unit present, otherwise `"{value}"`
- Caption is optional:
    - if wrapper contains authored description, do *not* duplicate it
    - if you want caption, use payload `label` as caption only if no prose exists (optional rule; pick one and stick to it)

Determinism:

- fixed table structure (same alignments/width defaults every time)
- stable string conversion for numbers (recommend: Python `Decimal` quantization only if you explicitly want; otherwise `repr(float)` vs `str(float)` ambiguity can bite—use a deterministic formatter)

## R6. Strictness by build target

- `dossier/external`: missing payload, hash mismatch, validation fail ⇒ **hard fail**
- `internal`: you may allow warnings if you want, but the resolver should still be capable of strict mode

---

## Related Documents

- **[Analysis Artifact Registry Contract (AARC)v1.1.md](Analysis%20Artifact%20Registry%20Contract%20(AARC)v1.1.md)** — Registry format specification
- **[Analysis Artifact Payload Specs.v1.md](Analysis%20Artifact%20Payload%20Specs.v1.md)** — Payload format specifications
- **[implementation/02_resolution.md](../implementation/02_resolution.md)** — Resolution implementation guide