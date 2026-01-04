# 005_rendering.md — Rendering Stage Specification (v1)

## 0. Purpose

Rendering is the **backend** of the documentation platform: it converts a **filtered canonical Pandoc AST** into target formats:

- **HTML** (primary for web viewing)
- **PDF** (primary for official delivery, via LaTeX engine)
- **Markdown / reStructuredText** (optional “view exports”, not canonical)

Rendering MUST be:
- **Deterministic** given the same input AST, renderer version, templates, and config
- **Safe**: no network I/O; no execution of untrusted embedded raw content in strict targets
- **Themeable** via templates/assets (HTML/CSS/JS, LaTeX class/packages)

> **Note: Sphinx-specific RST directives are not supported.**
> This pipeline uses Pandoc as the parsing and rendering backend, not Sphinx.
> Sphinx-only constructs such as `toctree`, `:ref:`, `:doc:`, `genindex`, `search`,
> and other Sphinx domain directives will either be ignored or rendered as plain text.
> For table of contents, use Pandoc metadata (`toc: true`) or template-level TOC generation.
> For cross-references, use standard RST or Markdown link syntax.

---

## 1. Rendering in the overall pipeline

Pipeline (simplified):

Authoring (.md/.rst)

- > Parse
- > Adapter
- > Normalization
- > Resolution
- > Validation
- > Filtering
- > Rendering <-- this document
- > Publish/Sync (optional)

Rendering assumes:
- Placeholders are already resolved
- Validation already guaranteed AST invariants and safety constraints
- Filtering already applied target-specific removals and presentation shaping

---

## 2. Inputs and outputs

### 2.1 Inputs
- `filtered_ast`: canonical Pandoc AST (JSON or internal model)
- `BuildContext`:
  - `build_target`: `internal | external | dossier`
  - `render_target`: `html | pdf | md | rst`
  - `strict`: bool (external/dossier MUST be strict)
- `RenderConfig`:
  - template selection
  - theme assets selection
  - PDF engine selection and font config
  - output paths

### 2.2 Outputs
- `output_artifact`:
  - HTML: `.html` (+ assets folder)
  - PDF: `.pdf`
  - MD: `.md`
  - RST: `.rst`
- `render_report.json` (recommended):
  - renderer versions
  - template names/hashes
  - warnings/errors summary

---

## 3. Rendering strategy: Pandoc writer as backend

### 3.1 Principle (v1)
The rendering backend SHOULD use **Pandoc writers**:
- HTML: Pandoc `html5` writer + template + assets
- PDF: Pandoc `latex` writer + custom LaTeX template + XeLaTeX
- MD/RST: Pandoc writers for convenience exports

This avoids reimplementing a full converter while retaining full control via:
- AST transformations (filters)
- Templates (HTML/LaTeX)
- Lightweight render-time transforms (optional)

### 3.2 Version pinning (normative)
Pandoc MUST be version-pinned by the build system to ensure stable output.

Renderer MUST record:
- `pandoc_version`
- `latex_engine_version` (for PDF)
- template and asset hashes (recommended)

---

## 4. Render targets

## 4.1 HTML rendering

### 4.1.1 Overview
HTML rendering uses:
- Pandoc HTML writer
- A project template (`template.html`)
- CSS theme (`theme.css`)
- JS behavior (`theme.js`) for interactive features:
  - foldable blocks
  - code copy buttons (optional)
  - anchor links (optional)

### 4.1.2 Foldables contract (v1)
Presentation filter may output “foldable containers” as:

- `Div` with class `foldable`
- attributes:
  - `data-title`: string (required)
  - `data-collapsed`: `true|false` (optional; default true)

Renderer MUST map foldables to HTML with semantic behavior.
Recommended mapping:
- `<details open?>` container
- `<summary>data-title</summary>`
- foldable content inside

> Implementation options:
> - Pandoc Lua filter applied at render-time to rewrite foldable Divs
> - Or post-process HTML DOM (less preferred; harder to keep deterministic)

### 4.1.3 Code blocks contract
HTML SHOULD preserve code blocks inline and allow folding (presentation filter may wrap them).

If presentation filter outputs code-fold wrappers:
- class `foldable-code` or reuse `foldable`
- renderer must respect it

No network I/O for code externalization in HTML; code remains local content.

### 4.1.4 Anchors and stable IDs
Renderer MUST preserve:
- wrapper `id` attributes as HTML anchors
- appendix anchors produced by presentation filter

Rule:
- semantic wrapper id `tbl.*` must become a stable `id` in the output DOM, so hyperlinks remain stable across builds.

### 4.1.5 Required assets
- `theme.css` (layout + typography)
- `theme.js` (foldables; optional copy buttons)

### 4.1.6 HTML template contract
Template MUST provide placeholders:
- document title
- table of contents (optional)
- body content
- link tags for CSS
- script tags for JS

Template SHOULD support:
- embedding a TOC
- optional sidebar
- optional build metadata footer (internal only)

---

## 4.2 PDF rendering (via LaTeX)

### 4.2.1 Overview
PDF rendering uses:
- Pandoc LaTeX writer
- XeLaTeX engine
- LaTeX template (custom)
- Font configuration supporting Korean + English

### 4.2.2 Requirements (normative)
- PDF renderer MUST support CJK text (Korean) correctly.
- PDF renderer MUST avoid raw LaTeX injection in strict targets unless explicitly allowed.
- Code blocks should be rendered with monospaced fonts and line wrapping / overflow handling.

### 4.2.3 Appendix contract
Presentation filter may relocate blocks to an Appendix section.
PDF renderer MUST:
- render appendix with correct sectioning
- preserve anchor references (links within PDF)

### 4.2.4 Externalized code blocks (PDF)
Presentation filter may replace long code blocks with link stubs.
PDF renderer MUST:
- render link stubs as clickable hyperlinks
- optionally render a short preview block (if present)

Important: PDF renderer MUST NOT attempt to fetch remote content.

### 4.2.5 LaTeX template contract (v1)
Template MUST define:
- page geometry and margins
- fonts:
  - English main font
  - Korean font (fallback / main)
  - monospaced code font
- table rendering behavior:
  - longtable support if needed
  - sane default alignment and font size

Template SHOULD:
- include hyperref
- include unicode-friendly packages
- configure listings or minted (minted requires Python/Pygments; prefer listings for determinism)

---

## 4.3 Markdown / reStructuredText exports

### 4.3.1 Purpose
MD/RST exports are **views**, not canonical sources.
They are intended for:
- diff-friendly review outputs
- lightweight external sharing in text form
- patch proposal workflows

### 4.3.2 Requirements
- Export MUST preserve semantic wrapper IDs as best as possible
- Export MAY degrade layout fidelity
- Export MUST NOT reintroduce placeholders

### 4.3.3 Writer configuration
- For Markdown: prefer Pandoc Markdown with a pinned variant (`gfm` vs `commonmark` vs `markdown+...`)
- For RST: treat as best-effort export only

---

## 5. Renderer interface (implementation contract)

### 5.1 API
Renderer exposes a single call:


render(ast, build_context, render_config) -> RenderResult


Where `RenderResult` includes:
- output file(s)
- render report
- warnings/errors

### 5.2 RenderConfig
Required fields:
- `output_dir`
- `template` (per render_target)
- `assets_dir` (HTML)
- `latex_engine` = `xelatex` (v1)
- `pandoc_path` and pinned version check
- `writer_options` (format-specific flags)

### 5.3 Determinism rules
- No network I/O
- Stable file naming (no timestamps)
- Stable asset bundling and paths
- Sort any generated lists (e.g., asset file lists)

---

## 6. Recommended implementation approach (v1)

### 6.1 One renderer per target, shared backend
- `HtmlRenderer`: calls pandoc writer with html template + assets
- `PdfRenderer`: calls pandoc writer to LaTeX, then XeLaTeX (or Pandoc direct PDF if you prefer)
- `MdRenderer`: pandoc markdown writer
- `RstRenderer`: pandoc rst writer (best effort)

### 6.2 Optional: render-time Lua filters
Use Lua filters for HTML/PDF to perform last-mile mapping:
- foldable Div -> details/summary for HTML
- optional wrappers for computed blocks (e.g., add CSS classes around tables/figures)

Lua filters are acceptable because:
- deterministic
- run locally
- closer to Pandoc’s node model

---

## 7. Safety requirements (strict targets)

For `build_target in {external, dossier}`:
- `allow_raw_pandoc` MUST be false
- HTML renderer MUST sanitize or reject raw HTML injection
- LaTeX renderer MUST not accept raw LaTeX blocks

(Validation stage should have enforced this already; rendering may re-check as defense-in-depth.)

---

## 8. Theming

### 8.1 HTML theme
Themes are:
- `theme.css`
- `theme.js`
- optional fonts

Theme selection should be config-driven.

### 8.2 PDF theme
Themes are:
- LaTeX template
- font selection
- package options

---

## 9. Reporting

Renderer SHOULD emit `render_report.json`:
- pandoc version
- latex engine version
- template hash
- theme asset hash
- warnings (e.g., missing fonts)
- output artifact path(s)

This report is especially useful for internal builds and audit trails.

---

## 10. Acceptance checklist (v1)

### HTML
- [ ] foldables render as collapsible blocks
- [ ] code folds work (if present)
- [ ] anchors stable for semantic wrapper IDs
- [ ] no network calls
- [ ] template + assets applied

### PDF
- [ ] Korean + English render correctly
- [ ] appendix renders and links work
- [ ] externalized code stubs hyperlink correctly
- [ ] tables render with acceptable layout
- [ ] no raw LaTeX injection in strict builds

### MD/RST
- [ ] no placeholders
- [ ] wrapper IDs preserved as best possible
- [ ] deterministic output

---

## 11. Related Documents

- **[Appendix_HTML_Theming_Contract.md](Appendix_HTML_Theming_Contract.md)** — HTML theming specification
- **[Appendix_PDF_Theming_Contract.md](Appendix_PDF_Theming_Contract.md)** — PDF theming specification
- **[implementation/05_rendering.md](../implementation/05_rendering.md)** — Rendering implementation guide