# Rendering Stage Documentation

## Overview

The rendering stage is the fifth and final stage in the LitePub documentation pipeline. It transforms a filtered Pandoc AST into final output formats: HTML (single-page or multi-page static site), PDF, Markdown, or RST.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Normalization  │───▶│   Resolution    │───▶│   Validation    │───▶│    Filtering    │───▶│   RENDERING     │
│                 │    │                 │    │                 │    │                 │    │                 │
│ • Parse source  │    │ • Load payloads │    │ • Schema check  │    │ • Visibility    │    │ • Pandoc        │
│ • Wrap computed │    │ • Validate      │    │ • Safety check  │    │ • Policy        │    │ • Templates     │
│   blocks        │    │ • Emit AST      │    │ • Invariants    │    │ • Presentation  │    │ • Final output  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

The rendering stage is the **presentation layer** that converts semantic AST into reader-facing formats while maintaining reproducibility through deterministic tool invocation.

---

## Role in the Architecture

The rendering stage operates **after** all semantic transformations are complete:

1. **Input**: Filtered Pandoc AST (JSON) — all visibility, policy, and presentation filters already applied
2. **Output**: Final documents (HTML, PDF, Markdown, RST) with assets

### Key Architectural Principles

| Principle | Description |
|-----------|-------------|
| **Determinism** | Same AST + config = identical output (stable temp paths, no timestamps in logic) |
| **Tool Isolation** | Pandoc and LaTeX are invoked via subprocess, not linked libraries |
| **Report Generation** | Every render produces `render_report.json` for reproducibility audit |
| **Asset Management** | Templates and assets are copied to output directory for self-contained builds |

### Separation of Concerns

```
Filtering Stage                      Rendering Stage
─────────────────                    ─────────────────
• Visibility rules                   • Pandoc invocation
• Policy enforcement                 • Template application
• Metadata stripping                 • Asset bundling
• Content transformations            • Format-specific options
  (folding, appendix)
```

The rendering stage does **not** make content decisions — it only translates the filtered AST to output formats.

---

## Module Architecture

```
src/litepub_norm/
├── render/
│   ├── __init__.py           # Public API exports
│   ├── api.py                # Main render() and render_all_targets()
│   ├── config.py             # RenderConfig dataclass
│   ├── result.py             # RenderResult and error types
│   ├── report.py             # RenderReport for audit trail
│   ├── pandoc_runner.py      # Pandoc subprocess wrapper
│   ├── latex_runner.py       # XeLaTeX subprocess wrapper
│   ├── themes/               # Built-in HTML themes
│   │   ├── base/             # Minimal base theme
│   │   ├── sidebar_docs/     # RTD/Furo-like sidebar theme
│   │   ├── topbar_classic/   # Python docs-like topbar theme
│   │   └── book_tutorial/    # JupyterBook-like theme
│   ├── html/
│   │   ├── renderer.py       # HTML renderer (single + site modes)
│   │   └── lua/
│   │       └── foldable.lua  # Lua filter for foldable content
│   ├── pdf/
│   │   ├── renderer.py       # PDF renderer (via XeLaTeX)
│   │   └── templates/
│   │       └── template.tex  # LaTeX template
│   └── text/
│       ├── md_renderer.py    # Markdown output
│       └── rst_renderer.py   # RST output
└── theming/                  # HTML theming system
    ├── __init__.py           # Public API exports
    ├── contract.py           # DOM contract (stable hook points)
    ├── manifest.py           # theme.json parsing
    ├── resolver.py           # Theme resolution and bundling
    └── selection.py          # RenderConfig integration
```

---

## Core Modules

### config.py — RenderConfig

The `RenderConfig` is an immutable dataclass that contains all rendering configuration.

```python
@dataclass(frozen=True)
class RenderConfig:
    # Output directory
    output_dir: Path = Path.cwd()

    # Pandoc options
    pandoc_path: Path | None = None
    pandoc_required_version: str | None = None

    # HTML options
    html_theme: str | None = None           # Theme ID (e.g., "base", "sidebar_docs")
    html_template_path: Path | None = None  # Resolved from theme if not set
    html_assets_dir: Path | None = None     # Resolved from theme if not set
    html_lua_filters: tuple[Path, ...] = ()
    html_mode: HtmlMode = "single"          # "single" or "site"
    html_site_split_level: int = 1          # 1=chapters, 2=sections
    html_site_chunk_template: str = "%s-%i.html"

    # PDF/LaTeX options
    latex_template_path: Path | None = None
    latex_engine: str = "xelatex"
    latex_engine_path: Path | None = None
    latex_runs: int = 2

    # Writer options (passed to pandoc)
    html_writer_options: tuple[str, ...] = ()
    latex_writer_options: tuple[str, ...] = ()

    # General options
    copy_assets: bool = True
    standalone: bool = True
```

**Builder Methods:**

```python
# Override output directory
config = default_html_config().with_output_dir(Path("./output"))

# Switch HTML mode
config = default_html_config().with_html_mode("site", split_level=2)

# Apply a theme
config = RenderConfig().with_theme("sidebar_docs")

# Chain multiple operations
config = (
    RenderConfig()
    .with_theme("book_tutorial")
    .with_html_mode("site", split_level=2)
    .with_output_dir(Path("./output"))
)
```

**Default Configurations:**

| Factory Function | Purpose |
|------------------|---------|
| `default_html_config(theme_id)` | Single-page HTML with specified theme (default: "base") |
| `default_html_site_config(split_level, theme_id)` | Multi-page static site with theme |
| `themed_html_config(theme_id, mode, split_level)` | Full theming control |
| `default_pdf_config()` | PDF via XeLaTeX |

---

### api.py — Pipeline API

#### `render()` — Main Entry Point

```python
def render(
    ast: dict[str, Any],
    context: BuildContext,
    config: RenderConfig | None = None,
    output_name: str | None = None,
) -> RenderResult:
```

Routes to the appropriate renderer based on `context.render_target`.

**Example:**

```python
from litepub_norm.render import render
from litepub_norm.render.config import default_html_site_config
from litepub_norm.filters import BuildContext

# Build context
context = BuildContext(build_target="internal", render_target="html")

# Site mode config
config = default_html_site_config(split_level=2).with_output_dir("./output")

# Render
result = render(filtered_ast, context, config, "whitepaper")
```

#### `render_all_targets()` — Multiple Formats

```python
def render_all_targets(
    ast: dict[str, Any],
    build_target: Literal["internal", "external", "dossier"],
    config: RenderConfig | None = None,
    targets: list[RenderTarget] | None = None,
) -> dict[RenderTarget, RenderResult]:
```

Renders to all specified formats in sequence.

---

### result.py — RenderResult

```python
@dataclass
class RenderResult:
    success: bool
    output_files: list[Path]      # All generated files
    warnings: list[RenderWarning]
    errors: list[RenderError]
    report: dict | None           # render_report.json contents

    @property
    def primary_output(self) -> Path | None:
        """First output file (usually the main document)."""
```

**Error Codes:**

| Code | Stage | Description |
|------|-------|-------------|
| `PANDOC_FAILED` | pandoc | Pandoc conversion error |
| `LATEX_FAILED` | latex | LaTeX compilation error |
| `LATEX_NOT_FOUND` | latex | LaTeX engine not in PATH |
| `RENDER_ERROR` | render | General rendering error |

---

### report.py — RenderReport

Every render produces a `render_report.json` for audit and reproducibility.

```json
{
  "timestamps": {
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:30:05Z"
  },
  "tools": {
    "pandoc_version": "3.1.9",
    "latex_engine": "xelatex",
    "latex_engine_version": "XeTeX 3.141592653-2.6-0.999995 (TeX Live 2023)"
  },
  "context": {
    "build_target": "internal",
    "render_target": "html",
    "strict_mode": false
  },
  "templates": {
    "template_path": "/path/to/template.html",
    "template_hash": "sha256:abc123...",
    "assets_dir": "/path/to/assets",
    "assets_hash": "sha256:def456..."
  },
  "output": {
    "files": ["output/document.html", "output/assets/theme.css"]
  },
  "extra": {
    "html_mode": "site",
    "split_level": 2,
    "pages": ["index.html", "1-introduction.html", "2-methodology.html"]
  }
}
```

---

## HTML Rendering

### Single-Page Mode (Default)

Produces a single HTML file with all content.

```python
from litepub_norm.render import render
from litepub_norm.render.config import default_html_config

config = default_html_config().with_output_dir("./output")
result = render(filtered_ast, context, config, "report.html")
```

**Output structure:**

```
output/
├── report.html        # Main document
├── assets/
│   ├── theme.css      # Copied from template assets
│   └── theme.js
└── render_report.json
```

### Multi-Page Site Mode

Uses Pandoc's `chunkedhtml` writer to produce a static site with navigation.

```python
from litepub_norm.render.config import default_html_site_config

config = default_html_site_config(split_level=2).with_output_dir("./output")
result = render(filtered_ast, context, config, "whitepaper")
```

**Configuration options:**

| Option | Default | Description |
|--------|---------|-------------|
| `html_mode` | `"single"` | `"single"` or `"site"` |
| `html_site_split_level` | `1` | Split at level-N headings (1=chapters, 2=sections) |
| `html_site_chunk_template` | `"%s-%i.html"` | Filename template (`%s`=number, `%i`=id) |

**Output structure (site mode):**

```
output/whitepaper/
├── index.html           # Top page with TOC
├── 1-introduction.html  # Chapter 1
├── 2-methodology.html   # Chapter 2
├── ...
├── sitemap.json         # Navigation hierarchy
├── assets/
│   ├── theme.css
│   └── theme.js
└── render_report.json
```

---

## HTML Theming System

The HTML theming system provides a pluggable mechanism for visual customization while maintaining stable DOM hooks for consistent behavior.

### Built-in Themes

| Theme ID | Style | Best For |
|----------|-------|----------|
| `base` | Minimal clean layout | Starting point for customization |
| `sidebar_docs` | RTD/Furo-like with fixed left sidebar | API documentation, reference guides |
| `topbar_classic` | Python docs-like with top navigation | Language/library documentation |
| `book_tutorial` | JupyterBook-like with chapter navigation | Tutorials, books, courses |

**Quick Usage:**

```python
from litepub_norm.render import default_html_config, themed_html_config

# Single-page with sidebar_docs theme
config = default_html_config("sidebar_docs")

# Multi-page site with book_tutorial theme
config = themed_html_config("book_tutorial", mode="site", split_level=2)
```

### Theme Architecture

Each theme is a self-contained directory with:

```
theme_name/
├── theme.json         # Manifest with metadata
├── template.html      # Pandoc HTML template
└── assets/
    ├── theme.css      # Visual styling
    └── theme.js       # Interactive features
```

**Manifest Structure (`theme.json`):**

```json
{
  "id": "sidebar_docs",
  "name": "Sidebar Documentation",
  "version": "1.0.0",
  "description": "RTD/Furo-like with fixed left sidebar",
  "base": "base",
  "entry": {
    "template": "template.html",
    "css": ["assets/theme.css"],
    "js": ["assets/theme.js"]
  },
  "supports": {
    "single": true,
    "site": true
  }
}
```

### DOM Contract

All themes must include these stable hook points for JavaScript and CSS:

**Required IDs:**

| ID | Purpose |
|----|---------|
| `lp-header` | Page header (title, metadata) |
| `lp-nav` | Site navigation |
| `lp-sidebar` | Sidebar content (TOC, menu) |
| `lp-toc` | Table of contents |
| `lp-content` | Main document content |
| `lp-footer` | Page footer |

**Required Classes:**

| Class | Purpose |
|-------|---------|
| `computed-figure` | Computed figure containers |
| `computed-table` | Computed table containers |
| `computed-metric` | Computed metric displays |
| `foldable` | Collapsible sections |
| `foldable-header` | Clickable header for foldable |
| `foldable-content` | Hidden/shown content |

### Theme Resolution

Themes are resolved in this order:

1. **Project-local themes**: `<project>/themes/<theme_id>/`
2. **Built-in themes**: `src/litepub_norm/render/themes/<theme_id>/`

```python
from litepub_norm.theming import resolve_theme, list_available_themes

# List all available themes
themes = list_available_themes()
# ['base', 'sidebar_docs', 'topbar_classic', 'book_tutorial']

# Resolve a theme to get full paths
bundle = resolve_theme("sidebar_docs")
print(bundle.template_path)  # Path to template.html
print(bundle.assets_dir)     # Path to assets directory
print(bundle.template_hash)  # sha256:abc123... (for reproducibility)
```

### ThemeBundle

When a theme is resolved, you receive a `ThemeBundle` with all paths and metadata:

```python
@dataclass(frozen=True)
class ThemeBundle:
    theme_id: str           # "sidebar_docs"
    theme_dir: Path         # Full path to theme directory
    template_path: Path     # Full path to template.html
    assets_dir: Path        # Full path to assets/
    css_files: tuple[Path]  # Absolute paths to CSS files
    js_files: tuple[Path]   # Absolute paths to JS files
    manifest: ThemeManifest # Parsed theme.json
    template_hash: str      # "sha256:..." for reproducibility
    assets_hash: str        # "sha256:..." for reproducibility
```

### Template Validation

Templates are validated for required hooks:

```python
from litepub_norm.theming import validate_template_hooks

result = validate_template_hooks(template_content)
if not result.valid:
    print(f"Missing: {result.missing_mandatory}")
    # ['lp-content', '$body$ (Pandoc variable)']
```

---

## PDF Rendering

PDF rendering uses a two-stage process:

1. **AST → LaTeX**: Pandoc generates LaTeX source
2. **LaTeX → PDF**: XeLaTeX compiles to PDF

```python
from litepub_norm.render.config import default_pdf_config

config = default_pdf_config().with_output_dir("./output")
result = render(filtered_ast, context, config, "report.pdf")
```

**Output structure:**

```
output/
├── report.pdf          # Final PDF
├── report.tex          # Intermediate LaTeX (for debugging)
├── report.log          # LaTeX log
└── render_report.json
```

### LaTeX Template Features

The default template (`template.tex`) includes:

| Feature | Package/Command | Purpose |
|---------|-----------------|---------|
| CJK support | `xeCJK` | Korean/Chinese/Japanese text |
| Space preservation | `CJKspace=true` | Preserve spaces in Korean text |
| Code listings | `listings` | Syntax-highlighted code blocks |
| Tables | `longtable`, `booktabs` | Professional table formatting |
| Hyperlinks | `hyperref` | Clickable links and bookmarks |

### Pandoc 3.x Compatibility

The template provides stubs for Pandoc 3.x features:

```latex
% Bounded images (Pandoc 3.x)
\providecommand{\pandocbounded}[1]{#1}

% Table column widths (Pandoc 3.x)
\providecommand{\real}[1]{\strip@pt\dimexpr #1pt\relax}

% Chapter compatibility (for article class)
\@ifundefined{chapter}{%
  \newcommand{\chapter}{\@ifstar\@litepub@schapter\@litepub@chapter}
}{}
```

---

## Applying Custom Themes and Templates

### Using Built-in Themes

The simplest way to customize HTML output is to select a built-in theme:

```python
from litepub_norm.render import render, themed_html_config
from litepub_norm.filters import BuildContext

# Use sidebar_docs theme for API documentation
config = themed_html_config("sidebar_docs", mode="site", split_level=2)
context = BuildContext(build_target="external", render_target="html")
result = render(filtered_ast, context, config, "api-reference")

# Use book_tutorial theme for tutorials
config = themed_html_config("book_tutorial", mode="site", split_level=1)
result = render(filtered_ast, context, config, "tutorial")
```

### HTML Theme Customization

The HTML template system uses three components:

1. **Template** (`template.html`) — HTML structure with Pandoc variables
2. **CSS** (`assets/theme.css`) — Visual styling
3. **JavaScript** (`assets/theme.js`) — Interactive features (foldable sections)

#### Creating a Custom Theme

**Step 1: Copy a built-in theme as starting point**

```bash
# Copy sidebar_docs as a starting point
cp -r src/litepub_norm/render/themes/sidebar_docs my_project/themes/my_theme

# Or copy the minimal base theme
cp -r src/litepub_norm/render/themes/base my_project/themes/my_theme
```

**Step 2: Update the manifest**

Edit `my_project/themes/my_theme/theme.json`:

```json
{
  "id": "my_theme",
  "name": "My Custom Theme",
  "version": "1.0.0",
  "description": "Custom theme for my project",
  "base": "sidebar_docs",
  "entry": {
    "template": "template.html",
    "css": ["assets/theme.css"],
    "js": ["assets/theme.js"]
  }
}
```

**Step 3: Modify theme.css**

The CSS is organized into sections:

```css
/* Base typography */
body { ... }

/* Title block */
#title-block-header { ... }

/* Table of contents */
nav#TOC { ... }

/* Main content */
main { ... }

/* Semantic blocks (figures, tables, metrics) */
.computed-figure { ... }
.computed-table { ... }
.computed-metric { ... }

/* Foldable sections */
.foldable { ... }
.foldable-header { ... }
.foldable-content { ... }
```

**Step 4: Use the custom theme**

```python
from pathlib import Path
from litepub_norm.render import themed_html_config

# Use project-local theme (automatically discovered from themes/ directory)
config = themed_html_config(
    "my_theme",
    mode="site",
    split_level=2,
    project_themes_dir=Path("my_project/themes")
)

# Or use with_theme() for more control
from litepub_norm.render.config import RenderConfig

config = (
    RenderConfig()
    .with_theme("my_theme", project_themes_dir=Path("my_project/themes"))
    .with_html_mode("site", split_level=2)
    .with_output_dir(Path("./output"))
)
```

#### Template Variables

The HTML template uses Pandoc template syntax:

| Variable | Description |
|----------|-------------|
| `$title$` | Document title |
| `$subtitle$` | Document subtitle |
| `$author$` | Author(s) |
| `$date$` | Publication date |
| `$abstract$` | Abstract content |
| `$body$` | Main document content |
| `$toc$` | Boolean: include TOC? |
| `$table-of-contents$` | Generated TOC HTML |

**Custom variables** can be set via document metadata:

```yaml
---
title: My Report
custom-logo: assets/logo.png
---
```

```html
<!-- In template.html -->
$if(custom-logo)$
<img src="$custom-logo$" class="logo" />
$endif$
```

### Site Mode Navigation Customization

For multi-page sites, customize navigation by modifying the template:

```html
<!-- Add navigation bar -->
$if(navigation)$
<nav class="site-nav">
  $for(navigation)$
  <a href="$navigation.url$">$navigation.title$</a>
  $endfor$
</nav>
$endif$
```

The generated `sitemap.json` contains the page hierarchy:

```json
{
  "index": "index.html",
  "pages": [
    {"title": "Introduction", "url": "1-introduction.html"},
    {"title": "Methodology", "url": "2-methodology.html"}
  ]
}
```

### PDF Theme Customization

**Step 1: Copy the default template**

```bash
cp src/litepub_norm/render/pdf/templates/template.tex my_theme/template.tex
```

**Step 2: Modify LaTeX styling**

Key customization points:

```latex
% Document class and margins
\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}

% Fonts (requires XeLaTeX)
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Colors
\definecolor{linkcolor}{HTML}{0366d6}
\hypersetup{colorlinks=true,linkcolor=linkcolor}

% Headers and footers
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead[L]{\leftmark}
\fancyhead[R]{\thepage}
```

**Step 3: Configure the renderer**

```python
custom_config = RenderConfig(
    latex_template_path=Path("my_theme/template.tex"),
    latex_engine="xelatex",
    latex_runs=2,
)
```

### Theme Inheritance Pattern

For maintaining consistency across themes, use a layered approach:

```
base_theme/
├── template.html          # Base structure
├── assets/
│   ├── base.css           # Foundation styles
│   └── base.js
└── template.tex           # Base LaTeX

corporate_theme/           # Extends base
├── template.html          # Overrides base
├── assets/
│   ├── base.css           # Symlink to base
│   ├── corporate.css      # Additional styles
│   └── logo.png
└── template.tex           # Overrides base
```

---

## Complete Example

```python
from pathlib import Path
from litepub_norm import resolve, load_registry
from litepub_norm.filters import apply_filters, BuildContext, FilterConfig
from litepub_norm.render import render
from litepub_norm.render.config import (
    default_html_site_config,
    default_pdf_config,
)

# Load resolved AST (from previous stages)
registry = load_registry("aarc_registry.json")
resolved_ast = resolve(normalized_ast, registry)

# Apply filters for internal build
context = BuildContext(build_target="internal", render_target="html")
filtered_ast, filter_report = apply_filters(resolved_ast, context=context)

# Render to multi-page HTML site
site_config = default_html_site_config(split_level=2).with_output_dir(
    Path("output/internal_site")
)
html_result = render(filtered_ast, context, site_config, "whitepaper")

if html_result.success:
    print(f"Site generated: {html_result.primary_output}")
    print(f"Pages: {len([f for f in html_result.output_files if str(f).endswith('.html')])}")
else:
    for err in html_result.errors:
        print(f"Error: {err.code} - {err.message}")

# Render to PDF
pdf_context = BuildContext(build_target="internal", render_target="pdf")
pdf_config = default_pdf_config().with_output_dir(Path("output/internal_pdf"))
pdf_result = render(filtered_ast, pdf_context, pdf_config, "whitepaper.pdf")

if pdf_result.success:
    print(f"PDF generated: {pdf_result.primary_output}")
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Korean spaces missing in PDF | Ensure `\xeCJKsetup{CJKspace=true}` in template |
| Undefined `\chapter` in article class | Template provides compatibility stub |
| Undefined `\pandocbounded` | Update template for Pandoc 3.x compatibility |
| Pandoc not found | Install Pandoc or set `pandoc_path` |
| XeLaTeX not found | Install TeX Live or set `latex_engine_path` |

### Debug Files

| File | Purpose |
|------|---------|
| `render_report.json` | Tool versions, timestamps, file hashes |
| `*.tex` | Intermediate LaTeX (inspect for errors) |
| `*.log` | LaTeX compilation log |

---

## Testing

Comprehensive tests are in `test/test_render.py` and `test/test_theming.py`:

```bash
# Rendering tests
uv run pytest test/test_render.py -v

# Theming system tests
uv run pytest test/test_theming.py -v
```

Test categories:

**Rendering tests (`test_render.py`):**
- **Config tests**: RenderConfig immutability and builder methods
- **HTML tests**: Single-page and site mode rendering
- **PDF tests**: LaTeX generation and compilation
- **Report tests**: Audit trail generation
- **Integration tests**: Full pipeline rendering

**Theming tests (`test_theming.py`):**
- **Contract tests**: DOM contract validation (required IDs/classes)
- **Manifest tests**: theme.json parsing and defaults
- **Resolver tests**: Theme discovery and bundling
- **Selection tests**: RenderConfig integration
- **Built-in theme tests**: All themes pass validation

---

## Design Principles

1. **Tool-Based**: Leverages Pandoc and LaTeX instead of reimplementing converters
2. **Reproducible**: Deterministic temp paths, tool version tracking, content hashes
3. **Auditable**: Every render generates a detailed report
4. **Themeable**: Pluggable HTML themes with stable DOM contract for consistent behavior
5. **Configurable**: Templates and assets are easily customizable
6. **Fail-Safe**: Errors are captured and reported, never silently ignored
