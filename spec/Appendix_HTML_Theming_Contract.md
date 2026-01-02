# Appendix: HTML Theming Contract / Spec

This document defines **how HTML theming works** in the LitePub pipeline, so build-script authors and theme authors can change the look of HTML output **without touching AST semantics**.

It is intentionally “pluggable”: selecting a theme should be a config change, not a code fork. The baseline mechanism is **(1) template.html + (2) assets/theme.css + (3) assets/theme.js**.

---

## 1. Non-Goals (so we don’t lie to ourselves)

1. HTML theming is **not** a new semantic layer.
2. HTML theming must not require changes to the **canonical AST contracts**.
3. Sphinx themes are **not drop-in compatible** with Pandoc HTML output (they expect Sphinx’s Jinja2 templates + DOM structure). You can *reuse* their styling, but you cannot “install and apply them directly” without an adaptation step.

---

## 2. Definitions

- **Theme Pack**: a directory containing `template.html` and static assets (CSS/JS/images/fonts).
- **Renderer**: component that turns (filtered) Pandoc AST into HTML (single page or site mode).
- **Template**: an HTML skeleton using **Pandoc template syntax** (variables like `$title$`, `$body$`).
- **Assets**: files copied verbatim into the output folder (CSS/JS/etc.).
- **Site Mode**: multi-page static site output using Pandoc’s `chunkedhtml` writer, plus a `sitemap.json`.

---

## 3. Contract: Theme Pack Layout

A theme pack **MUST** be loadable from a directory path.

Minimum required structure:

```
my_theme/
├── template.html
└── assets/
    ├── theme.css
    └── theme.js        (optional - CSS handles core interactions)

```

Why these files exist: template provides structure, CSS provides look **and core interactions** (collapsible TOC, sticky sidebar), JS provides **optional enhancements** (current-section highlighting, state persistence).

Recommended additions:

```
my_theme/
├── theme.json              # optional manifest (see §4)
├── template.html
└── assets/
    ├── theme.css
    ├── theme.js
    ├── fonts/...
    └── img/...

```

### 3.1 Encoding requirement (Korean included)

All HTML output and templates **MUST** be UTF-8 and include:

```html
<meta charset="utf-8">

```

(UTF-8 is absolutely sufficient for Korean; if something breaks, it’s usually a font or CSS issue, not the encoding.)

---

## 4. Contract: Optional `theme.json` Manifest

If present, `theme.json` is metadata and routing hints only.

Example:

```json
{
  "id": "rtd_like",
  "name": "RTD-like",
  "version": "1.0.0",
  "base": null,
  "entry": {
    "template": "template.html",
    "css": ["assets/theme.css"],
    "js": ["assets/theme.js"]
  }
}

```

Rules:

- `id` should be stable (used by build scripts).
- `entry.*` paths are **relative** to the theme directory.
- Manifest must not introduce semantics; it’s only for wiring.

---

## 5. Contract: Template (`template.html`)

### 5.1 What `template.html` is supposed to do

`template.html` is the **outer shell** of the HTML document. It decides:

- page chrome (header/footer)
- where TOC appears
- where the body goes
- which CSS/JS files are included
- whether to display optional navigation blocks (site mode)

It does **not**:

- compute content
- reorder semantics
- invent missing parts of the document

### 5.2 Minimum required Pandoc variables

Templates **MUST** support, at minimum, these variables (because your renderer already documents/depends on them): `$title$`, `$body$`, `$toc$`, `$table-of-contents$`.

You also already documented the common metadata variables `$subtitle$`, `$author$`, `$date$`, `$abstract$`.

### 5.3 Custom variables

Custom variables are allowed via document metadata (YAML front matter), and referenced in template with `$if(...)$` blocks.

### 5.4 Site navigation hook (optional)

For site mode, templates may render navigation if provided, e.g. iterating over `navigation`.

Your build will also emit `sitemap.json` describing page hierarchy.

### 5.5 CSS-Only Navigation Contract

The base theme implements **core navigation using CSS only**, without JavaScript dependency. This ensures:

1. **Reliability**: Navigation works with JavaScript disabled
2. **Performance**: No JS bundle required for basic functionality
3. **Accessibility**: Native browser behavior for links and focus

**Required CSS patterns for collapsible TOC:**

```css
/* Hide nested levels by default */
#lp-toc > ul > li > ul {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.2s ease-out;
}

/* Expand on hover or keyboard focus */
#lp-toc > ul > li:hover > ul,
#lp-toc > ul > li:focus-within > ul {
  max-height: 2000px;
  transition: max-height 0.3s ease-in;
}
```

**Visual indicator for expandable items:**

```css
#lp-toc > ul > li:has(> ul) > a::after {
  content: " ▸";
  font-size: 0.7em;
  transition: transform 0.2s;
  display: inline-block;
}

#lp-toc > ul > li:hover:has(> ul) > a::after {
  transform: rotate(90deg);
}
```

**Sticky sidebar:**

```css
#lp-toc {
  position: sticky;
  top: var(--spacing-lg);
  max-height: calc(100vh - var(--spacing-xl) * 2);
  overflow-y: auto;
}
```

**What CSS provides:**
- Expand/collapse on hover
- Keyboard navigation via `:focus-within`
- Visual expand indicator (arrow rotation)
- Smooth transitions
- Fixed/sticky sidebar
- Works offline

**What requires JavaScript (optional enhancements):**
- Highlight current section while scrolling
- Remember expand/collapse state
- Smooth scroll to sections
- Search within TOC

See `implementation/07_html_site_navigation.md` for full details.

---

## 6. Contract: Assets (`assets/`)

### 6.1 Copying rules

- The renderer **MUST copy** the theme’s `assets/` directory into the output.
- Output examples you already defined:
    - single page output includes `output/assets/theme.css` and `output/assets/theme.js`.
    - site mode output includes `output/<site>/assets/...` plus `sitemap.json`.

### 6.2 Stable CSS hooks (recommended contract)

To keep themes maintainable, the renderer should ensure stable class hooks for semantic blocks (these were already implied by your CSS sectioning guidance): `.computed-figure`, `.computed-table`, `.computed-metric`, plus foldables.

If you ever change class names, that’s a breaking change for themes.

---

## 7. Contract: Theme Selection from Build Script

### 7.1 API shape

Your rendering config already shows the intended model: pick a template path and assets dir in config.

The official contract is:

- Build script selects either:
    - `html_template_path` + `html_assets_dir`, **or**
    - a `theme_id` that resolves to those paths via your own lookup.

### 7.2 Reproducibility requirement

For audit-grade determinism:

- store theme packs in-repo, **or**
- pin exact versions + hash the resolved template and assets in the render report.

Your render report schema already anticipates recording template/assets hashes and paths.

---

## 8. Contract: “Lua filters” vs “Python (panflute) filters”

You previously referenced `html_lua_filters` in config.

Here’s the clean rule:

- **Theming does not require Lua filters.** A theme is valid with only `template.html + assets/`.
- Lua filters are an **optional Pandoc-writer hook** (useful when invoking Pandoc writers like `chunkedhtml` and you need writer-stage transformations).
- Your main transformation pipeline can remain Python/panflute-based; Lua should be treated as “advanced / optional / last-mile”.

So: you didn’t “need Lua because themes require it.” Themes don’t. That earlier mention is best treated as an optional extension point, not part of the base theming mechanism.

---

## 9. Site Mode vs Single Page Mode (doesn’t violate contracts)

You already defined:

- `html_mode: "single" | "site"`
- `html_site_split_level`
- `html_site_chunk_template`

This **does not hurt your contract**, because it’s purely a rendering backend choice: same AST in, different HTML packaging out. The theme contract stays identical; only the template may choose to render navigation and your renderer emits a `sitemap.json`.

---

## 10. “Can we automate making our own style set from open-sourced Sphinx themes?”

Partially, yes. Fully automatic, no (unless you also recreate Sphinx’s DOM conventions).

Practical automation strategy:

1. **Fetch theme package assets** (CSS/JS/fonts/images) from a Sphinx theme distribution.
2. **Create a LitePub theme pack** with:
    - your own `template.html` (Pandoc template syntax)
    - copied/rewired CSS/JS assets
3. **Add a DOM-compat adapter (optional)**:
    - a small postprocessor that adds expected classes/containers so the borrowed CSS behaves.

This is exactly the kind of “looks like RTD / looks like Python docs” approach that works without dragging Sphinx into your pipeline.

---

## 11. Popular Sphinx theme packages on PyPI (curated)

These are *installable theme sources* you can mine for assets and design language:

- `sphinx-rtd-theme` (Read the Docs theme) ([PyPI](https://pypi.org/project/sphinx-rtd-theme/?utm_source=chatgpt.com))
- `python-docs-theme` (CPython docs theme) ([PyPI](https://pypi.org/project/python-docs-theme/?utm_source=chatgpt.com))
- `pydata-sphinx-theme` (PyData ecosystem theme) ([PyPI](https://pypi.org/project/pydata-sphinx-theme/?utm_source=chatgpt.com))
- `furo` (clean modern theme) ([PyPI](https://pypi.org/project/furo/?utm_source=chatgpt.com))
- `sphinx-book-theme` (book / notebook-friendly theme) ([PyPI](https://pypi.org/project/sphinx-book-theme/0.1.9/?utm_source=chatgpt.com))
- `sphinx-immaterial` (mkdocs-material adapted to Sphinx) ([PyPI](https://pypi.org/project/sphinx-immaterial/?utm_source=chatgpt.com))
- `sphinxawesome-theme` (modern usability features; code copy buttons etc.) ([PyPI](https://pypi.org/project/sphinxawesome-safenet-theme/?utm_source=chatgpt.com))
- `sphinx-press-theme` / `sphinx_press_theme` (VuePress-like) ([PyPI](https://pypi.org/project/sphinx-press-theme/?utm_source=chatgpt.com))
- `sphinx-bootstrap-theme` (Bootstrap-based classic) ([PyPI](https://pypi.org/project/sphinx-bootstrap-theme/?utm_source=chatgpt.com))
- `alabaster` (Sphinx’s long-time default theme) ([PyPI](https://pypi.org/project/alabaster/0.7.7/?utm_source=chatgpt.com))
- `sphinx-theme-material` and/or `sphinx-material` (Material-ish options) ([PyPI](https://pypi.org/project/sphinx-theme-material/?utm_source=chatgpt.com))

Note: these packages are not “LitePub themes”; they’re upstream sources you can borrow from.

---

## 12. Minimal `template.html` skeleton (what you should write)

This is the “good enough” baseline that matches your variable contract and keeps themes sane:

```html
<!doctype html>
<html lang="$lang$">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>$if(title)$$title$$endif$</title>

  <!-- Theme CSS -->
  <link rel="stylesheet" href="assets/theme.css">

  $for(header-includes)$
  $header-includes$
  $endfor$
</head>

<body>
  <header id="title-block-header">
    $if(title)$<h1 class="title">$title$</h1>$endif$
    $if(subtitle)$<p class="subtitle">$subtitle$</p>$endif$
    $if(author)$<p class="author">$author$</p>$endif$
    $if(date)$<p class="date">$date$</p>$endif$
  </header>

  $if(toc)$
  <nav id="TOC">
    $table-of-contents$
  </nav>
  $endif$

  <main>
    $body$
  </main>

  <!-- Optional: JavaScript for enhanced features -->
  <!-- <script src="assets/theme.js"></script> -->

  $for(include-after)$
  $include-after$
  $endfor$
</body>
</html>

```

This aligns with your documented template variables. Note that JavaScript is optional; the base theme provides full navigation functionality via CSS alone.