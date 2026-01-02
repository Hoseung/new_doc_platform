# Development Plan: PDF Theming Implementation

This plan outlines the steps to build the PDF rendering capability with the three defined archetypes.

> **Status**: ✅ Implemented (January 2025)
>
> This document has been updated post-implementation to accurately describe the final system and capture debugging lessons learned.

---

## Implementation Summary

The PDF theming system was successfully implemented with:
- Three archetypes: `std-report`, `corp-report`, `academic-paper`
- Modular separation of structure (template.tex), style (theme.sty), and config (theme.yaml)
- Pandoc 3.x idiomatic syntax highlighting via `--syntax-highlighting=idiomatic`
- Lua filter for callout box mapping (info/warning/danger → LaTeX environments)
- Full Korean/CJK support via xeCJK with Noto Sans CJK KR

See `implementation/06_pdf_theming.md` for complete technical documentation.

---

#### Phase 1: The Rendering Harness (Infrastructure)

*Goal: Ensure the python renderer can drive Pandoc + XeLaTeX with a local theme pack.*

* ✅ **Task 1.1**: Update `PdfRenderer` class to accept a `theme_path` config.
* ✅ **Task 1.2**: Implement "Asset Staging":
  * The renderer copies the selected theme's `assets/` folder to the temp build directory alongside the input `.tex`.
* ✅ **Task 1.3**: Implement `theme.yaml` injection:
  * Pass the theme's config file to Pandoc using `--metadata-file`.
* ✅ **Task 1.4**: Verify Korean support (Golden Test):
  * All three themes load `xeCJK` with `Noto Sans CJK KR`.
  * Korean text renders correctly in all themes.


#### Phase 2: The `std-report` Theme (Baseline)

*Goal: Create the "Technical Standard" archetype. This is the fallback/default theme.*

* ✅ **Task 2.1**: Create `themes/std-report/` structure.
* ✅ **Task 2.2**: Implement `theme.sty`:
  * Setup `booktabs`, `longtable`.
  * Define `\setcounter{secnumdepth}{4}` for deep numbering.
  * Set `parskip` for dense, indented-less paragraphs.
  * Define callout environments: `infobox`, `warningbox`, `dangerbox`.
* ✅ **Task 2.3**: Implement `template.tex`:
  * Standard `article` class.
  * Simple title block with `\maketitle`.
  * **Critical**: Include all Pandoc 3.x compatibility macros (see Debugging Notes).
* ✅ **Task 2.4**: Validate against `Analysis Artifact Payload Specs`:
  * Complex tables render cleanly without overflowing page margins.


#### Phase 3: The `corp-report` Theme (Polish)

*Goal: Create the "Modern Corporate" archetype for executive consumption.*

* ✅ **Task 3.1**: Create `themes/corp-report/`.
* ✅ **Task 3.2**: Implement `theme.sty` with `tcolorbox`:
  * Define `\newtcolorbox{metricbox}` for highlighting computed metrics.
  * Define `\newtcolorbox{codebox}` for code blocks.
  * Define callout environments: `infobox`, `warningbox`, `dangerbox`.
* ✅ **Task 3.3**: Implement `fancyhdr`:
  * Add fancy header with section marks.
  * Corporate color accent in header/footer.
* ✅ **Task 3.4**: Cover Sheet:
  * Create a custom Title Page in `template.tex` with color accent bar.


#### Phase 4: The `academic-paper` Theme (Density)

*Goal: Create the "Academic" archetype for complex analysis.*

* ✅ **Task 4.1**: Create `themes/academic-paper/`.
* ✅ **Task 4.2**: Configure `geometry`:
  * Wider margins for margin notes and annotations.
* ✅ **Task 4.3**: Typography:
  * Uses DejaVu Serif for elegant body text.
  * Subdued scholarly styling for callout boxes.


#### Phase 5: Provenance & Final Polish

*Goal: Ensure audit requirements are met.*

* ✅ **Task 5.1**: Metadata injection:
  * Renderer injects build metadata into Pandoc variables.
* ✅ **Task 5.2**: Footer logic:
  * All 3 `theme.sty` files define `\provenancefooter` command.
* ✅ **Task 5.3**: Final Golden Test Suite:
  * All three themes render the rst_source example correctly:
    - `std-report`: ~31 pages
    - `corp-report`: ~33 pages (includes cover page)
    - `academic-paper`: ~29 pages (wider margins)

---

## Debugging Notes: Lessons from Implementation

### The Core Architectural Challenge

Our modular architecture separates **structure** (template.tex) from **style** (theme.sty). This is more maintainable than monolithic templates like Eisvogel, but introduces a critical coordination requirement: **both files must provide complete Pandoc compatibility macros**.

Standard templates assume a monolithic design where everything is in one file. When we split structure from style, we discovered that certain Pandoc-generated LaTeX constructs require definitions in **both** the template and the style package.

### Critical Discovery: `\passthrough` Command

**Symptom**: PDF renders TOC but body content is completely missing (2 pages instead of 30+).

**Root Cause**: Pandoc 3.x with `--syntax-highlighting=idiomatic` generates inline code like:
```latex
\passthrough{\lstinline[role=ref]!target!}
```

If `\passthrough` is undefined, LaTeX silently fails at that point and truncates the entire document.

**Fix**: Every template.tex MUST include:
```latex
\newcommand{\passthrough}[1]{#1}
```

### Critical Discovery: `\lst@Key{role}` Definition

**Symptom**: "undefined key role" error that silently truncates the document.

**Root Cause**: RST inline roles (`:ref:`, `:doc:`, etc.) generate `\lstinline[role=ref]!...!`. The `role` key is not defined by the standard `listings` package.

**Fix**: Every theme.sty MUST include:
```latex
\makeatletter
\lst@Key{role}{}{}
\makeatother
```

### Critical Discovery: `\newcounter{none}`

**Symptom**: "No counter 'none' defined" error, empty TOC.

**Root Cause**: Pandoc generates `\setcounter{none}{0}` for longtables without captions.

**Fix**: Every template.tex MUST include:
```latex
\newcounter{none}
```

### Critical Discovery: `\pandocbounded`

**Symptom**: Images overflow page margins.

**Root Cause**: Pandoc 3.x generates `\pandocbounded{...}` for images.

**Fix**: Every template.tex MUST include:
```latex
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
```

### The `--listings` Flag is Deprecated

**Original Plan**: Use `--listings` to enable `\lstset` styling.

**Reality**: Pandoc 3.x deprecates `--listings` in favor of `--syntax-highlighting=idiomatic`. The idiomatic mode generates `\lstlisting` environments that respect `\lstset` configuration, plus it adds the `role=` parameter for RST inline roles.

**Implementation**: Use `--syntax-highlighting=idiomatic` (not `--listings`).

### Lua Filter for Callout Boxes

The plan correctly identified the need for a Lua filter to map AST Divs to LaTeX environments. The implementation uses `pdf_callouts.lua`:

```lua
local class_to_env = {
  info = "infobox",
  note = "infobox",
  warning = "warningbox",
  danger = "dangerbox",
}

function Div(el)
  for _, class in ipairs(el.classes) do
    local env_name = class_to_env[class]
    if env_name then
      return {
        pandoc.RawBlock('latex', '\\begin{' .. env_name .. '}'),
        table.unpack(el.content),
        pandoc.RawBlock('latex', '\\end{' .. env_name .. '}')
      }
    end
  end
  return nil
end
```

---

## Template Checklist (Required for All Themes)

Every `template.tex` MUST include these Pandoc compatibility definitions:

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
  \newcommand{\chapter}{\@ifstar\@litepub@schapter\@litepub@chapter}
}{}
\makeatother
```

Every `theme.sty` MUST include:

```latex
% Required for Pandoc idiomatic highlighting with RST roles
\makeatletter
\lst@Key{role}{}{}
\makeatother
```

---

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| PDF has only TOC, no body | Missing `\passthrough` command | Add `\newcommand{\passthrough}[1]{#1}` to template |
| "undefined key role" error | Missing `\lst@Key{role}` | Add role key definition to theme.sty |
| Code blocks unstyled | Pandoc using Skylighting | Use `--syntax-highlighting=idiomatic` |
| Empty TOC | "No counter 'none' defined" error | Add `\newcounter{none}` to template |
| Images overflow margins | Missing `\pandocbounded` | Add bounded image macro to template |
| Callouts render as plain text | No Lua filter | Apply `pdf_callouts.lua` filter |

---

## Mining from Existing Templates

The original strategy of "Mine, Don't Mount" from Eisvogel proved correct. Key insight: monolithic templates conflate structure and style, while our modular approach requires explicit coordination.

When borrowing from templates like Eisvogel:
1. Extract **visual definitions** (colors, box styles) → `theme.sty`
2. Extract **structural elements** (title page layout) → `template.tex`
3. **Always add** the Pandoc compatibility macros (they're often buried in monolithic templates)
4. **Test with RST content** (RST roles expose compatibility gaps that Markdown doesn't)
