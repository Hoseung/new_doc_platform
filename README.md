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
