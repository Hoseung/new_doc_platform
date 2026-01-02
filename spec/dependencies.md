# Dependencies and Version Requirements

This document specifies the required versions for all major components in the litepub-norm pipeline.

## Python Environment

| Component | Minimum Version | Notes |
|-----------|-----------------|-------|
| Python | 3.12 | Required for modern type hints and performance |
| pypandoc | 1.13 | Python wrapper for Pandoc invocation |

## External Tools

### Pandoc

| Component | Minimum Version | Recommended | Notes |
|-----------|-----------------|-------------|-------|
| Pandoc | 3.1 | 3.6+ | Required for `chunkedhtml` writer (multi-page HTML sites) |

**Required Pandoc features:**
- `chunkedhtml` writer (multi-page HTML sites)
- `--listings` option (generates `\lstlisting` for LaTeX)
- `--split-level` option for site generation
- JSON AST input (`--from=json`)

**Installation:**
```bash
# Ubuntu/Debian (may have older version)
sudo apt install pandoc

# For latest version, download from GitHub releases:
# https://github.com/jgm/pandoc/releases
```

### LaTeX (for PDF rendering)

| Component | Minimum Version | Recommended | Notes |
|-----------|-----------------|-------------|-------|
| TeX Live | 2023 | 2024 | Full distribution recommended |
| XeLaTeX | 0.999995 | latest | Required engine for Unicode/CJK support |

**Required LaTeX packages:**
- `fontspec` - Font selection for XeLaTeX
- `xeCJK` - Chinese/Japanese/Korean text support
- `geometry` - Page layout
- `hyperref` - Hyperlinks and PDF metadata
- `listings` - Code block formatting
- `tcolorbox` - Callout boxes (info, warning, danger)
- `booktabs` - Professional table formatting
- `longtable` - Multi-page tables
- `graphicx` - Image handling
- `fancyhdr` - Headers and footers

**Installation:**
```bash
# Ubuntu/Debian
sudo apt install texlive-full

# Or minimal installation:
sudo apt install texlive-xetex texlive-fonts-recommended texlive-latex-extra
```

### Fonts (for PDF rendering)

| Font | Purpose | Notes |
|------|---------|-------|
| Noto Sans CJK KR | Korean text | Required for Korean language support |
| DejaVu Sans/Serif/Mono | Default fonts | Fallback if system fonts unavailable |

**Installation:**
```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk fonts-dejavu
```

## Development Dependencies

| Component | Minimum Version | Purpose |
|-----------|-----------------|---------|
| pytest | 8.0 | Test framework |
| pytest-cov | 4.0 | Coverage reporting |

## Version Verification

Run the following to verify your environment:

```bash
# Python version
python --version  # Should be 3.12+

# Pandoc version
pandoc --version  # Should be 3.1+

# XeLaTeX version
xelatex --version  # Should show XeTeX

# Check for required Pandoc features
pandoc --list-output-formats | grep chunkedhtml  # Should output "chunkedhtml"
```

## Compatibility Matrix

| litepub-norm | Python | Pandoc | TeX Live |
|--------------|--------|--------|----------|
| 0.1.x | 3.12+ | 3.1+ | 2023+ |
