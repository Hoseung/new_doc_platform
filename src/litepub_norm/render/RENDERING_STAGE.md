# Rendering Stage Summary

The rendering stage converts filtered normalized documents into final output formats (HTML or PDF).

## Architecture

```
render/
├── __init__.py          # Main render() function and RenderResult
├── config.py            # RenderConfig and default configs
├── html/
│   ├── __init__.py      # HTML renderer
│   └── templates/
│       └── template.html
└── pdf/
    ├── __init__.py      # PDF renderer (XeLaTeX via Pandoc)
    └── templates/
        └── template.tex
```

## Usage

```python
from litepub_norm.render import render, RenderConfig
from litepub_norm.render.config import default_html_config, default_pdf_config

# HTML rendering
html_config = default_html_config().with_output_dir(output_path)
result = render(filtered_doc, context, html_config, "output.html")

# PDF rendering
pdf_config = default_pdf_config().with_output_dir(output_path)
result = render(filtered_doc, context, pdf_config, "output.pdf")
```

## RenderResult

```python
@dataclass
class RenderResult:
    success: bool
    primary_output: Path | None
    output_files: list[Path]
    error_code: str | None
    error_message: str | None
```

## HTML Renderer

- Uses Pandoc to convert normalized JSON AST to HTML
- Copies referenced assets to output directory
- Generates `render_report.json` with metadata

## PDF Renderer

- Uses Pandoc with XeLaTeX engine
- Requires: `xelatex`, `fontspec`, `xeCJK` packages
- Template: `templates/template.tex`

### LaTeX Template Features

| Feature | Package/Command | Purpose |
|---------|-----------------|---------|
| CJK support | `xeCJK` | Korean/Chinese/Japanese text |
| Space preservation | `CJKspace=true` | Preserve spaces in Korean text |
| Code listings | `listings` | Syntax-highlighted code blocks |
| Tables | `longtable`, `booktabs` | Professional table formatting |
| Hyperlinks | `hyperref` | Clickable links and bookmarks |

### Pandoc 3.x Compatibility

The template includes definitions for Pandoc 3.x features:

```latex
% Bounded images
\providecommand{\pandocbounded}[1]{#1}

% Table column widths
\providecommand{\real}[1]{\strip@pt\dimexpr #1pt\relax}

% Tight lists
\providecommand{\tightlist}{...}
```

### Article Class Compatibility

For documents with `\chapter` commands (e.g., from RST sources):

```latex
\@ifundefined{chapter}{%
  \newcommand{\chapter}{\@ifstar\@litepub@schapter\@litepub@chapter}
}{}
```

## Font Configuration

### Latin Fonts
- Main: DejaVu Serif
- Sans: DejaVu Sans
- Mono: DejaVu Sans Mono

### CJK Fonts (Korean)
- Main: Noto Sans CJK KR
- Sans: Noto Sans CJK KR
- Mono: Noto Sans Mono CJK KR

## Error Handling

Common error codes:
- `LATEX_FAILED` - LaTeX compilation error
- `PANDOC_FAILED` - Pandoc conversion error
- `MISSING_ASSET` - Referenced file not found

Check `.log` files in output directory for detailed error messages.

## Troubleshooting

### Missing Korean Spaces
Ensure `CJKspace=true` is set in `\xeCJKsetup`.

### Undefined Control Sequence
Check if Pandoc 3.x commands (`\pandocbounded`, `\real`) are defined in template.

### Chapter Not Defined
The template maps `\chapter` to `\section` for article class compatibility.
