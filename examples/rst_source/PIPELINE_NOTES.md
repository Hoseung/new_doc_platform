# RST Source Pipeline Notes

This document describes what was needed to process `rst_source` through the LitePub Norm pipeline.

## Source Structure

The `rst_source` example is a multi-file RST document:
- 8 RST files (index.rst + 7 chapters)
- 5 PNG figures in `_static/figures/`
- 4 CSV table files in `_static/tables/`

## Pipeline Stage Fixes

### 1. Normalization Stage

**Issue**: RST adapter only recognized custom directives (`.. computed-figure::`) with `:id:` fields, not standard RST directives with `:name:` attributes.

**Fix**: Extended `src/litepub_norm/adapters/rst.py`:
- Added `STANDARD_DIRECTIVES` set for `figure`, `table`, `image`
- Added `STANDARD_DIRECTIVE_PATTERN` regex to match standard RST directives
- Added `NAME_FIELD_PATTERN` to extract `:name:` attribute from directive options
- Modified `preprocess_rst()` to wrap standard directives with semantic HTML comments when they have `:name:` attributes

**Code**: The adapter now wraps:
```rst
.. figure:: path/to/image.png
   :name: fig:example
   :caption: Example caption
```

As:
```rst
<!-- BEGIN_COMPUTED_BLOCK id="fig:example" kind="figure" -->
.. figure:: path/to/image.png
   :name: fig:example
   :caption: Example caption
<!-- END_COMPUTED_BLOCK -->
```

### 2. Registry Configuration

**Created Files**:

1. `config/normalization_registry.json` - Flat ID→metadata mapping:
   ```json
   {
     "fig:example_plot": {
       "role": "computed",
       "kind": "figure",
       "visibility": "external",
       "policy": [],
       "source": "figures/example_line_plot.png"
     }
   }
   ```

   **Note**: Registry format must be flat (not nested under "entries" key).

2. `config/aarc_registry.json` - Artifact registry with SHA256 hashes for figures.

### 3. Resolution Stage

No issues - works with the adapter extension.

### 4. Filtering Stage

Works correctly:
- `internal`: All 5 figures included
- `external`: All 5 figures stripped (visibility=external, no dossier figures)
- `dossier`: All 5 figures removed

### 5. Rendering Stage

**Issue 1**: `\chapter*{Abstract}` undefined in article class.

The RST source contains raw LaTeX blocks with `\chapter*{}` commands, but the LaTeX template uses `article` document class which doesn't define `\chapter`.

**Fix**: Added compatibility stub in `src/litepub_norm/render/pdf/templates/template.tex`:
```latex
\makeatletter
\@ifundefined{chapter}{%
  \newcommand{\@litepub@chapter}[1]{\section{#1}}
  \newcommand{\@litepub@schapter}[1]{\section*{#1}}
  \newcommand{\chapter}{\@ifstar\@litepub@schapter\@litepub@chapter}
  \providecommand{\chaptermark}[1]{\markboth{#1}{}}
}{}
\makeatother
```

**Issue 2**: `\pandocbounded{}` undefined (Pandoc 3.x feature).

**Fix**: Added:
```latex
\providecommand{\pandocbounded}[1]{#1}
```

**Issue 3**: `\real{}` undefined in table column specifications (Pandoc 3.x feature).

**Fix**: Added packages and definition:
```latex
\usepackage{array}
\usepackage{calc}
% ...
\makeatletter
\providecommand{\real}[1]{\strip@pt\dimexpr #1pt\relax}
\makeatother
```

## Build Script

Created `build.py` that:
1. Concatenates multiple RST files into single document
2. Runs normalization with RST adapter
3. Processes through resolution, filtering, and rendering
4. Builds all three targets: internal, external, dossier

### Usage

```bash
# Standard build (single-page HTML + PDF)
python build.py

# Multi-page static site
python build.py --site

# Site only with section-level split
python build.py --only-site --split-level=2
```

### Command-line Options

| Option | Description |
|--------|-------------|
| `--site` | Build multi-page static site in addition to regular outputs |
| `--only-site` | Only build site (skip single-page HTML/PDF) |
| `--split-level=N` | Split pages at heading level N (1=chapters, 2=sections) |

## Output Summary

| Target   | Format | Figures | Size/Pages |
|----------|--------|---------|------------|
| internal | HTML   | 5       | single page |
| internal | PDF    | 5       | 970 KB |
| internal | Site   | 5       | 10 pages (split_level=2) |
| external | HTML   | 0       | single page |
| dossier  | PDF    | 0       | 163 KB |

## Key Lessons

1. **RST Adapter Flexibility**: Standard RST `:name:` attributes should map to semantic IDs
2. **Registry Format**: Must be flat ID→metadata, not nested under "entries"
3. **LaTeX Compatibility**: Article class needs chapter stubs for book-style RST sources
4. **Pandoc 3.x Support**: Template needs `\pandocbounded`, `\real`, and calc package
