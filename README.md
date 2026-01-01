# litepub-norm

AST normalization pipeline for the documentation platform.

## Design Decisions

- **Parsing strategy**: Uses `pypandoc` to call pandoc and return JSON (Option A)
- **AST manipulation**: Manipulates raw Pandoc JSON dicts directly (Option A - recommended for strictness)

## Usage

```python
from litepub_norm import normalize_file

result = normalize_file("document.md", "registry.json")
```

## HTML Theming

LitePub provides a theming system for customizing HTML output. Four built-in themes are available:

| Theme | Description | Best For |
|-------|-------------|----------|
| `base` | Minimal clean layout | Starting point for customization |
| `sidebar_docs` | Fixed left sidebar with TOC | API docs, reference guides |
| `topbar_classic` | Top navigation bar | Language/library docs |
| `book_tutorial` | Chapter navigation with page TOC | Tutorials, books, courses |

### Quick Start

```python
from litepub_norm.render import themed_html_config, render
from litepub_norm.filters import BuildContext

# Single-page HTML with sidebar theme
config = themed_html_config("sidebar_docs")
context = BuildContext(build_target="external", render_target="html")
result = render(filtered_ast, context, config, "document.html")

# Multi-page site with book theme
config = themed_html_config("book_tutorial", mode="site", split_level=2)
result = render(filtered_ast, context, config, "tutorial")
```

### Listing Available Themes

```python
from litepub_norm.theming import list_available_themes

themes = list_available_themes()
# ['base', 'sidebar_docs', 'topbar_classic', 'book_tutorial']
```

### Using Default Config with Theme

```python
from litepub_norm.render import default_html_config, default_html_site_config

# Single-page with specific theme
config = default_html_config("sidebar_docs")

# Multi-page site with specific theme
config = default_html_site_config(split_level=2, theme_id="book_tutorial")
```

### Builder Pattern

```python
from litepub_norm.render.config import RenderConfig
from pathlib import Path

config = (
    RenderConfig()
    .with_theme("sidebar_docs")
    .with_html_mode("site", split_level=2)
    .with_output_dir(Path("./output"))
)
```

### Creating Custom Themes

1. Copy a built-in theme as starting point:
   ```bash
   cp -r src/litepub_norm/render/themes/sidebar_docs my_project/themes/my_theme
   ```

2. Update `theme.json` with your theme ID and metadata

3. Modify `assets/theme.css` for visual styling

4. Use your theme:
   ```python
   config = themed_html_config(
       "my_theme",
       project_themes_dir=Path("my_project/themes")
   )
   ```

See [implementation/05_rendering.md](implementation/05_rendering.md) for detailed documentation.
