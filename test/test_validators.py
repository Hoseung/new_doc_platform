"""
Comprehensive tests for payload validators.

Tests based on plan_validation.md checklist:
- Bool-as-number bug
- Hidden RawInline detection
- Dtype enforcement
- Document AST validation
"""

import math
import pytest

from litepub_norm.resolver.errors import ValidationError
from litepub_norm.resolver.config import ResolutionConfig, ResolutionLimits
from litepub_norm.resolver.validators import (
    validate_metric_v1,
    validate_table_simple_v1,
    validate_table_pandoc_v1,
    validate_figure_meta_v1,
    validate_resolved_document,
    walk_pandoc,
    WalkContext,
    collect_all_types,
)


class TestMetricValidator:
    """Tests for metric.json@v1 validator."""

    def test_valid_metric(self):
        """Valid metric passes validation."""
        payload = {"label": "Test Metric", "value": 42.5, "unit": "deg"}
        validate_metric_v1(payload, "test.metric")  # Should not raise

    def test_valid_metric_dimensionless(self):
        """Valid metric with empty unit (dimensionless) passes."""
        payload = {"label": "Ratio", "value": 0.95, "unit": ""}
        validate_metric_v1(payload, "test.metric")  # Should not raise

    def test_value_bool_fails(self):
        """value=True fails (bool-as-number bug)."""
        payload = {"label": "Test", "value": True}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_VALUE_BOOL"

    def test_value_bool_false_fails(self):
        """value=False also fails (bool-as-number bug)."""
        payload = {"label": "Test", "value": False}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_VALUE_BOOL"

    def test_value_nan_fails(self):
        """value=NaN fails validation."""
        payload = {"label": "Test", "value": float("nan")}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_VALUE_NONFINITE"

    def test_value_inf_fails(self):
        """value=Infinity fails validation."""
        payload = {"label": "Test", "value": float("inf")}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_VALUE_NONFINITE"

    def test_value_negative_inf_fails(self):
        """value=-Infinity fails validation."""
        payload = {"label": "Test", "value": float("-inf")}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_VALUE_NONFINITE"

    def test_label_empty_fails(self):
        """label="" fails validation."""
        payload = {"label": "", "value": 1.0}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_LABEL_EMPTY"

    def test_label_whitespace_only_fails(self):
        """label with only whitespace fails."""
        payload = {"label": "   ", "value": 1.0}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_LABEL_EMPTY"

    def test_notes_non_string_fails(self):
        """notes=[1,2] fails validation."""
        payload = {"label": "Test", "value": 1.0, "notes": [1, 2]}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric")
        assert exc_info.value.code == "VAL_METRIC_NOTES_ITEM_TYPE"

    def test_format_valid_tokens(self):
        """format with {value} and {unit} passes."""
        payload = {"label": "Test", "value": 1.0, "format": "{value} {unit}"}
        validate_metric_v1(payload, "test.metric")  # Should not raise

    def test_format_invalid_token_fails(self):
        """format with invalid tokens fails in strict mode."""
        # {label} is not an allowed token (only {value} and {unit} are allowed)
        payload = {"label": "Test", "value": 1.0, "format": "Result: {label} = {value}"}
        with pytest.raises(ValidationError) as exc_info:
            validate_metric_v1(payload, "test.metric", strict_format=True)
        assert exc_info.value.code == "VAL_METRIC_FORMAT_INVALID_TOKEN"

    def test_format_python_mini_language_passes(self):
        """format with Python mini-language passes (not parsed as tokens)."""
        # {value:.2f} doesn't match the simple \{(\w+)\} pattern
        # so it's allowed even in strict mode
        payload = {"label": "Test", "value": 1.0, "format": "{value:.2f} {unit}"}
        validate_metric_v1(payload, "test.metric", strict_format=True)  # Should not raise

    def test_format_non_strict_allows_any_tokens(self):
        """format with any tokens passes in non-strict mode."""
        payload = {"label": "Test", "value": 1.0, "format": "{label}: {value} {custom}"}
        validate_metric_v1(payload, "test.metric", strict_format=False)  # Should not raise


class TestSimpleTableValidator:
    """Tests for table.simple.json@v1 validator."""

    def test_valid_table(self):
        """Valid table passes validation."""
        payload = {
            "columns": [
                {"key": "name", "label": "Name"},
                {"key": "value", "label": "Value", "dtype": "float"},
            ],
            "rows": [
                {"name": "A", "value": 1.0},
                {"name": "B", "value": 2.0},
            ],
        }
        validate_table_simple_v1(payload, "test.table")  # Should not raise

    def test_duplicate_column_keys_fails(self):
        """Duplicate column keys fails."""
        payload = {
            "columns": [
                {"key": "name"},
                {"key": "name"},  # Duplicate
            ],
            "rows": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_COLUMN_KEY_DUPLICATE"

    def test_row_extra_key_fails(self):
        """Row with extra key fails."""
        payload = {
            "columns": [{"key": "name"}],
            "rows": [{"name": "A", "extra": "B"}],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_ROW_EXTRA_KEYS"

    def test_row_missing_key_fails_strict(self):
        """Row missing key fails in strict mode (Policy S)."""
        payload = {
            "columns": [{"key": "name"}, {"key": "value"}],
            "rows": [{"name": "A"}],  # Missing 'value'
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table", strict_keys=True)
        assert exc_info.value.code == "VAL_TABLE_ROW_MISSING_KEYS"

    def test_row_missing_key_passes_permissive(self):
        """Row missing key passes in permissive mode (Policy P)."""
        payload = {
            "columns": [{"key": "name"}, {"key": "value"}],
            "rows": [{"name": "A"}],  # Missing 'value'
        }
        validate_table_simple_v1(payload, "test.table", strict_keys=False)  # Should not raise

    def test_dtype_mismatch_fails(self):
        """Dtype mismatch fails."""
        payload = {
            "columns": [{"key": "count", "dtype": "int"}],
            "rows": [{"count": "not an int"}],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_DTYPE_MISMATCH"

    def test_bool_in_int_dtype_fails(self):
        """Bool in int dtype fails."""
        payload = {
            "columns": [{"key": "count", "dtype": "int"}],
            "rows": [{"count": True}],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_DTYPE_BOOL_AS_INT"

    def test_bool_in_float_dtype_fails(self):
        """Bool in float dtype fails."""
        payload = {
            "columns": [{"key": "value", "dtype": "float"}],
            "rows": [{"value": False}],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_DTYPE_BOOL_AS_FLOAT"

    def test_nan_in_float_dtype_fails(self):
        """NaN in float dtype fails."""
        payload = {
            "columns": [{"key": "value", "dtype": "float"}],
            "rows": [{"value": float("nan")}],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_DTYPE_FLOAT_NONFINITE"

    def test_null_value_allowed(self):
        """Null value is always allowed."""
        payload = {
            "columns": [{"key": "value", "dtype": "int"}],
            "rows": [{"value": None}],
        }
        validate_table_simple_v1(payload, "test.table")  # Should not raise

    def test_huge_table_triggers_limit(self):
        """Huge table triggers size limit."""
        limits = ResolutionLimits(max_table_rows=10)
        payload = {
            "columns": [{"key": "x"}],
            "rows": [{"x": i} for i in range(20)],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table", limits)
        assert exc_info.value.code == "VAL_TABLE_EXCEEDS_MAX_ROWS"

    def test_invalid_column_key_fails(self):
        """Invalid column key (starts with digit) fails."""
        payload = {
            "columns": [{"key": "123invalid"}],
            "rows": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_table_simple_v1(payload, "test.table")
        assert exc_info.value.code == "VAL_TABLE_COLUMN_KEY_INVALID"


class TestPandocTableValidator:
    """Tests for table.pandoc.json@v1 validator."""

    def _make_simple_table(self, cells_content=None, num_cols=1):
        """Create a minimal valid Pandoc Table.

        Args:
            cells_content: List of rows, each row is a list of block content for cells.
                           Each cell content is a dict (single block) or list of blocks.
            num_cols: Number of columns (for ColSpecs).
        """
        if cells_content is None:
            cells_content = [[{"t": "Plain", "c": [{"t": "Str", "c": "Test"}]}]]

        rows = []
        for row_cells in cells_content:
            cells = []
            for cell_blocks in row_cells:
                # Ensure cell_blocks is a list of blocks
                if isinstance(cell_blocks, dict):
                    blocks = [cell_blocks]
                else:
                    blocks = cell_blocks

                cell = {
                    "t": "Cell",
                    "c": [
                        ["", [], []],  # Attr
                        {"t": "AlignDefault"},  # Alignment
                        1,  # RowSpan
                        1,  # ColSpan
                        blocks,  # [Block]
                    ],
                }
                cells.append(cell)
            row = {"t": "Row", "c": [["", [], []], cells]}
            rows.append(row)

        # Create ColSpecs for each column
        col_specs = [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(num_cols)]

        return {
            "t": "Table",
            "c": [
                ["", [], []],  # Attr
                [None, []],  # Caption
                col_specs,  # ColSpecs
                {"t": "TableHead", "c": [["", [], []], []]},  # TableHead
                [{"t": "TableBody", "c": [["", [], []], 0, [], rows]}],  # [TableBody]
                {"t": "TableFoot", "c": [["", [], []], []]},  # TableFoot
            ],
        }

    def test_valid_table(self):
        """Valid Pandoc table passes validation."""
        table = self._make_simple_table()
        config = ResolutionConfig()
        validate_table_pandoc_v1(table, "test.table", config)  # Should not raise

    def test_raw_inline_rejected_safe_mode(self):
        """RawInline is rejected in safe mode."""
        table = self._make_simple_table([[
            {"t": "Para", "c": [{"t": "RawInline", "c": ["html", "<script>evil()</script>"]}]}
        ]])
        config = ResolutionConfig(allow_raw_pandoc=False)
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert "RAWINLINE" in exc_info.value.code

    def test_raw_inline_in_bullet_list_detected(self):
        """RawInline buried in BulletList inside cell is detected and rejected."""
        # This tests the plan's requirement that nested content is fully traversed
        bullet_list = {
            "t": "BulletList",
            "c": [
                [{"t": "Plain", "c": [{"t": "RawInline", "c": ["html", "<b>hidden</b>"]}]}]
            ],
        }
        table = self._make_simple_table([[bullet_list]])
        config = ResolutionConfig(allow_raw_pandoc=False)
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert "RAWINLINE" in exc_info.value.code

    def test_raw_block_rejected_safe_mode(self):
        """RawBlock is rejected in safe mode."""
        table = self._make_simple_table([[
            {"t": "RawBlock", "c": ["html", "<div>evil</div>"]}
        ]])
        config = ResolutionConfig(allow_raw_pandoc=False)
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert "RAWBLOCK" in exc_info.value.code

    def test_div_rejected_always(self):
        """Div is rejected even in allow_raw mode."""
        table = self._make_simple_table([[
            {"t": "Div", "c": [["", [], []], [{"t": "Para", "c": [{"t": "Str", "c": "test"}]}]]}
        ]])
        config = ResolutionConfig(allow_raw_pandoc=True)
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert "DIV" in exc_info.value.code

    def test_raw_allowed_with_config(self):
        """RawInline is allowed when config.allow_raw_pandoc=True."""
        table = self._make_simple_table([[
            {"t": "Para", "c": [{"t": "RawInline", "c": ["html", "<b>ok</b>"]}]}
        ]])
        config = ResolutionConfig(allow_raw_pandoc=True)
        validate_table_pandoc_v1(table, "test.table", config)  # Should not raise

    def test_rowspan_zero_fails(self):
        """rowspan=0 fails."""
        table = self._make_simple_table()
        # Modify the cell to have rowspan=0
        table["c"][4][0]["c"][3][0]["c"][1][0]["c"][2] = 0
        config = ResolutionConfig()
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert exc_info.value.code == "VAL_PANDOC_ROWSPAN_INVALID"

    def test_colspan_zero_fails(self):
        """colspan=0 fails."""
        table = self._make_simple_table()
        # Modify the cell to have colspan=0
        table["c"][4][0]["c"][3][0]["c"][1][0]["c"][3] = 0
        config = ResolutionConfig()
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert exc_info.value.code == "VAL_PANDOC_COLSPAN_INVALID"

    def test_colspan_overflow_fails(self):
        """Colspan exceeding table width fails."""
        table = self._make_simple_table()
        # Modify the cell to have colspan=5 (but table has 1 column)
        table["c"][4][0]["c"][3][0]["c"][1][0]["c"][3] = 5
        config = ResolutionConfig()
        with pytest.raises(ValidationError) as exc_info:
            validate_table_pandoc_v1(table, "test.table", config)
        assert exc_info.value.code == "VAL_PANDOC_COLSPAN_OVERFLOW"


class TestFigureMetaValidator:
    """Tests for figure.meta.json@v1 validator."""

    def test_valid_meta(self):
        """Valid figure metadata passes."""
        payload = {
            "caption": "A figure",
            "alt": "Description",
            "notes": ["Note 1"],
        }
        validate_figure_meta_v1(payload, "test.figure")  # Should not raise

    def test_none_payload_passes(self):
        """None payload (no sidecar) passes."""
        validate_figure_meta_v1(None, "test.figure")  # Should not raise

    def test_notes_not_list_fails(self):
        """notes not list[str] fails."""
        payload = {"notes": "not a list"}
        with pytest.raises(ValidationError) as exc_info:
            validate_figure_meta_v1(payload, "test.figure")
        assert exc_info.value.code == "VAL_FIGURE_NOTES_TYPE"

    def test_notes_non_string_item_fails(self):
        """notes with non-string item fails."""
        payload = {"notes": ["valid", 123]}
        with pytest.raises(ValidationError) as exc_info:
            validate_figure_meta_v1(payload, "test.figure")
        assert exc_info.value.code == "VAL_FIGURE_NOTES_ITEM_TYPE"

    def test_caption_non_string_fails(self):
        """caption non-string fails."""
        payload = {"caption": 123}
        with pytest.raises(ValidationError) as exc_info:
            validate_figure_meta_v1(payload, "test.figure")
        assert exc_info.value.code == "VAL_FIGURE_CAPTION_TYPE"


class TestPandocWalker:
    """Tests for the generic Pandoc walker."""

    def test_collects_all_types(self):
        """Walker collects all node types."""
        node = {
            "t": "Para",
            "c": [
                {"t": "Str", "c": "Hello"},
                {"t": "Space"},
                {"t": "Strong", "c": [{"t": "Str", "c": "world"}]},
            ],
        }
        types = collect_all_types(node, "test")
        assert "Para" in types
        assert "Str" in types
        assert "Space" in types
        assert "Strong" in types

    def test_walks_nested_bullet_list(self):
        """Walker traverses nested BulletList."""
        node = {
            "t": "BulletList",
            "c": [
                [{"t": "Plain", "c": [{"t": "Str", "c": "item1"}]}],
                [{"t": "Plain", "c": [{"t": "Emph", "c": [{"t": "Str", "c": "item2"}]}]}],
            ],
        }
        types = collect_all_types(node, "test")
        assert "BulletList" in types
        assert "Plain" in types
        assert "Str" in types
        assert "Emph" in types

    def test_walks_definition_list(self):
        """Walker traverses DefinitionList."""
        node = {
            "t": "DefinitionList",
            "c": [
                (
                    [{"t": "Str", "c": "term"}],
                    [[{"t": "Para", "c": [{"t": "Str", "c": "definition"}]}]],
                ),
            ],
        }
        types = collect_all_types(node, "test")
        assert "DefinitionList" in types
        assert "Para" in types
        assert "Str" in types


class TestDocumentValidator:
    """Tests for post-resolution document validator."""

    def _make_resolved_doc(self, blocks):
        """Create a minimal resolved document."""
        return {
            "pandoc-api-version": [1, 23],
            "meta": {},
            "blocks": blocks,
        }

    def _make_wrapper_div(self, semantic_id, content, role="computed", kind="metric"):
        """Create a wrapper Div."""
        return {
            "t": "Div",
            "c": [
                [semantic_id, [], [["role", role], ["kind", kind]]],
                content,
            ],
        }

    def test_valid_resolved_document(self):
        """Valid resolved document passes."""
        table = {"t": "Table", "c": [[], [], [], {"t": "TableHead", "c": [[], []]}, [], {"t": "TableFoot", "c": [[], []]}]}
        wrapper = self._make_wrapper_div("test.metric", [table])
        doc = self._make_resolved_doc([wrapper])
        result = validate_resolved_document(doc, fail_fast=False)
        assert result.valid

    def test_leftover_placeholder_fails(self):
        """Leftover placeholder fails."""
        placeholder = {"t": "Para", "c": [{"t": "Str", "c": "[[COMPUTED:METRIC]]"}]}
        wrapper = self._make_wrapper_div("test.metric", [placeholder])
        doc = self._make_resolved_doc([wrapper])
        with pytest.raises(ValidationError) as exc_info:
            validate_resolved_document(doc, fail_fast=True)
        assert exc_info.value.code == "VAL_DOC_UNRESOLVED_PLACEHOLDER"

    def test_duplicate_semantic_ids_fail(self):
        """Duplicate semantic IDs fail."""
        table = {"t": "Table", "c": [[], [], [], {"t": "TableHead", "c": [[], []]}, [], {"t": "TableFoot", "c": [[], []]}]}
        wrapper1 = self._make_wrapper_div("test.metric", [table])
        wrapper2 = self._make_wrapper_div("test.metric", [table])  # Same ID
        doc = self._make_resolved_doc([wrapper1, wrapper2])
        with pytest.raises(ValidationError) as exc_info:
            validate_resolved_document(doc, fail_fast=True)
        assert exc_info.value.code == "VAL_DOC_DUPLICATE_ID"

    def test_raw_block_fails_in_dossier(self):
        """Raw block anywhere fails in dossier build."""
        raw = {"t": "RawBlock", "c": ["html", "<div>test</div>"]}
        doc = self._make_resolved_doc([raw])
        config = ResolutionConfig(target="dossier", allow_raw_pandoc=False)
        with pytest.raises(ValidationError) as exc_info:
            validate_resolved_document(doc, config, fail_fast=True)
        assert "RAWBLOCK" in exc_info.value.code

    def test_collect_errors_mode(self):
        """Collect all errors when fail_fast=False."""
        placeholder1 = {"t": "Para", "c": [{"t": "Str", "c": "[[COMPUTED:METRIC]]"}]}
        placeholder2 = {"t": "Para", "c": [{"t": "Str", "c": "[[COMPUTED:TABLE]]"}]}
        wrapper1 = self._make_wrapper_div("test.metric1", [placeholder1])
        wrapper2 = self._make_wrapper_div("test.metric2", [placeholder2])
        doc = self._make_resolved_doc([wrapper1, wrapper2])

        result = validate_resolved_document(doc, fail_fast=False)
        assert not result.valid
        assert len(result.errors) >= 2  # At least 2 placeholder errors
