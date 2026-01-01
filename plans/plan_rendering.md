# rendering.md — Rendering Stage Specification (v1, updated: HTML Site Mode)

## 0. Purpose

Rendering is the **backend** of the documentation platform: it converts a **filtered canonical Pandoc AST** into target formats:

- **HTML** (single-page document OR multi-page static site)
- **PDF** (official delivery, via LaTeX engine)
- **Markdown / reStructuredText** (optional “view exports”, not canonical)

Rendering MUST be:
- **Deterministic** given the same input AST, renderer version, templates, and config
- **Safe**: no network I/O; no execution of untrusted embedded raw content in strict targets
- **Themeable** via templates/assets (HTML/CSS/JS, LaTeX class/packages)

---

## 1. Rendering in the overall pipeline

Pipeline (simplified):

```

Normalize -> Resolve -> Validate -> Filter -> Render -> Publish/Sync (optional)

```

Rendering assumes:
- Placeholders are resolved
- Validation already enforced AST invariants and safety constraints
- Filtering already applied target-specific removals + presentation shaping

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
- HTML single-page:
  - `output.html` (+ assets)
- HTML site:
  - output directory containing multiple `.html` pages + `sitemap.json` + assets
- PDF:
  - `output.pdf`
- MD/RST:
  - `output.md` / `output.rst`
- `render_report.json` (recommended):
  - renderer versions
  - template names/hashes
  - warnings/errors summary

---

## 3. Rendering strategy: Pandoc writers as backends

### 3.1 Principle (v1)
Rendering SHOULD use **Pandoc writers**:
- HTML (single): Pandoc `html5` writer + template + assets
- HTML (site): Pandoc `chunkedhtml` writer + template + assets :contentReference[oaicite:0]{index=0}
- PDF: Pandoc `latex` writer + custom LaTeX template + XeLaTeX
- MD/RST: Pandoc writers for convenience exports

### 3.2 Version pinning (normative)
Pandoc MUST be version-pinned by the build system to ensure stable output.

Renderer MUST record:
- `pandoc_version`
- `latex_engine_version` (PDF)
- template and asset hashes (recommended)

---

## 4. Render targets

# 4.1 HTML rendering

HTML rendering supports two modes over the **same filtered AST**:

- `html_mode = single` → one HTML file (sequential document)
- `html_mode = site` → multi-page static site (“chunked HTML”)

This does not change the canonical model. It is purely a rendering backend choice.

---

## 4.1.1 HTML mode: single-page

### Overview
Uses:
- Pandoc HTML writer (`--to=html5`)
- Project template (`template.html`)
- CSS theme (`theme.css`)
- JS behavior (`theme.js`) for interactive features (foldables)

### Foldables contract (v1)
Presentation filter may output foldables as:
- `Div` with class `foldable`
- attributes:
  - `data-title`: string (required)
  - `data-collapsed`: `true|false` (optional; default true)

Renderer SHOULD map foldables to semantic HTML behavior (recommended mapping: `<details><summary>…`). This is best done via a Pandoc Lua filter (render-time) rather than post-processing HTML.

### Anchors and stable IDs
Renderer MUST preserve:
- wrapper `id` attributes as HTML anchors
- appendix anchors produced by presentation filter

---

## 4.1.2 HTML mode: static site (chunked HTML)

### Overview
Uses Pandoc’s `chunkedhtml` writer: it produces **linked HTML files**, one per section, adjusts internal links automatically, adds navigation links, and includes a `sitemap.json` describing the hierarchy. :contentReference[oaicite:1]{index=1}

Invocation conceptually:
- `--to=chunkedhtml`
- `--split-level=N` (where to split) :contentReference[oaicite:2]{index=2}
- `--chunk-template=...` (stable filenames) :contentReference[oaicite:3]{index=3}

### Output shape (normative)
Pandoc `chunkedhtml` produces a zip by default; if -o is a path **without an extension**, Pandoc treats it as a directory and unpacks the output there (error if directory exists). :contentReference[oaicite:4]{index=4}

Required site artifacts:
- `index.html` (top page)
- multiple section pages (`*.html`)
- `sitemap.json` :contentReference[oaicite:5]{index=5}
- theme assets (CSS/JS/fonts) copied alongside, under a stable relative path

### Split policy (normative)
`--split-level=NUMBER` determines how much content goes into each chunk (default split at level-1 headings). :contentReference[oaicite:6]{index=6}

Recommended defaults:
- one page per chapter: `split_level=1`
- one page per section: `split_level=2`

### Filename stability (normative)
Use `--chunk-template=PATHTEMPLATE` to control filenames. In the template:
- `%n` chunk number
- `%s` section number
- `%h` heading text
- `%i` section identifier
Default is `%s-%i.html`. :contentReference[oaicite:7]{index=7}

**Strong recommendation:** base filenames primarily on `%i` (identifier), not `%h` (heading text), to keep URLs stable when titles change.

### Heading identifiers (recommended contract)
Chunked HTML uses **section identifiers** (`%i`) derived from headings. To ensure stable URLs:
- Authors SHOULD provide explicit stable IDs for chapter/section headings, OR
- Normalization SHOULD inject stable IDs for top-level headings derived from source structure (if applicable)

This does not alter semantics; it only stabilizes navigation.

### Template behavior and TOC
Chunked HTML adds navigation links and can be customized by adjusting the template. By default, TOC is included only on the top page; to include it on every page, set the `toc` variable in the template. :contentReference[oaicite:8]{index=8}

### Foldables in site mode
Foldables contract remains identical:
- presentation filter emits foldable Divs
- render-time Lua filter converts to `<details>` per page

### Assets in site mode (normative)
- Renderer MUST NOT fetch remote resources.
- Assets MUST be local files copied into the output directory under a deterministic location (e.g., `_assets/`).
- HTML pages must reference assets with relative paths.

---

## 4.2 PDF rendering (via LaTeX)

### Overview
Uses:
- Pandoc LaTeX writer
- XeLaTeX engine
- LaTeX template (custom)
- Font configuration supporting Korean + English

### Requirements (normative)
- MUST support Korean + English correctly.
- MUST avoid raw LaTeX injection in strict targets unless explicitly allowed.
- MUST render links as clickable hyperlinks.

Appendix and code-stub behaviors are governed by the Presentation Filter; PDF rendering must faithfully render those transformed structures.

---

## 4.3 Markdown / reStructuredText exports

### Purpose
MD/RST exports are **views**, not canonical sources. They are intended for:
- diff-friendly review outputs
- lightweight text-form distribution
- patch proposal workflows

### Requirements
- MUST not reintroduce placeholders
- SHOULD preserve wrapper IDs as best as possible
- RST export is best-effort (no strict fidelity guarantee)

---

## 5. Renderer interface (implementation contract)

### 5.1 API
Renderer exposes:

```

render(ast, build_context, render_config) -> RenderResult

```

`RenderResult` includes:
- output file(s)/directory
- render report
- warnings/errors

### 5.2 RenderConfig (required fields)
Common:
- `output_dir`
- `pandoc_path` + pinned version check
- writer options per target

HTML-specific:
- `html_mode`: `single|site`
- `html_template_path`
- `html_assets_dir`
- `html_lua_filters: list[path]` (recommended)
- `html_site_split_level` (site mode) :contentReference[oaicite:9]{index=9}
- `html_site_chunk_template` (site mode) :contentReference[oaicite:10]{index=10}

PDF-specific:
- `latex_template_path`
- `latex_engine` = `xelatex`
- engine path + run count

### 5.3 Determinism rules
- No network I/O
- Stable file naming (no timestamps)
- Stable asset bundling and paths
- Sort any generated lists (e.g., assets manifest)

---

## 6. Recommended implementation approach (v1)

### 6.1 One renderer per target, shared backend
- `HtmlRenderer`:
  - single mode: `--to=html5`
  - site mode: `--to=chunkedhtml` + `--split-level` + `--chunk-template` :contentReference[oaicite:11]{index=11}
  - apply Lua filter(s) for foldables mapping
  - copy assets into output
- `PdfRenderer`: `--to=latex` then XeLaTeX
- `MdRenderer`: Pandoc Markdown writer
- `RstRenderer`: Pandoc RST writer

### 6.2 Render-time Lua filters (recommended)
Lua filters are allowed because they are deterministic and local. Use them for:
- foldable mapping (Div → `<details>` in HTML modes)
- optional CSS class injection for computed wrappers

---

## 7. Safety requirements (strict targets)

For `build_target in {external, dossier}`:
- strict mode MUST prevent raw HTML/LaTeX injection from content
- renderer may re-check and fail fast as defense-in-depth

(Primary enforcement remains in Validation.)

---

## 8. Reporting

Renderer SHOULD emit `render_report.json` including:
- tool versions
- template + assets hashes
- `html_mode` (single/site)
- if site mode: `split_level`, `chunk_template`, and list of generated pages
- warnings/errors

---

## 9. Acceptance checklist (v1)

### HTML (single)
- [ ] foldables render as collapsible blocks
- [ ] anchors stable for semantic wrapper IDs
- [ ] template + assets applied
- [ ] no network calls

### HTML (site)
- [ ] output directory contains multiple HTML pages
- [ ] `sitemap.json` present :contentReference[oaicite:12]{index=12}
- [ ] navigation links work
- [ ] internal links adjusted correctly :contentReference[oaicite:13]{index=13}
- [ ] filenames stable via `--chunk-template` :contentReference[oaicite:14]{index=14}
- [ ] no network calls

### PDF
- [ ] Korean + English render correctly
- [ ] appendix renders and links work
- [ ] externalized code stubs hyperlink correctly
- [ ] no raw LaTeX injection in strict builds

### MD/RST
- [ ] no placeholders
- [ ] wrapper IDs preserved as best possible
- [ ] deterministic output
```
