```md
# Development Plan — Rendering Stage (v1) with Comprehensive Test Cases

This plan implements rendering from **filtered canonical Pandoc AST** to:
- HTML (Pandoc HTML writer + template + assets + optional Lua filter)
- PDF (Pandoc LaTeX writer + XeLaTeX template + fonts)
- MD/RST exports (Pandoc writers; view-only)

Guiding rules:
- Deterministic builds (pinned versions, stable filenames)
- No network I/O
- Strict safety for `external/dossier`
- Render reports for audit/debug

---

## 0. Deliverables

### D0. Renderers + CLI/API
- `render/` package:
  - `render.api.render(ast, context, config) -> RenderResult`
  - `HtmlRenderer`, `PdfRenderer`, `MdRenderer`, `RstRenderer`
- `render/report.py`: `render_report.json` generator
- `render/pandoc_runner.py`: stable pandoc invocation wrapper (version pinned)
- `render/latex_runner.py`: XeLaTeX wrapper (stable flags; controlled env)

### D1. Templates & assets
- `templates/html/template.html`
- `assets/html/theme.css`
- `assets/html/theme.js` (foldables)
- `templates/latex/template.tex`
- `assets/latex/` (optional: cls, images, etc.)
- `filters/lua/foldable.lua` (optional; recommended)

### D2. Tests
- Unit tests for config, path mapping, report generation
- Integration tests for HTML/PDF output existence and key invariants
- Golden tests for HTML structure (DOM-level) and for LaTeX intermediate output
- Smoke tests for PDF generation (non-empty, stable metadata rules)

---

## 1. Module skeleton

```
```
docplatform/

render/
__init__.py
api.py
context.py
config.py
result.py
report.py
pandoc_runner.py
latex_runner.py
assets.py

html/
__init__.py
renderer.py
lua/
foldable.lua
templates/
template.html

assets/
theme.css
theme.js

pdf/
__init__.py
renderer.py
templates/
template.tex

assets/
# optional cls/fonts manifests

text/
__init__.py
md_renderer.py
rst_renderer.py

tests/
test_render_config.py
test_pandoc_runner.py
test_html_render_smoke.py
test_html_foldable_mapping.py
test_pdf_render_smoke.py
test_pdf_cjk_smoke.py
test_pdf_no_raw_strict.py
test_md_export.py
test_rst_export.py

fixtures/
ast_minimal.json
ast_with_wrappers.json
ast_with_foldables.json
ast_with_codeblocks.json
ast_with_appendix.json
ast_with_korean.json
ast_with_tables.json
ast_with_links.json

expected/

html/

latex/

```
---

## 2. Foundation tasks (do first)

### Task 2.1 — RenderContext & RenderConfig
Implement:
- `BuildContext` (reuse existing):
  - build_target: internal|external|dossier
  - render_target: html|pdf|md|rst
  - strict: bool (forced true for external/dossier)
- `RenderConfig`:
  - `output_dir`
  - `pandoc_path`
  - `pandoc_required_version`
  - `html_template_path`
  - `html_assets_dir`
  - `html_lua_filters: list[path]` (optional)
  - `latex_template_path`
  - `latex_engine` = xelatex
  - `latex_engine_path`
  - `latex_runs` (1–3; pinned)
  - writer flags: `html_writer_options`, `latex_writer_options`, etc.

Acceptance checklist:
- [ ] config serializable (for report)
- [ ] strict mode toggles safety flags in pandoc
- [ ] all file paths resolved deterministically (no relative ambiguity)

### Task 2.2 — Pandoc runner wrapper
Implement `pandoc_runner.run(input_ast_json, to_format, options, template, lua_filters, output_path)`:
- writes input ast to temp path with stable name (hash-based), not timestamp
- invokes pandoc with:
  - `--from=json`
  - `--to=html5` or `--to=latex` or `--to=gfm` or `--to=rst`
  - `--template`
  - `--lua-filter` (if any)
- captures stdout/stderr
- fails with rich error message and report entry

Acceptance checklist:
- [ ] enforces pandoc version pinning (fail if mismatch)
- [ ] no network calls
- [ ] stable ordering of args

### Task 2.3 — Render report
Implement `render_report.json` with:
- tool versions (pandoc, xelatex)
- template paths + file hashes
- assets dir hash or manifest hash
- build context snapshot
- warnings/errors list
- output artifact list

Acceptance checklist:
- [ ] report is deterministic
- [ ] includes enough to reproduce build

---

## 3. HTML Renderer (v1)

### Objective
Convert AST → HTML with foldables + stable anchors + theme.

### Task 3.1 — HTML template + assets
- Implement `template.html` with placeholders:
  - title, TOC placeholder, body, CSS, JS
- `theme.css` baseline:
  - typography, tables, code blocks, wrapper styling
- `theme.js` baseline:
  - optional: add anchor link icons
  - optional: copy-code button (can be v2)

Acceptance checklist:
- [ ] template works with pandoc output
- [ ] CSS/JS copied into output alongside HTML

### Task 3.2 — Foldables mapping
Preferred approach: Lua filter `foldable.lua`
- Transform Div class `foldable` (and optionally `foldable-code`) into:
  - HTML `<details>` with `<summary>`
- Preserve semantic wrapper IDs and nested content

Acceptance checklist:
- [ ] foldables rendered as `<details>`
- [ ] collapsed state derived from `data-collapsed`

### Task 3.3 — Stable anchors
- Ensure wrapper `id` attributes survive in HTML output
- Ensure appendix anchors survive

Acceptance checklist:
- [ ] `id="tbl...."` appears in HTML as an anchor
- [ ] internal links resolve to anchors

### HTML test cases (comprehensive)
#### Unit tests
- [ ] `pandoc_runner` called with `--to=html5`, template, lua filters
- [ ] assets copied to output dir deterministically
- [ ] report includes template hash + assets hash

#### Integration tests (HTML output)
1) **Minimal doc**
- Input: `ast_minimal.json`
- Assert: output html exists, contains `<html>` and body content

2) **Foldable container**
- Input: `ast_with_foldables.json`
- Assert:
  - contains `<details`
  - contains `<summary>` with expected title
  - foldable content present

3) **Code block**
- Input: `ast_with_codeblocks.json` (with folded wrappers)
- Assert:
  - code appears
  - wrapper class present

4) **Anchors**
- Input: `ast_with_wrappers.json`
- Assert:
  - HTML contains id for each wrapper semantic ID
  - links reference correct anchors

5) **No raw in strict**
- Input contains RawInline/RawBlock (if you keep such fixture)
- Context: external strict
- Assert: render fails OR sanitizes according to policy (prefer fail)

6) **Korean text**
- Input: `ast_with_korean.json`
- Assert: output contains Korean text intact

---

## 4. PDF Renderer (v1)

### Objective
AST → LaTeX → PDF with XeLaTeX, CJK support, stable links, appendix, and safe strict mode.

### Task 4.1 — LaTeX template
Create `template.tex`:
- `fontspec` + CJK font support:
  - set main font (English)
  - set CJK font fallback (Korean)
  - set monospaced font
- configure:
  - hyperref
  - geometry
  - tables (longtable/booktabs as needed)
  - code blocks (listings; minted only if you intentionally manage pygments)

Acceptance checklist:
- [ ] template builds a simple PDF with Korean + English
- [ ] links clickable

### Task 4.2 — XeLaTeX runner wrapper
Implement `latex_runner.build(latex_path, pdf_path, runs=2)`:
- controlled env, stable flags
- capture logs
- fail with clear error summary

Acceptance checklist:
- [ ] deterministic run count
- [ ] stable output filenames
- [ ] logs stored in output dir for debugging

### Task 4.3 — Strict mode defenses
For external/dossier:
- pass pandoc options that avoid raw latex
- optionally re-scan produced latex for `\begin{verbatim}`? (not needed if validator is solid)
- fail on detection of raw blocks if you still allow them internally

Acceptance checklist:
- [ ] strict build rejects raw latex injection attempts

### PDF test cases (comprehensive)

#### Unit tests
- [ ] pandoc invoked with `--to=latex` and template
- [ ] xelatex invoked with stable flags
- [ ] report includes xelatex version + template hash

#### Integration tests
1) **Minimal PDF**
- Input: `ast_minimal.json`
- Assert:
  - PDF file exists
  - size > minimal threshold (e.g., > 5 KB)

2) **Korean + English**
- Input: `ast_with_korean.json`
- Assert:
  - PDF generated successfully (smoke)
  - optional: extract text via `pdftotext` and confirm Korean appears (if tooling available)

3) **Appendix**
- Input: `ast_with_appendix.json`
- Assert:
  - LaTeX intermediate contains “Appendix” heading
  - PDF generated
  - optional: `pdftotext` includes appendix headings

4) **Externalized code stub**
- Input: contains code stub blocks (from presentation filter)
- Assert:
  - PDF generated
  - LaTeX contains hyperlink markup for stub link

5) **Tables**
- Input: `ast_with_tables.json`
- Assert:
  - PDF generated
  - LaTeX contains `\begin{longtable}` or tabular depending on options
  - no compilation errors

6) **No raw in strict**
- Input: fixture with RawBlock
- Context: dossier strict
- Assert: build fails with clear message

---

## 5. Markdown and reStructuredText export renderers (v1)

### Objective
Provide view-only exports, preserving IDs where feasible.

### Task 5.1 — Markdown export
- Pandoc writer to `gfm` or chosen markdown flavor
- Ensure:
  - no placeholders
  - wrapper IDs preserved using fenced Divs or HTML comments (policy decision)

Tests
1) Minimal md export exists
2) Wrapper IDs appear (as `::: {#id}` or comment fences)
3) Korean preserved

### Task 5.2 — RST export (best effort)
- Pandoc writer to rst
- No strict fidelity guarantees; treat as export view

Tests
1) rst export exists
2) Basic headings and paragraphs exported
3) No placeholders remain

---

## 6. Cross-cutting test matrix

Run the same AST fixture under multiple contexts:

Contexts:
- internal/html (non-strict)
- external/html (strict)
- dossier/html (strict)
- internal/pdf
- external/pdf
- dossier/pdf
- internal/md
- external/md (if you export)
- internal/rst (optional)

Assertions:
- [ ] deterministic outputs (hash stable) when toolchain pinned
- [ ] strict mode rejects raw content
- [ ] metadata stripping is reflected only by filters (not renderer)
- [ ] render report generated for every run

---

## 7. Golden testing strategy

### 7.1 Recommended goldens
- For HTML: golden test the **DOM invariants**, not full HTML bytes:
  - presence of `<details>` for foldables
  - presence of anchors for wrapper IDs
  - presence of CSS/JS includes
- For LaTeX: golden test the intermediate `.tex` (more stable than PDF bytes)
  - no timestamps
  - contains appendix heading
  - contains hyperref for links

### 7.2 Determinism checks
- Record tool versions in CI
- Pin template and assets hashes
- Compare:
  - HTML normalized DOM snapshot (e.g., strip whitespace)
  - LaTeX `.tex` file exact match (after normalizing line endings)

---

## 8. Milestones

### M1 — Pandoc runner + reports
- pandoc wrapper, version pinning, render report

### M2 — HTML renderer shipped
- template/assets + foldables lua filter + smoke tests

### M3 — PDF renderer shipped
- LaTeX template + XeLaTeX wrapper + CJK smoke tests

### M4 — MD/RST exports
- stable view exports + basic tests

### M5 — Full test matrix + goldens
- run matrix across targets + strict mode enforcement

---

## 9. Non-goals (v1)
- Site generator features (nav, search indexing, multi-page)
- Executing code cells (Quarto-style)
- Auto-summarization during rendering
- Byte-identical PDFs across OS/toolchain variants (test LaTeX instead)

---
```
