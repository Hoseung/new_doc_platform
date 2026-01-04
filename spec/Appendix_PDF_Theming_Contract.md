# Appendix: PDF Theming Contract / Spec (v1)

## 0. Purpose

This document defines **how PDF theming works** in the pipeline. It enforces a strict separation between **Document Structure** (AST), **Page Skeleton** (Template), and **Styling Logic** (LaTeX Packages).

To ensure audit-grade determinism and professional output, PDF theming relies on **Pandoc via XeLaTeX**.

---

## 1. Non-Goals

1. PDF theming is **not** a new semantic layer. Semantics (e.g., "Note", "Warning") come from the AST.
2. PDF theming must **not** require the host OS to install arbitrary fonts. Standard fonts (DejaVu, Noto Sans CJK) are acceptable as they are widely available across Linux distributions.
3. PDF theming must **not** execute arbitrary code. It is a transformation of the AST into LaTeX macros.

---

## 2. Definitions

* **Theme Pack**: A directory containing the template, style package, and static assets (fonts/images).
* **Archetype**: A "preset" style philosophy (e.g., Corporate, Standard, Academic) implemented as a Theme Pack.
* **Template (`template.tex`)**: The outer shell that sets up the `\documentclass` and includes Pandoc compatibility macros.
* **Style Package (`theme.sty`)**: The LaTeX package acting as the "CSS," defining colors, typography, and container environments.
* **Theme Config (`theme.yaml`)**: Pandoc metadata file defining geometry, font filenames, and toggle flags.
* **Lua Filter**: Render-time filter that maps AST elements (Divs with classes) to LaTeX environments.

---

## 3. Contract: Theme Pack Layout

A theme pack **MUST** be loadable from a directory path and explicitly referenced in the build config.

**Required Structure:**

```text
<theme_id>/
├── template.tex            # Pandoc LaTeX template (structure + compatibility)
├── theme.yaml              # Configuration (fonts, geometry, toggles)
└── assets/
    ├── theme.sty           # The "CSS" (macros, packages, colors)
    ├── fonts/              # Bundled .ttf/.otf files (optional)
    └── images/             # Logos, watermarks, etc.

```

### 3.1 Determinism & Fonts

* **Standard Fonts**: Themes rely on standard cross-platform fonts (DejaVu family, Noto Sans CJK KR) that are available on typical Linux systems and CI/CD environments.
* **Bundling (Optional)**: Themes MAY include custom fonts in `assets/fonts/` for brand-specific typography.
* **Korean Support**: Themes **MUST** configure `xeCJK` with a CJK-compatible font (Noto Sans CJK KR is the standard choice).

---

## 4. Contract: The Three Standard Archetypes

To prevent fragmentation, the system officially supports **three distinct archetypes** for v1.

### 4.1 `std-report` (The Technical Standard)

* **Intent**: Audits, specifications, regulatory dossiers.
* **Visuals**: Dense, rigid, minimal fluff. Resembles ISO standards or IETF RFCs.
* **Key Traits**:
  * Strict numbering depth (secnumdepth=4).
  * `booktabs` for all computed tables.
  * Serif fonts (DejaVu Serif) for body text.
  * Framed code blocks with line numbers.
  * Subdued callout boxes (gray left border).

### 4.2 `corp-report` (The Modern Corporate)

* **Intent**: Executive summaries, external whitepapers.
* **Visuals**: Clean, polished, brand-aligned. Resembles Stripe technical guides.
* **Key Traits**:
  * Distinct title page ("Cover Sheet") with accent color bar.
  * Fancy headers/footers with section marks.
  * Sans-serif fonts (DejaVu Sans) for modern look.
  * Colored callout boxes (`tcolorbox`) for info/warning/danger.
  * Metric display boxes for highlighting computed values.

### 4.3 `academic-paper` (The Data-Rich Analysis)

* **Intent**: Deep dives, research notes, complex analysis.
* **Visuals**: Elegant typography, scholarly appearance.
* **Key Traits**:
  * Wider margins for annotations.
  * Serif fonts (DejaVu Serif) for body text.
  * Subtle, scholarly callout styling.
  * Margin note support via `marginnote` package.

---

## 5. Contract: Template (`template.tex`)

The template is the **outer shell**. It MUST:

1. **Load the Theme Package**: `\usepackage{assets/theme}`.
2. **Apply Metadata**: Inject `$title$`, `$author$`, `$date$` into standard LaTeX macros.
3. **Render Body**: Output `$body$` (the AST content).
4. **Provide Pandoc Compatibility**: Include all required compatibility macros (see 5.1).

### 5.1 Required Pandoc Compatibility Macros

Every `template.tex` **MUST** include these definitions for Pandoc 3.x compatibility:

```latex
% Required for tightlist in bullet points
\providecommand{\tightlist}{%
  \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

% Required for idiomatic highlighting with RST roles
\newcommand{\passthrough}[1]{#1}

% Required for Pandoc 3.x image sizing
\makeatletter
\newsavebox\pandoc@box
\newcommand*\pandocbounded[1]{%
  \sbox\pandoc@box{#1}%
  \ifdim\wd\pandoc@box>\linewidth
    \resizebox{\linewidth}{!}{#1}%
  \else
    #1%
  \fi
}
\makeatother

% Required for longtable without caption
\newcounter{none}

% Required for article class using \chapter
\makeatletter
\@ifundefined{chapter}{%
  \newcommand{\@litepub@chapter}[1]{\section{#1}}
  \newcommand{\@litepub@schapter}[1]{\section*{#1}}
  \newcommand{\chapter}{\@ifstar\@litepub@schapter\@litepub@chapter}
}{}
\makeatother
```

**Warning**: Missing any of these macros can cause silent document truncation. The `\passthrough` command is particularly critical—without it, documents with inline RST roles will render only the TOC.

---

## 6. Contract: Style Package (`theme.sty`)

The `.sty` file is the **CSS equivalent**. It MUST:

### 6.1 Pandoc Syntax Highlighting Compatibility

* **MUST** define the `role` key for `listings` package to support RST inline roles:

```latex
\makeatletter
\lst@Key{role}{}{}
\makeatother
```

Without this definition, inline roles like `:ref:` will cause "undefined key" errors that silently truncate the document.

### 6.2 Computed Artifact Styling

* **Tables**: MUST load and configure `booktabs` and `longtable` to handle computed tables injected by the Resolver.
* **Metrics**: MUST define a visual representation for computed metrics (e.g., a macro `\RenderMetric{Label}{Value}`).
* **Figures**: MUST configure `graphicx` to handle image sizing and placement.

### 6.3 Callout Environment Definitions

* **MUST** define `tcolorbox` environments for semantic callouts:
  * `infobox` - for info/note callouts
  * `warningbox` - for warning callouts
  * `dangerbox` - for danger/error callouts

These environments are invoked by the Lua filter during rendering.

### 6.4 Provenance Footer (Audit Requirement)

* Themes MUST support injecting **Run IDs / Commit Hashes** into the footer for traceability.
* Define `\provenancefooter{run_id}{timestamp}` command for footer injection.

---

## 7. Contract: Lua Filter (`pdf_callouts.lua`)

A Lua filter **MUST** be applied during PDF rendering to map AST Divs to LaTeX environments.

### 7.1 Required Mappings

```lua
local class_to_env = {
  info = "infobox",
  note = "infobox",
  warning = "warningbox",
  danger = "dangerbox",
}
```

### 7.2 Filter Behavior

The filter transforms Divs with recognized classes into LaTeX environment blocks:
```
Div[class=info] → \begin{infobox}...\end{infobox}
```

Without this filter, callout boxes render as plain unstyled text.

---

## 8. Contract: Renderer Configuration

The PDF renderer **MUST** invoke Pandoc with specific flags:

### 8.1 Required Pandoc Arguments

```python
cmd = [
    "pandoc",
    "--pdf-engine=xelatex",
    "--syntax-highlighting=idiomatic",  # NOT --listings (deprecated)
    f"--template={template_path}",
    f"--lua-filter={filter_path}",      # pdf_callouts.lua
    # ... metadata and input/output
]
```

### 8.2 Syntax Highlighting Mode

* **Use**: `--syntax-highlighting=idiomatic`
* **NOT**: `--listings` (deprecated in Pandoc 3.x)

The idiomatic mode generates `\lstlisting` environments that respect `\lstset` configuration AND adds the `role=` parameter needed for RST inline roles.

---

## 9. Safety Contract (Strict Targets)

For `build_target` = `external` or `dossier`:

* **No Raw LaTeX**: The AST validator guarantees no raw LaTeX blocks exist.
* **Theme Trust**: The `theme.sty` is considered "trusted system code."
* **No Network**: The renderer MUST NOT attempt to fetch remote assets (images/fonts) during compilation.

---

## 10. Common Failure Modes

| Symptom | Cause | Contract Violation |
|---------|-------|-------------------|
| PDF shows only TOC | Missing `\passthrough` | Section 5.1 |
| "undefined key role" error | Missing `\lst@Key{role}` | Section 6.1 |
| Callouts render as plain text | No Lua filter applied | Section 7 |
| Images overflow margins | Missing `\pandocbounded` | Section 5.1 |
| Empty TOC / counter errors | Missing `\newcounter{none}` | Section 5.1 |

---

## 11. Implementation Reference

For implementation details, module organization, and code examples, see:

- **[implementation/06_pdf_theming.md](../implementation/06_pdf_theming.md)** — PDF theming implementation guide
