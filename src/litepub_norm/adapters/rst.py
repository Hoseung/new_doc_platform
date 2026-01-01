"""
reStructuredText adapter for the normalization pipeline.

Pandoc's RST reader may not preserve custom directives in a usable form.
This adapter uses a preprocessor strategy: it converts known directives
(computed-table, computed-figure, metric, annotation, prose) into a form
that Pandoc will preserve as Divs.

The preprocessor converts RST directives to fenced Divs before Pandoc parsing.
"""

from __future__ import annotations

import re
from typing import Any


# Known directive types that represent semantic blocks (custom litepub directives)
KNOWN_DIRECTIVES = {
    "computed-table",
    "computed-figure",
    "metric",
    "annotation",
    "prose",
}

# Standard RST directives that can also be semantic blocks if they have :name:
STANDARD_DIRECTIVES = {
    "figure",
    "table",
    "image",
}

# Regex to match RST directive start: ".. directive-name::"
DIRECTIVE_PATTERN = re.compile(
    r"^(\s*)\.\.\s+(" + "|".join(re.escape(d) for d in KNOWN_DIRECTIVES) + r")::\s*$"
)

# Regex to match standard RST directives: ".. figure:: path" or ".. table::"
STANDARD_DIRECTIVE_PATTERN = re.compile(
    r"^(\s*)\.\.\s+(" + "|".join(re.escape(d) for d in STANDARD_DIRECTIVES) + r")::\s*(.*)$"
)

# Regex to match :id: field (for custom directives)
ID_FIELD_PATTERN = re.compile(r"^\s+:id:\s+(\S+)\s*$")

# Regex to match :name: field (for standard RST directives)
NAME_FIELD_PATTERN = re.compile(r"^\s+:name:\s+(\S+)\s*$")


def preprocess_rst(text: str) -> str:
    """
    Preprocess RST text to convert known directives to fenced Divs.

    This allows Pandoc to parse them as Div blocks with identifiers.

    Handles both:
    - Custom litepub directives (computed-table, computed-figure, etc.) with :id: field
    - Standard RST directives (figure, table, image) with :name: field

    Args:
        text: Raw RST source text.

    Returns:
        Modified RST text with directives converted to fenced Div syntax.
    """
    lines = text.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for custom litepub directives first
        match = DIRECTIVE_PATTERN.match(line)

        # Also check for standard RST directives with :name:
        std_match = STANDARD_DIRECTIVE_PATTERN.match(line) if not match else None

        if match:
            indent = match.group(1)
            directive_type = match.group(2)

            # Look for :id: field on the next line(s)
            semantic_id = None
            body_start = i + 1
            j = i + 1

            while j < len(lines):
                next_line = lines[j]
                # Check for :id: field
                id_match = ID_FIELD_PATTERN.match(next_line)
                if id_match:
                    semantic_id = id_match.group(1)
                    body_start = j + 1
                    j += 1
                    continue
                # Check for other field options (skip them)
                if re.match(r"^\s+:\w+:", next_line):
                    body_start = j + 1
                    j += 1
                    continue
                # Check for blank line (separator before body)
                if not next_line.strip():
                    body_start = j + 1
                    j += 1
                    break
                # Content started
                break

            if semantic_id is None:
                # No :id: found - pass through as-is
                result_lines.append(line)
                i += 1
                continue

            # Find the end of the directive body (next non-indented line or directive)
            body_lines = []
            body_indent = None

            while j < len(lines):
                body_line = lines[j]

                # Empty line - include it
                if not body_line.strip():
                    body_lines.append("")
                    j += 1
                    continue

                # Check if this is content (indented) or end of directive
                line_indent = len(body_line) - len(body_line.lstrip())

                if body_indent is None:
                    # First content line sets the body indent
                    if line_indent > len(indent):
                        body_indent = line_indent
                        body_lines.append(body_line[body_indent:])
                        j += 1
                        continue
                    else:
                        # No body content
                        break
                else:
                    # Check if still indented (part of body)
                    if line_indent >= body_indent:
                        body_lines.append(body_line[body_indent:])
                        j += 1
                        continue
                    else:
                        # Outdented - end of directive
                        break

            # Remove trailing empty lines from body
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()

            # Convert to fenced Div syntax (Pandoc markdown style embedded in RST)
            # We use HTML comment fences since they work well
            result_lines.append(f"{indent}.. raw:: html")
            result_lines.append("")
            result_lines.append(f"{indent}   <!-- BEGIN {semantic_id} -->")
            result_lines.append("")

            # Add body content
            for body_line in body_lines:
                if body_line:
                    result_lines.append(f"{indent}{body_line}")
                else:
                    result_lines.append("")

            result_lines.append("")
            result_lines.append(f"{indent}.. raw:: html")
            result_lines.append("")
            result_lines.append(f"{indent}   <!-- END {semantic_id} -->")
            result_lines.append("")

            i = j

        elif std_match:
            # Handle standard RST directives (figure, table, image) with :name:
            indent = std_match.group(1)
            directive_type = std_match.group(2)
            directive_arg = std_match.group(3)  # e.g., path for figure

            # Scan for :name: field and collect directive options
            semantic_id = None
            options_lines = [line]  # Start with the directive line
            j = i + 1
            directive_indent = len(indent)

            while j < len(lines):
                next_line = lines[j]

                # Empty line before body content
                if not next_line.strip():
                    options_lines.append(next_line)
                    j += 1
                    continue

                # Check for :name: field
                name_match = NAME_FIELD_PATTERN.match(next_line)
                if name_match:
                    semantic_id = name_match.group(1)
                    options_lines.append(next_line)
                    j += 1
                    continue

                # Check for other option fields (:width:, :alt:, etc.)
                if re.match(r"^\s+:\w+:", next_line):
                    options_lines.append(next_line)
                    j += 1
                    continue

                # Check if this is body content (caption for figure, etc.)
                line_indent = len(next_line) - len(next_line.lstrip())
                if line_indent > directive_indent:
                    # Body content - continue collecting
                    options_lines.append(next_line)
                    j += 1
                    continue

                # End of directive
                break

            if semantic_id is None:
                # No :name: found - pass through as-is
                result_lines.append(line)
                i += 1
                continue

            # Wrap the entire directive with semantic markers
            result_lines.append(f"{indent}.. raw:: html")
            result_lines.append("")
            result_lines.append(f"{indent}   <!-- BEGIN {semantic_id} -->")
            result_lines.append("")

            # Add the original directive lines
            for opt_line in options_lines:
                result_lines.append(opt_line)

            result_lines.append("")
            result_lines.append(f"{indent}.. raw:: html")
            result_lines.append("")
            result_lines.append(f"{indent}   <!-- END {semantic_id} -->")
            result_lines.append("")

            i = j

        else:
            result_lines.append(line)
            i += 1

    return "\n".join(result_lines)


def apply(ast: dict) -> dict:
    """
    Apply the RST adapter to a Pandoc AST.

    Since we use preprocessing, this function mainly handles any post-processing
    needed after Pandoc parsing. The heavy lifting is done in preprocess_rst().

    For RST, we reuse the md_adapter logic since the preprocessing converts
    RST directives to HTML comment fences.

    Args:
        ast: A Pandoc AST as a dict (parsed JSON).

    Returns:
        Modified AST with wrapper Div candidates.
    """
    # Import here to avoid circular dependency
    from . import markdown
    return markdown.apply(ast)
