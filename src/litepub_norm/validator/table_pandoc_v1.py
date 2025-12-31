"""Validator for table.pandoc.json@v1 payloads."""

from __future__ import annotations

from typing import Any

from .errors import ValidationError
from ..resolver.config import ResolutionConfig, ResolutionLimits
from .pandoc_walk import (
    walk_pandoc,
    WalkContext,
    NodeContext,
    ALL_BLOCK_TYPES,
    ALL_INLINE_TYPES,
)


# Types that are never allowed in table payloads (safety policy)
NEVER_ALLOWED_TYPES = {"Div"}

# Types that require explicit permission
RAW_TYPES = {"RawInline", "RawBlock"}

# Safe inline types for tables
SAFE_INLINE_TYPES = {
    "Str",
    "Space",
    "SoftBreak",
    "LineBreak",
    "Emph",
    "Underline",
    "Strong",
    "Strikeout",
    "Superscript",
    "Subscript",
    "SmallCaps",
    "Code",
    "Math",
    "Link",
    "Image",
    "Span",
    "Quoted",
    "Cite",
    "Note",
}

# Safe block types for table cells
SAFE_BLOCK_TYPES = {
    "Plain",
    "Para",
    "CodeBlock",
    "BlockQuote",
    "BulletList",
    "OrderedList",
    "DefinitionList",
    "Header",
    "HorizontalRule",
    "LineBlock",
    # Note: Table is excluded (no nested tables in cells)
    # Note: Figure is excluded (no figures in cells by default)
}


def validate_table_pandoc_v1(
    payload: dict[str, Any],
    semantic_id: str,
    config: ResolutionConfig | None = None,
    *,
    allow_nested_tables: bool = False,
    allow_figures_in_cells: bool = False,
    allow_images_in_cells: bool = True,
    check_geometry: bool = True,
) -> None:
    """
    Validate a table.pandoc.json@v1 payload.

    Args:
        payload: Parsed Pandoc Table block.
        semantic_id: For error messages.
        config: Resolution config for safety settings.
        allow_nested_tables: Allow Table blocks inside cells.
        allow_figures_in_cells: Allow Figure blocks inside cells.
        allow_images_in_cells: Allow Image inlines inside cells.
        check_geometry: Validate cell spanning geometry.

    Raises:
        ValidationError: If payload is invalid.
    """
    spec = "table.pandoc.json@v1"
    allow_raw = config.allow_raw_pandoc if config else False
    limits = config.limits if config else None

    if not isinstance(payload, dict):
        raise ValidationError(
            "Pandoc table payload must be an object",
            code="VAL_PANDOC_NOT_OBJECT",
            semantic_id=semantic_id,
            spec=spec,
        )

    if payload.get("t") != "Table":
        raise ValidationError(
            f"Expected Table block, got {payload.get('t')}",
            code="VAL_PANDOC_NOT_TABLE",
            semantic_id=semantic_id,
            spec=spec,
        )

    content = payload.get("c", [])
    if not isinstance(content, list) or len(content) < 6:
        raise ValidationError(
            "Invalid Table structure (expected 6-element array)",
            code="VAL_PANDOC_TABLE_STRUCTURE",
            semantic_id=semantic_id,
            spec=spec,
            hint="Table.c should be [Attr, Caption, ColSpecs, TableHead, [TableBody], TableFoot]",
        )

    # Build allowed type sets based on config
    allowed_block_types = set(SAFE_BLOCK_TYPES)
    if allow_nested_tables:
        allowed_block_types.add("Table")
    if allow_figures_in_cells:
        allowed_block_types.add("Figure")
    if allow_raw:
        allowed_block_types.add("RawBlock")

    allowed_inline_types = set(SAFE_INLINE_TYPES)
    if not allow_images_in_cells:
        allowed_inline_types.discard("Image")
    if allow_raw:
        allowed_inline_types.add("RawInline")

    # Table structure types that are part of the table itself, not content
    table_structure_types = {"Table", "TableHead", "TableBody", "TableFoot", "Row", "Cell"}

    # Define the safety check callback
    def safety_check(node: Any, ctx: WalkContext) -> None:
        node_type = ctx.node_type
        if not node_type:
            return

        # Skip table structure types - they are validated separately
        if node_type in table_structure_types:
            return

        # Never allow Div in payloads (prevents wrapper smuggling)
        if node_type in NEVER_ALLOWED_TYPES:
            raise ValidationError(
                f"{node_type} blocks not allowed in table payload",
                code=f"VAL_PANDOC_{node_type.upper()}_FORBIDDEN",
                semantic_id=semantic_id,
                spec=spec,
                ast_path=ctx.path,
                hint="Payloads must not contain Div blocks",
            )

        # Check raw content permission
        if node_type in RAW_TYPES:
            if not allow_raw:
                raise ValidationError(
                    f"Raw content ({node_type}) not allowed in table payload",
                    code=f"VAL_PANDOC_{node_type.upper()}_FORBIDDEN",
                    semantic_id=semantic_id,
                    spec=spec,
                    ast_path=ctx.path,
                    hint="Set allow_raw_pandoc=True in config to allow raw content",
                )

        # Check against allowlists (only for content blocks/inlines, not structure)
        if ctx.context == NodeContext.BLOCK:
            if node_type in ALL_BLOCK_TYPES and node_type not in allowed_block_types:
                raise ValidationError(
                    f"Block type '{node_type}' not allowed in table cells",
                    code="VAL_PANDOC_BLOCK_NOT_ALLOWED",
                    semantic_id=semantic_id,
                    spec=spec,
                    ast_path=ctx.path,
                )
        elif ctx.context == NodeContext.INLINE:
            if node_type in ALL_INLINE_TYPES and node_type not in allowed_inline_types:
                raise ValidationError(
                    f"Inline type '{node_type}' not allowed in table cells",
                    code="VAL_PANDOC_INLINE_NOT_ALLOWED",
                    semantic_id=semantic_id,
                    spec=spec,
                    ast_path=ctx.path,
                )

    # Walk the entire payload
    walk_pandoc(payload, safety_check, semantic_id, path="Table")

    # Validate table structure
    _validate_table_structure(content, semantic_id, spec, limits, check_geometry)


def _validate_table_structure(
    content: list,
    semantic_id: str,
    spec: str,
    limits: ResolutionLimits | None,
    check_geometry: bool,
) -> None:
    """Validate Table structural integrity and geometry."""

    # c[0]: Attr
    # c[1]: Caption
    # c[2]: ColSpecs
    # c[3]: TableHead
    # c[4]: [TableBody]
    # c[5]: TableFoot

    col_specs = content[2]
    table_head = content[3]
    table_bodies = content[4]
    table_foot = content[5]

    # Determine column count from ColSpecs
    if not isinstance(col_specs, list):
        raise ValidationError(
            "Table ColSpecs must be an array",
            code="VAL_PANDOC_COLSPECS_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    num_cols = len(col_specs)
    if num_cols == 0:
        raise ValidationError(
            "Table must have at least one column",
            code="VAL_PANDOC_NO_COLUMNS",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Validate TableHead
    _validate_table_section(table_head, "TableHead", num_cols, semantic_id, spec, check_geometry)

    # Validate TableBody sections
    if not isinstance(table_bodies, list):
        raise ValidationError(
            "Table bodies must be an array",
            code="VAL_PANDOC_BODIES_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    total_rows = 0
    total_cells = 0

    for i, body in enumerate(table_bodies):
        rows, cells = _validate_table_body(body, i, num_cols, semantic_id, spec, check_geometry)
        total_rows += rows
        total_cells += cells

    # Validate TableFoot
    _validate_table_section(table_foot, "TableFoot", num_cols, semantic_id, spec, check_geometry)

    # Count rows from head/foot
    if isinstance(table_head, dict):
        head_rows = table_head.get("c", [None, []])[1]
        if isinstance(head_rows, list):
            total_rows += len(head_rows)
            for row in head_rows:
                if isinstance(row, dict):
                    cells = row.get("c", [None, []])[1]
                    if isinstance(cells, list):
                        total_cells += len(cells)

    if isinstance(table_foot, dict):
        foot_rows = table_foot.get("c", [None, []])[1]
        if isinstance(foot_rows, list):
            total_rows += len(foot_rows)
            for row in foot_rows:
                if isinstance(row, dict):
                    cells = row.get("c", [None, []])[1]
                    if isinstance(cells, list):
                        total_cells += len(cells)

    # Apply size limits
    if limits:
        if num_cols > limits.max_table_cols:
            raise ValidationError(
                f"Table exceeds max columns ({num_cols} > {limits.max_table_cols})",
                code="VAL_PANDOC_EXCEEDS_MAX_COLS",
                semantic_id=semantic_id,
                spec=spec,
            )
        if total_rows > limits.max_table_rows:
            raise ValidationError(
                f"Table exceeds max rows ({total_rows} > {limits.max_table_rows})",
                code="VAL_PANDOC_EXCEEDS_MAX_ROWS",
                semantic_id=semantic_id,
                spec=spec,
            )
        if total_cells > limits.max_table_cells:
            raise ValidationError(
                f"Table exceeds max cells ({total_cells} > {limits.max_table_cells})",
                code="VAL_PANDOC_EXCEEDS_MAX_CELLS",
                semantic_id=semantic_id,
                spec=spec,
            )


def _validate_table_section(
    section: Any,
    section_name: str,
    num_cols: int,
    semantic_id: str,
    spec: str,
    check_geometry: bool,
) -> None:
    """Validate TableHead or TableFoot."""
    if not isinstance(section, dict):
        raise ValidationError(
            f"{section_name} must be an object",
            code=f"VAL_PANDOC_{section_name.upper()}_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    if section.get("t") != section_name:
        raise ValidationError(
            f"Expected {section_name}, got {section.get('t')}",
            code=f"VAL_PANDOC_{section_name.upper()}_WRONG_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    content = section.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        raise ValidationError(
            f"Invalid {section_name} structure",
            code=f"VAL_PANDOC_{section_name.upper()}_STRUCTURE",
            semantic_id=semantic_id,
            spec=spec,
        )

    rows = content[1]
    if not isinstance(rows, list):
        raise ValidationError(
            f"{section_name} rows must be an array",
            code=f"VAL_PANDOC_{section_name.upper()}_ROWS_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    for i, row in enumerate(rows):
        _validate_row(row, i, section_name, num_cols, semantic_id, spec, check_geometry)


def _validate_table_body(
    body: Any,
    body_idx: int,
    num_cols: int,
    semantic_id: str,
    spec: str,
    check_geometry: bool,
) -> tuple[int, int]:
    """Validate a TableBody section. Returns (row_count, cell_count)."""
    if not isinstance(body, dict):
        raise ValidationError(
            f"TableBody[{body_idx}] must be an object",
            code="VAL_PANDOC_TABLEBODY_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    if body.get("t") != "TableBody":
        raise ValidationError(
            f"Expected TableBody, got {body.get('t')}",
            code="VAL_PANDOC_TABLEBODY_WRONG_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    content = body.get("c", [])
    if not isinstance(content, list) or len(content) < 4:
        raise ValidationError(
            f"Invalid TableBody[{body_idx}] structure",
            code="VAL_PANDOC_TABLEBODY_STRUCTURE",
            semantic_id=semantic_id,
            spec=spec,
            hint="TableBody.c should be [Attr, RowHeadColumns, [Row], [Row]]",
        )

    # content[2]: intermediate head rows
    # content[3]: body rows
    intermediate_rows = content[2]
    body_rows = content[3]

    row_count = 0
    cell_count = 0

    if isinstance(intermediate_rows, list):
        for i, row in enumerate(intermediate_rows):
            cells = _validate_row(row, i, f"TableBody[{body_idx}].intermediate", num_cols, semantic_id, spec, check_geometry)
            row_count += 1
            cell_count += cells

    if isinstance(body_rows, list):
        for i, row in enumerate(body_rows):
            cells = _validate_row(row, i, f"TableBody[{body_idx}]", num_cols, semantic_id, spec, check_geometry)
            row_count += 1
            cell_count += cells

    return row_count, cell_count


def _validate_row(
    row: Any,
    row_idx: int,
    context: str,
    num_cols: int,
    semantic_id: str,
    spec: str,
    check_geometry: bool,
) -> int:
    """Validate a Row. Returns cell count."""
    if not isinstance(row, dict):
        raise ValidationError(
            f"{context}.rows[{row_idx}] must be an object",
            code="VAL_PANDOC_ROW_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    if row.get("t") != "Row":
        raise ValidationError(
            f"Expected Row, got {row.get('t')}",
            code="VAL_PANDOC_ROW_WRONG_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    content = row.get("c", [])
    if not isinstance(content, list) or len(content) < 2:
        raise ValidationError(
            f"Invalid Row structure at {context}.rows[{row_idx}]",
            code="VAL_PANDOC_ROW_STRUCTURE",
            semantic_id=semantic_id,
            spec=spec,
        )

    cells = content[1]
    if not isinstance(cells, list):
        raise ValidationError(
            f"{context}.rows[{row_idx}] cells must be an array",
            code="VAL_PANDOC_ROW_CELLS_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    # Track column occupancy for geometry check
    if check_geometry:
        col_position = 0

    for i, cell in enumerate(cells):
        rowspan, colspan = _validate_cell(cell, i, f"{context}.rows[{row_idx}]", semantic_id, spec)

        if check_geometry:
            # Check colspan doesn't exceed remaining columns
            if col_position + colspan > num_cols:
                raise ValidationError(
                    f"Cell colspan exceeds table width at {context}.rows[{row_idx}].cells[{i}]",
                    code="VAL_PANDOC_COLSPAN_OVERFLOW",
                    semantic_id=semantic_id,
                    spec=spec,
                    hint=f"Cell at column {col_position} has colspan={colspan} but only {num_cols - col_position} columns remain",
                )
            col_position += colspan

    return len(cells)


def _validate_cell(
    cell: Any,
    cell_idx: int,
    context: str,
    semantic_id: str,
    spec: str,
) -> tuple[int, int]:
    """Validate a Cell. Returns (rowspan, colspan)."""
    if not isinstance(cell, dict):
        raise ValidationError(
            f"{context}.cells[{cell_idx}] must be an object",
            code="VAL_PANDOC_CELL_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    if cell.get("t") != "Cell":
        raise ValidationError(
            f"Expected Cell, got {cell.get('t')}",
            code="VAL_PANDOC_CELL_WRONG_TYPE",
            semantic_id=semantic_id,
            spec=spec,
        )

    content = cell.get("c", [])
    if not isinstance(content, list) or len(content) < 5:
        raise ValidationError(
            f"Invalid Cell structure at {context}.cells[{cell_idx}]",
            code="VAL_PANDOC_CELL_STRUCTURE",
            semantic_id=semantic_id,
            spec=spec,
            hint="Cell.c should be [Attr, Alignment, RowSpan, ColSpan, [Block]]",
        )

    # c[2]: RowSpan (int >= 1)
    rowspan = content[2]
    if not isinstance(rowspan, int) or rowspan < 1:
        raise ValidationError(
            f"Invalid RowSpan at {context}.cells[{cell_idx}]: {rowspan}",
            code="VAL_PANDOC_ROWSPAN_INVALID",
            semantic_id=semantic_id,
            spec=spec,
            hint="RowSpan must be a positive integer",
        )

    # c[3]: ColSpan (int >= 1)
    colspan = content[3]
    if not isinstance(colspan, int) or colspan < 1:
        raise ValidationError(
            f"Invalid ColSpan at {context}.cells[{cell_idx}]: {colspan}",
            code="VAL_PANDOC_COLSPAN_INVALID",
            semantic_id=semantic_id,
            spec=spec,
            hint="ColSpan must be a positive integer",
        )

    # c[4]: [Block] - validated by walker

    return rowspan, colspan
