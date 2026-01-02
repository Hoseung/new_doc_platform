# PDF Theming Implementation

## Overview

The PDF theming system provides a modular, deterministic approach to generating styled PDF documents via Pandoc and XeLaTeX. It separates **document structure** (template.tex), **visual styling** (theme.sty), and **configuration** (theme.yaml) to ensure reproducibility and maintainability.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  template.tex   │    │   theme.sty     │    │  theme.yaml     │
│                 │    │                 │    │                 │
│ • Document      │    │ • Colors        │    │ • Fonts         │
│   class         │    │ • Typography    │    │ • Geometry      │
│ • $body$        │    │ • Boxes         │    │ • Toggles       │
│ • Title page    │    │ • Tables        │    │                 │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   PdfRenderer       │
                    │                     │
                    │ • Asset staging     │
                    │ • Lua filters       │
                    │ • Pandoc → LaTeX    │
                    │ • XeLaTeX → PDF     │
                    └─────────────────────┘
```

---

## Module Architecture

```
src/litepub_norm/render/
├── pdf/
│   ├── renderer.py           # Main PDF rendering logic
│   └── templates/
│       └── template.tex      # Legacy fallback template
├── pdf_themes/
│   ├── __init__.py           # Public API exports
│   ├── manifest.py           # PdfThemeManifest, YAML parsing
│   ├── resolver.py           # Theme resolution, PdfThemeBundle
│   ├── filters/
│   │   └── pdf_callouts.lua  # Lua filter for Div → LaTeX environment mapping
│   └── themes/
│       ├── std-report/       # Technical Standard archetype
│       │   ├── template.tex
│       │   ├── theme.yaml
│       │   └── assets/
│       │       └── theme.sty
│       ├── corp-report/      # Modern Corporate archetype
│       │   ├── template.tex
│       │   ├── theme.yaml
│       │   └── assets/
│       │       └── theme.sty
│       └── academic-paper/   # Academic archetype
│           ├── template.tex
│           ├── theme.yaml
│           └── assets/
│               └── theme.sty
└── config.py                 # RenderConfig with PDF theme support
```

---

## Theme Pack Structure

Each theme pack follows this layout:

```
<theme_id>/
├── template.tex          # Document skeleton (structure)
├── theme.yaml            # Configuration (fonts, geometry)
└── assets/
    ├── theme.sty         # Visual styling (the "CSS")
    ├── fonts/            # Bundled fonts (optional)
    └── images/           # Logos, watermarks (optional)
```

### template.tex — Document Structure

The template defines the document class, page layout, and content insertion points:

```latex
\documentclass[11pt,a4paper]{article}

% Load theme styling
\usepackage{assets/theme}

% Essential packages
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage{geometry}
...

% Pandoc compatibility
\providecommand{\tightlist}{...}
\newcommand{\passthrough}[1]{#1}  % Required for idiomatic highlighting

\begin{document}

$if(title)$
\maketitle
$endif$

$if(toc)$
\tableofcontents
\newpage
$endif$

$body$

\end{document}
```

### theme.sty — Visual Styling

The style package contains all visual definitions (colors, typography, box environments):

```latex
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{theme}[2025/01/02 Theme Name]

%% Colors
\RequirePackage{xcolor}
\definecolor{themeAccent}{HTML}{0366D6}

%% Code Listings
\RequirePackage{listings}
\makeatletter
\lst@Key{role}{}{}  % Required for Pandoc RST role support
\makeatother
\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{themeCodeBg},
  ...
}

%% Callout Boxes
\RequirePackage{tcolorbox}
\tcbuselibrary{skins,breakable}

\newtcolorbox{infobox}{...}
\newtcolorbox{warningbox}{...}
\newtcolorbox{dangerbox}{...}

%% Provenance Footer
\newcommand{\provenancefooter}[2]{
  \fancyfoot[C]{\tiny Run: #1 | Generated: #2}
}
```

---

## Three Standard Archetypes

### std-report (Technical Standard)

**Intent**: Audits, specifications, regulatory dossiers.

**Characteristics**:
- Dense, formal typography
- Deep section numbering (1.2.3.4)
- Minimal visual embellishment
- Serif fonts with tight spacing

**Key Styling**:
```latex
% Deep numbering
\setcounter{secnumdepth}{4}

% Dense paragraphs
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}

% Formal code blocks with frame
\lstset{frame=single, ...}

% Subdued callout boxes
\newtcolorbox{infobox}{colback=gray!5!white, leftrule=2pt, ...}
```

### corp-report (Modern Corporate)

**Intent**: Executive summaries, external whitepapers.

**Characteristics**:
- Clean, polished look
- Custom title page (cover sheet)
- Sans-serif primary font
- Colorful accent elements

**Key Styling**:
```latex
% Cover page with accent bar
\begin{titlepage}
  \noindent\colorbox{corpAccent}{\makebox[\textwidth][l]{\rule{0pt}{1cm}}}
  ...
\end{titlepage}

% Modern callout boxes
\newtcolorbox{infobox}{
  colback=blue!5!white,
  colframe=blue!75!black,
  leftrule=3pt,
  ...
}

% Watermark support
\newcommand{\setwatermark}[1]{...}
```

### academic-paper (Data-Rich Analysis)

**Intent**: Research notes, complex analysis.

**Characteristics**:
- Elegant typography (serif)
- Wider margins
- Subtle, scholarly callout styling
- Tufte-inspired margin notes

**Key Styling**:
```latex
% Wider margins for annotations
\geometry{left=3cm, right=3cm, marginparwidth=2cm}

% Traditional serif font
\setmainfont{DejaVu Serif}

% Scholarly subtle callouts
\newtcolorbox{infobox}{
  colback=acadLight,
  leftrule=1.5pt,
  ...
}

% Margin notes
\RequirePackage{marginnote}
\newcommand{\sidenote}[1]{\marginnote{#1}}
```

---

## Rendering Pipeline Integration

### Asset Staging

When rendering with a theme, assets are staged to the build directory:

```python
def _stage_assets(assets_dir: Path, output_dir: Path) -> Path:
    """Copy theme.sty, fonts/, images/ to output directory."""
    staged_dir = output_dir / "assets"

    # Copy theme.sty
    shutil.copy2(assets_dir / "theme.sty", staged_dir / "theme.sty")

    # Copy fonts directory
    if (assets_dir / "fonts").is_dir():
        shutil.copytree(assets_dir / "fonts", staged_dir / "fonts")

    # Copy images directory
    if (assets_dir / "images").is_dir():
        shutil.copytree(assets_dir / "images", staged_dir / "images")

    return staged_dir
```

### Syntax Highlighting

Pandoc 3.x uses `--syntax-highlighting=idiomatic` to generate `\lstlisting` environments:

```python
# In renderer.py
if context.strict:
    extra_args.append("--syntax-highlighting=none")
else:
    extra_args.append("--syntax-highlighting=idiomatic")
```

This enables theme.sty to control code block styling via `\lstset`.

### Lua Filters

The `pdf_callouts.lua` filter maps AST Div classes to LaTeX environments:

```lua
-- pdf_callouts.lua
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

## Configuration API

### RenderConfig Fields

```python
@dataclass(frozen=True)
class RenderConfig:
    # PDF theming
    pdf_theme: str | None = None           # Theme ID (e.g., "corp-report")
    pdf_theme_dir: Path | None = None      # Resolved theme directory
    latex_template_path: Path | None = None
    latex_style_path: Path | None = None
    latex_assets_dir: Path | None = None

    # PDF compilation
    latex_engine: str = "xelatex"
    latex_runs: int = 2

    def with_pdf_theme(
        self,
        theme_id: str,
        project_themes_dir: Path | None = None
    ) -> RenderConfig:
        """Configure PDF theme by ID."""
        ...
```

### Factory Functions

```python
# Default PDF with specific theme
config = default_pdf_config("corp-report")

# Themed config with output directory
config = themed_pdf_config("academic-paper").with_output_dir(Path("./output"))

# List available themes
from litepub_norm.render.pdf_themes import list_pdf_themes
print(list_pdf_themes())  # ['std-report', 'corp-report', 'academic-paper']
```

### Usage Example

```python
from litepub_norm.render import render
from litepub_norm.render.config import themed_pdf_config
from litepub_norm.filters import BuildContext

# Configure with corporate theme
config = themed_pdf_config("corp-report").with_output_dir(Path("./output"))

# Build context (non-strict for syntax highlighting)
context = BuildContext(
    build_target="internal",
    render_target="pdf",
    strict=False
)

# Render
result = render(filtered_ast, context, config, "whitepaper.pdf")

if result.success:
    print(f"PDF: {result.primary_output}")  # ./output/whitepaper.pdf
```

---

## Debugging Notes

### Critical Template Requirements

Templates must include these Pandoc compatibility definitions:

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

### Critical theme.sty Requirements

Style packages must define the `role` key for lstinline:

```latex
% Required: Pandoc idiomatic highlighting uses lstinline[role=ref]
\makeatletter
\lst@Key{role}{}{}
\makeatother
```

Without this, RST inline roles like `:ref:\`target\`` cause "undefined key" errors that silently truncate the document.

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| PDF has only TOC, no body | Missing `\passthrough` command | Add `\newcommand{\passthrough}[1]{#1}` to template |
| "undefined key role" error | Missing `\lst@Key{role}` | Add role key definition to theme.sty |
| Code blocks unstyled | Pandoc using Skylighting | Use `--syntax-highlighting=idiomatic` |
| Empty TOC | "No counter 'none' defined" error | Add `\newcounter{none}` to template |
| Images overflow margins | Missing `\pandocbounded` | Add bounded image macro to template |

---

## Testing

```bash
# Build with specific theme
python examples/rst_source/build.py --pdf-theme academic-paper

# Build with all themes to verify
for theme in std-report corp-report academic-paper; do
    python examples/rst_source/build.py --pdf-theme $theme
    pdfinfo examples/rst_source/output/internal_pdf/whitepaper.pdf | grep Pages
done
```

Expected page counts (for rst_source example):
- **std-report**: ~31 pages
- **corp-report**: ~33 pages (includes cover page)
- **academic-paper**: ~29 pages (wider margins)

---

## Design Principles

1. **Modular Separation**: Structure (template.tex), style (theme.sty), and config (theme.yaml) are kept separate
2. **Determinism**: All fonts bundled in assets/fonts/, no system font dependencies
3. **Korean Support**: All themes configure xeCJK with Noto Sans CJK KR
4. **Pandoc Compatibility**: Templates include all required compatibility macros
5. **Audit Trail**: render_report.json includes theme info, template hashes
