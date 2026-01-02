# Development Plan — HTML Theming (v1) for LitePub

Goal: ship a **sane, stakeholder-familiar** HTML theming system with **three layout families**, without trying to be “compatible with every Sphinx theme”.

We will implement:
1) A **stable HTML skeleton** (DOM contract) once
2) Three **theme packs** that style that skeleton:
   - `sidebar_docs` (RTD/PyData/Furo family)
   - `topbar_classic` (Python docs family)
   - `book_tutorial` (Sphinx-book/JupyterBook family)
3) Build-script selection:
   - `--html-theme sidebar_docs|topbar_classic|book_tutorial`
4) Deterministic packaging (single-page and site mode)

Non-goal: “install any pip Sphinx theme and it just works.”

---

## 0. Deliverables

### D0. Theme API + resolver
- `themes/` directory with:
  - `base/` theme (skeleton + minimal CSS)
  - `sidebar_docs/`
  - `topbar_classic/`
  - `book_tutorial/`
- Theme resolver:
  - `resolve_theme(theme_id) -> ThemeBundle(template_path, assets_dir, manifest)`
- Renderer integration:
  - `RenderConfig.with_theme(theme_id)` or CLI `--html-theme`

### D1. Template + assets
Each theme pack includes:
- `template.html`
- `assets/theme.css`
- `assets/theme.js` (optional; recommended)
- optional `theme.json` manifest

### D2. Tests
- Unit tests: theme resolution, manifest parsing, asset copying, config wiring
- Integration tests: render HTML for single-page and site mode per theme
- Golden tests: DOM invariants + stable hook points

---

## 1. Implementation layout (suggested)

```

docplatform/
theming/
**init**.py
contract.py         # constants: required ids/classes
manifest.py         # theme.json parsing (optional)
resolver.py         # find theme on disk, validate pack
bundler.py          # copy assets, compute hashes
selection.py        # RenderConfig.with_theme(...)
render/
html/
renderer.py       # uses theming resolver + pandoc runner
templates/        # optional fallback
themes/
base/
template.html
assets/theme.css
assets/theme.js
theme.json
sidebar_docs/
template.html
assets/theme.css
assets/theme.js
theme.json
topbar_classic/
template.html
assets/theme.css
assets/theme.js
theme.json
book_tutorial/
template.html
assets/theme.css
assets/theme.js
theme.json
tests/
test_theme_resolver.py
test_theme_validation.py
test_theme_asset_copy.py
test_render_html_single_theme_matrix.py
test_render_html_site_theme_matrix.py
fixtures/ast_small.json
fixtures/ast_with_toc.json
fixtures/ast_with_wrappers.json
fixtures/ast_with_codeblocks.json
fixtures/ast_with_foldables.json

```

---

## 2. Phase 1 — Define the stable HTML skeleton (DOM contract)

### Task 2.1 — Choose stable hook points (IDs/classes)
Define a minimal, stable skeleton that all themes can style:

Required IDs:
- `lp-header`
- `lp-nav` (topbar or empty)
- `lp-sidebar` (sidebar or empty)
- `lp-toc` (optional; can be inside sidebar)
- `lp-content` (main content container)
- `lp-footer`

Required classes (semantic blocks):
- `.computed-table`
- `.computed-figure`
- `.computed-metric`
- `.foldable` (if foldables are used)

Acceptance checklist:
- [ ] hook points exist in all templates
- [ ] themes may choose to hide/relayout nav/sidebar but must not remove `lp-content`

### Task 2.2 — Document the contract (1-page spec)
Create `docs/theming_contract.md` (short) describing:
- required IDs/classes
- what can be omitted (nav/sidebar can be empty)
- compatibility expectations (not universal Sphinx theme compatibility)

Acceptance checklist:
- [ ] contract is self-contained
- [ ] mentions single vs site mode and asset path assumptions

---

## 3. Phase 2 — Theme pack format + validation

### Task 3.1 — Implement theme.json manifest parsing (optional but recommended)
Support:
- id, name, version
- entry.template
- entry.css/js list
- supports: single/site

Validation rules:
- template exists
- assets dir exists
- required files referenced by manifest exist

Acceptance checklist:
- [ ] missing manifest is allowed (fallback defaults)
- [ ] invalid theme pack fails fast with clear error

### Task 3.2 — Implement resolver
Resolution order:
1) project-local `./themes/<id>`
2) built-in `repo/themes/<id>`

Return `ThemeBundle`:
- template_path
- assets_dir
- css list, js list
- computed hash of template + assets (for render report)

Acceptance checklist:
- [ ] deterministic selection
- [ ] supports absolute or repo-relative paths
- [ ] emits stable hashes for reproducibility

---

## 4. Phase 3 — Base template.html (the skeleton)

### Task 4.1 — Write `themes/base/template.html`
Must:
- include `<meta charset="utf-8">`
- include `assets/theme.css` (or manifest-provided CSS list)
- include `$body$` and optional TOC insertion
- create the stable hook points listed in §2

Minimum layout:
- header
- optional sidebar area (can contain TOC)
- main content

Acceptance checklist:
- [ ] renders minimal docs cleanly
- [ ] no theme-specific assumptions (no RTD-specific markup)

### Task 4.2 — Base CSS
`themes/base/assets/theme.css`:
- readable typography
- tables and code blocks look acceptable
- minimal responsive behavior

Acceptance checklist:
- [ ] works without JS
- [ ] doesn’t depend on external fonts/CDNs

---

## 5. Phase 4 — Implement 3 theme packs (layout families)

Each theme pack:
- extends base skeleton (copy base template and modify layout zones)
- provides CSS to create the “familiar look”
- optional JS for small UX improvements (foldables, sticky sidebar, etc.)

### Theme A — `sidebar_docs` (RTD/PyData/Furo family)
Template behavior:
- `lp-sidebar` visible left
- `lp-content` right
- TOC placed in sidebar (or separate `lp-toc` region)
- optional topbar for mobile

CSS features:
- fixed/sticky sidebar
- content width responsive
- code blocks with subtle background
- headings spaced like “docs”

Optional JS:
- sidebar collapse on small screens
- active section highlight (optional; v2)

Acceptance checklist:
- [ ] looks “RTD-like” at first glance
- [ ] single-page and site mode both usable

### Theme B — `topbar_classic` (Python docs family)
Template behavior:
- top navigation bar (lp-nav)
- sidebar minimal or absent
- content centered, narrower width
- TOC can be at top or right

CSS features:
- narrower content column
- classic heading hierarchy
- subtle separators and link style

Acceptance checklist:
- [ ] resembles docs.python.org feel (not necessarily pixel-perfect)

### Theme C — `book_tutorial` (Sphinx-book/JupyterBook family)
Template behavior:
- chapter navigation sidebar
- prominent prev/next links (can be rendered by template if site mode provides nav)
- content width comfortable for tutorials
- callout styles (admonitions) if you use them

CSS features:
- tutorial-friendly spacing
- strong “reading flow”
- optional right-side “on this page” TOC (v2)

Acceptance checklist:
- [ ] suited for long-form chapters with sections

---

## 6. Phase 5 — Renderer integration

### Task 6.1 — Add `RenderConfig.with_theme(theme_id)`
Implements:
- resolve theme bundle
- set `html_template_path`, `html_assets_dir`
- set `css` / `js` lists (template variables) if you support that
- record theme hash in render report

Acceptance checklist:
- [ ] theme is selectable via build script/CLI
- [ ] fallback to base theme if none specified

### Task 6.2 — Asset bundling rules
For output:
- copy theme assets into `output/assets/` (single mode)
- copy into `<site_out>/assets/` (site mode)
- ensure pages reference `assets/...` relatively

Acceptance checklist:
- [ ] deterministic copy (sorted file list)
- [ ] no timestamps in filenames
- [ ] no network fetch

### Task 6.3 — Site mode compatibility
If you support site mode:
- ensure each generated page references the same assets path
- optional: include navigation from sitemap.json later (v2)

Acceptance checklist:
- [ ] site mode pages are styled consistently
- [ ] works opening from local filesystem (no fetch required)

---

## 7. Phase 6 — “Theme mining” from PyPI Sphinx themes (optional, v1.1)

This is optional. Implement only after the 3 theme packs work.

### Task 7.1 — Asset importer tool
`tools/import_sphinx_theme_assets.py`:
- install a specified theme package in a temp venv
- locate theme static assets
- copy into `themes/<new_theme>/assets/vendor/<pkg>/...`
- write a stub theme.json with upstream metadata

Acceptance checklist:
- [ ] deterministic pinned version support
- [ ] produces NOTICE file stub for license compliance
- [ ] does not overwrite existing theme pack without explicit flag

Note: this does not guarantee visual correctness. It just helps bootstrap styling.

---

## 8. Test Plan (comprehensive)

### 8.1 Unit tests
- [ ] resolver finds built-in themes
- [ ] resolver finds project-local themes
- [ ] invalid theme pack errors (missing template, missing assets)
- [ ] manifest parsing (if enabled)
- [ ] asset bundler copies deterministically (hash stable)

### 8.2 Integration tests — render matrix
For each theme in {base, sidebar_docs, topbar_classic, book_tutorial}:
- render single-page HTML
- render site-mode HTML (if enabled)

Fixtures:
- `ast_small.json` (headings + paragraphs)
- `ast_with_toc.json` (multiple headings)
- `ast_with_wrappers.json` (computed blocks with IDs/classes)
- `ast_with_codeblocks.json` (short + long code)
- `ast_with_foldables.json` (foldable blocks)

Assertions (single):
- [ ] output HTML exists
- [ ] contains required hook IDs: lp-header, lp-content, lp-footer
- [ ] includes CSS link(s) to assets
- [ ] body contains expected content
- [ ] wrapper IDs preserved (anchors)

Assertions (site):
- [ ] output directory contains multiple pages
- [ ] each page references the same assets paths
- [ ] sitemap.json exists (if your writer emits it)
- [ ] navigation links are not broken (basic check: presence of `<a href="...">`)

### 8.3 Golden tests — DOM invariants, not full HTML bytes
For each theme, parse HTML and assert:
- [ ] hook points exist exactly once (or expected count)
- [ ] `.computed-*` classes present where expected
- [ ] foldable containers render to `<details>` if your pipeline uses that behavior

### 8.4 Visual sanity (manual checklist; optional)
- [ ] open output in browser
- [ ] check sidebar collapse on mobile widths (if implemented)
- [ ] check tables don’t overflow
- [ ] check code blocks wrap/scroll acceptably
- [ ] check Korean text renders without tofu (font fallback)

---

## 9. Milestones

### M1 — Base theme pack + resolver
- base template/css + theme resolution + config wiring

### M2 — Three theme packs
- sidebar_docs, topbar_classic, book_tutorial

### M3 — Renderer integration + matrix tests
- theme selection from build script/CLI
- site mode compatibility

### M4 — Optional importer tool
- asset mining from PyPI Sphinx themes (bootstrap only)

---

## 10. Key guardrails (so this doesn’t explode)
- One stable HTML skeleton (DOM contract) for all themes.
- Three theme packs cover stakeholder-familiar layouts.
- Treat PyPI Sphinx themes as *asset donors*, not plug-and-play.
- Keep theming separate from semantic stages (normalize/resolve/validate/filter).

