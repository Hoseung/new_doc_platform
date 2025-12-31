"""
Comprehensive tests for the filter pipeline.

Tests based on plan_filters.md:
- Visibility filter: removes correct wrappers
- Policy filter: removes wrappers with forbidden tags
- Metadata strip: strips keys and keeps protected attrs
- Presentation: PDF/HTML transformations
- Pipeline order: deterministic ordering
"""

import copy
import json
import pytest

from litepub_norm.filters import (
    apply_filters,
    apply_filter,
    BuildContext,
    FilterConfig,
    FilterReport,
    filter_visibility,
    filter_policy,
    filter_metadata_strip,
    filter_presentation,
)
from litepub_norm.filters.utils.wrappers import (
    get_wrapper_id,
    get_wrapper_attr,
    is_semantic_wrapper,
    iter_wrappers,
)


# ============================================================================
# Test Fixtures
# ============================================================================

def make_wrapper_div(
    semantic_id: str,
    role: str = "computed",
    kind: str = "table",
    visibility: str = "internal",
    policies: list[str] | None = None,
    extra_attrs: dict[str, str] | None = None,
    content: list | None = None,
) -> dict:
    """Create a semantic wrapper Div for testing."""
    attrs = [
        ["role", role],
        ["kind", kind],
        ["visibility", visibility],
    ]
    if policies:
        attrs.append(["policies", ",".join(policies)])
    if extra_attrs:
        for k, v in extra_attrs.items():
            attrs.append([k, v])

    classes = policies or []

    inner_content = content or [
        {"t": "Para", "c": [{"t": "Str", "c": f"Content for {semantic_id}"}]}
    ]

    return {
        "t": "Div",
        "c": [
            [semantic_id, classes, attrs],
            inner_content,
        ],
    }


def make_ast(blocks: list) -> dict:
    """Create a minimal Pandoc AST."""
    return {
        "pandoc-api-version": [1, 23],
        "meta": {},
        "blocks": blocks,
    }


# ============================================================================
# Test: Visibility Filter
# ============================================================================

class TestVisibilityFilter:
    """Tests for visibility filter."""

    def test_internal_build_keeps_all(self):
        """Internal build keeps all visibility levels."""
        ast = make_ast([
            make_wrapper_div("internal-1", visibility="internal"),
            make_wrapper_div("external-1", visibility="external"),
            make_wrapper_div("dossier-1", visibility="dossier"),
        ])

        context = BuildContext(build_target="internal")
        result_ast, report = filter_visibility(ast, FilterConfig(), context)

        # All wrappers should remain
        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert wrapper_ids == {"internal-1", "external-1", "dossier-1"}
        assert len(report) == 0

    def test_external_removes_internal_only(self):
        """External build removes internal-only wrappers."""
        ast = make_ast([
            make_wrapper_div("internal-1", visibility="internal"),
            make_wrapper_div("external-1", visibility="external"),
            make_wrapper_div("dossier-1", visibility="dossier"),
        ])

        context = BuildContext(build_target="external")
        result_ast, report = filter_visibility(ast, FilterConfig(), context)

        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert wrapper_ids == {"external-1", "dossier-1"}
        assert len(report) == 1
        assert report.entries[0].reason_code == "VIS_REMOVED_INTERNAL_ONLY"

    def test_dossier_keeps_only_dossier(self):
        """Dossier build keeps only dossier-visibility wrappers."""
        ast = make_ast([
            make_wrapper_div("internal-1", visibility="internal"),
            make_wrapper_div("external-1", visibility="external"),
            make_wrapper_div("dossier-1", visibility="dossier"),
        ])

        context = BuildContext(build_target="dossier")
        result_ast, report = filter_visibility(ast, FilterConfig(), context)

        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert wrapper_ids == {"dossier-1"}
        assert len(report) == 2

    def test_removal_preserves_structure(self):
        """Removal preserves surrounding AST structure."""
        ast = make_ast([
            {"t": "Para", "c": [{"t": "Str", "c": "Before"}]},
            make_wrapper_div("internal-1", visibility="internal"),
            {"t": "Para", "c": [{"t": "Str", "c": "After"}]},
        ])

        context = BuildContext(build_target="external")
        result_ast, report = filter_visibility(ast, FilterConfig(), context)

        assert len(result_ast["blocks"]) == 2
        assert result_ast["blocks"][0]["t"] == "Para"
        assert result_ast["blocks"][1]["t"] == "Para"


# ============================================================================
# Test: Policy Filter
# ============================================================================

class TestPolicyFilter:
    """Tests for policy filter."""

    def test_single_tag_removal(self):
        """Single forbidden tag removes wrapper."""
        ast = make_ast([
            make_wrapper_div("normal-1", visibility="external"),
            make_wrapper_div("draft-1", visibility="external", policies=["draft"]),
        ])

        context = BuildContext(build_target="external")
        result_ast, report = filter_policy(ast, FilterConfig(), context)

        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert wrapper_ids == {"normal-1"}
        assert len(report) == 1
        assert "POL_REMOVED_TAG:draft" == report.entries[0].reason_code

    def test_multiple_tags_deterministic_reason(self):
        """Multiple forbidden tags use sorted first tag in reason code."""
        ast = make_ast([
            make_wrapper_div("multi-1", visibility="external",
                           policies=["wip", "draft", "internal-only"]),
        ])

        context = BuildContext(build_target="external")
        result_ast, report = filter_policy(ast, FilterConfig(), context)

        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert len(wrapper_ids) == 0
        assert len(report) == 1
        # Sorted order: draft < internal-only < wip
        assert report.entries[0].reason_code == "POL_REMOVED_TAG:draft"
        # All matching tags should be in details
        assert set(report.entries[0].details["matching_policies"]) == {
            "draft", "internal-only", "wip"
        }

    def test_internal_allows_all_policies(self):
        """Internal build has no forbidden policies."""
        ast = make_ast([
            make_wrapper_div("draft-1", visibility="internal", policies=["draft"]),
        ])

        context = BuildContext(build_target="internal")
        result_ast, report = filter_policy(ast, FilterConfig(), context)

        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert wrapper_ids == {"draft-1"}
        assert len(report) == 0


# ============================================================================
# Test: Metadata Strip Filter
# ============================================================================

class TestMetadataStripFilter:
    """Tests for metadata strip filter."""

    def test_internal_keeps_provenance(self):
        """Internal build keeps all provenance attributes."""
        ast = make_ast([
            make_wrapper_div(
                "table-1",
                visibility="internal",
                extra_attrs={
                    "producer": "analysis-v1",
                    "run_id": "run-123",
                    "sha256": "abc123",
                },
            ),
        ])

        context = BuildContext(build_target="internal")
        result_ast, report = filter_metadata_strip(ast, FilterConfig(), context)

        for div, _, _ in iter_wrappers(result_ast):
            assert get_wrapper_attr(div, "producer") == "analysis-v1"
            assert get_wrapper_attr(div, "run_id") == "run-123"
            assert get_wrapper_attr(div, "sha256") == "abc123"
        assert len(report) == 0

    def test_external_strips_provenance(self):
        """External build strips provenance attributes."""
        ast = make_ast([
            make_wrapper_div(
                "table-1",
                visibility="external",
                extra_attrs={
                    "producer": "analysis-v1",
                    "run_id": "run-123",
                    "sha256": "abc123",
                },
            ),
        ])

        context = BuildContext(build_target="external")
        result_ast, report = filter_metadata_strip(ast, FilterConfig(), context)

        for div, _, _ in iter_wrappers(result_ast):
            assert get_wrapper_attr(div, "producer") is None
            assert get_wrapper_attr(div, "run_id") is None
            assert get_wrapper_attr(div, "sha256") is None
            # Protected attrs should remain
            assert get_wrapper_attr(div, "role") == "computed"
            assert get_wrapper_attr(div, "visibility") == "external"

        assert len(report) == 1
        assert report.entries[0].reason_code == "META_STRIP_ATTRS"

    def test_protected_keys_never_stripped(self):
        """Protected keys (role, kind, visibility) are never stripped."""
        ast = make_ast([
            make_wrapper_div("table-1", visibility="dossier"),
        ])

        context = BuildContext(build_target="dossier")
        result_ast, _ = filter_metadata_strip(ast, FilterConfig(), context)

        for div, _, _ in iter_wrappers(result_ast):
            assert get_wrapper_attr(div, "role") == "computed"
            assert get_wrapper_attr(div, "kind") == "table"
            assert get_wrapper_attr(div, "visibility") == "dossier"


# ============================================================================
# Test: Presentation Filter (PDF)
# ============================================================================

class TestPresentationFilterPDF:
    """Tests for PDF presentation filter."""

    def test_pdf_externalizes_long_code_blocks(self):
        """PDF mode externalizes code blocks exceeding thresholds."""
        long_code = "x = 1\n" * 100  # 100 lines

        ast = make_ast([
            {"t": "CodeBlock", "c": [["", ["python"], []], long_code]},
        ])

        context = BuildContext(build_target="internal", render_target="pdf")
        result_ast, report = filter_presentation(ast, FilterConfig(), context)

        # Code block should be replaced with stub
        blocks = result_ast["blocks"]
        assert blocks[0]["t"] == "Para"  # Stub paragraph

        assert len(report) == 1
        assert report.entries[0].reason_code == "PRES_PDF_CODEBLOCK_EXTERNALIZED"

    def test_pdf_preserves_short_code_blocks(self):
        """PDF mode preserves code blocks under thresholds."""
        short_code = "x = 1\ny = 2\n"

        ast = make_ast([
            {"t": "CodeBlock", "c": [["", ["python"], []], short_code]},
        ])

        context = BuildContext(build_target="internal", render_target="pdf")
        result_ast, report = filter_presentation(ast, FilterConfig(), context)

        # Code block should remain unchanged
        assert result_ast["blocks"][0]["t"] == "CodeBlock"
        assert len(report) == 0

    def test_pdf_moves_additional_to_appendix(self):
        """PDF mode moves long additional sections to appendix."""
        # Create a long additional section
        long_content = [
            {"t": "Para", "c": [{"t": "Str", "c": "Paragraph " + str(i)}]}
            for i in range(10)
        ]

        ast = make_ast([
            make_wrapper_div(
                "additional-1",
                visibility="internal",
                policies=["additional"],
                content=long_content,
            ),
        ])

        context = BuildContext(build_target="internal", render_target="pdf")
        result_ast, report = filter_presentation(ast, FilterConfig(), context)

        # Should have stub + appendix header + content
        blocks = result_ast["blocks"]

        # Find appendix header
        has_appendix = any(
            b.get("t") == "Header" and "Appendix" in str(b)
            for b in blocks
        )
        assert has_appendix

        assert any(
            e.reason_code == "PRES_PDF_MOVED_TO_APPENDIX"
            for e in report.entries
        )


# ============================================================================
# Test: Presentation Filter (HTML)
# ============================================================================

class TestPresentationFilterHTML:
    """Tests for HTML presentation filter."""

    def test_html_folds_additional_sections(self):
        """HTML mode folds long additional sections in place."""
        long_content = [
            {"t": "Para", "c": [{"t": "Str", "c": "Paragraph " + str(i)}]}
            for i in range(10)
        ]

        ast = make_ast([
            make_wrapper_div(
                "additional-1",
                visibility="internal",
                policies=["additional"],
                content=long_content,
            ),
        ])

        context = BuildContext(build_target="internal", render_target="html")
        result_ast, report = filter_presentation(ast, FilterConfig(), context)

        # Content should remain in place (not moved)
        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert "additional-1" in wrapper_ids

        # Should have fold marker
        assert any(
            e.reason_code == "PRES_HTML_FOLDED"
            for e in report.entries
        )

    def test_html_folds_long_code_blocks(self):
        """HTML mode folds long code blocks."""
        long_code = "x = 1\n" * 100

        ast = make_ast([
            {"t": "CodeBlock", "c": [["", ["python"], []], long_code]},
        ])

        context = BuildContext(build_target="internal", render_target="html")
        result_ast, report = filter_presentation(ast, FilterConfig(), context)

        # Code block should remain (not externalized like PDF)
        assert result_ast["blocks"][0]["t"] == "CodeBlock"

        assert any(
            e.reason_code == "PRES_HTML_CODEBLOCK_FOLDED"
            for e in report.entries
        )


# ============================================================================
# Test: Pipeline Order
# ============================================================================

class TestPipelineOrder:
    """Tests for filter pipeline ordering."""

    def test_visibility_removes_before_policy(self):
        """Visibility filter removes before policy filter runs."""
        # Create a wrapper that's internal-only AND policy-tagged
        ast = make_ast([
            make_wrapper_div(
                "internal-draft",
                visibility="internal",
                policies=["draft"],
            ),
        ])

        context = BuildContext(build_target="external")
        result_ast, report = apply_filters(ast, FilterConfig(), context)

        # Should be removed by visibility, not policy
        wrapper_ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(result_ast)}
        assert len(wrapper_ids) == 0

        # Report should show visibility removal, not policy
        assert len(report) == 1
        assert report.entries[0].reason_code == "VIS_REMOVED_INTERNAL_ONLY"

    def test_pipeline_order_fixed(self):
        """Pipeline runs filters in fixed order."""
        ast = make_ast([
            make_wrapper_div(
                "test-1",
                visibility="external",
                extra_attrs={"producer": "test"},
            ),
        ])

        context = BuildContext(build_target="external", render_target="pdf")
        result_ast, report = apply_filters(ast, FilterConfig(), context)

        # Should have metadata stripped (after visibility/policy passed)
        for div, _, _ in iter_wrappers(result_ast):
            assert get_wrapper_attr(div, "producer") is None


# ============================================================================
# Test: Determinism
# ============================================================================

class TestDeterminism:
    """Tests for deterministic output."""

    def test_output_is_deterministic(self):
        """Running filter twice produces identical output."""
        ast = make_ast([
            make_wrapper_div("internal-1", visibility="internal"),
            make_wrapper_div("external-1", visibility="external"),
            make_wrapper_div(
                "provenance-1",
                visibility="external",
                extra_attrs={"producer": "test", "run_id": "123"},
            ),
        ])

        context = BuildContext(build_target="external", render_target="pdf")
        config = FilterConfig()

        result1, report1 = apply_filters(copy.deepcopy(ast), config, context)
        result2, report2 = apply_filters(copy.deepcopy(ast), config, context)

        # AST should be identical
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)

        # Report should be identical
        assert report1.to_json() == report2.to_json()

    def test_report_order_matches_application_order(self):
        """Report entries match filter application order."""
        ast = make_ast([
            make_wrapper_div("internal-1", visibility="internal"),
            make_wrapper_div("internal-2", visibility="internal"),
        ])

        context = BuildContext(build_target="external")
        _, report = apply_filters(ast, FilterConfig(), context)

        # Entries should be in document order
        assert report.entries[0].semantic_id == "internal-1"
        assert report.entries[1].semantic_id == "internal-2"


# ============================================================================
# Test: BuildContext
# ============================================================================

class TestBuildContext:
    """Tests for BuildContext."""

    def test_context_is_immutable(self):
        """BuildContext is frozen dataclass."""
        context = BuildContext(build_target="internal")
        with pytest.raises(Exception):  # FrozenInstanceError
            context.build_target = "external"

    def test_external_forces_strict(self):
        """External/dossier targets force strict=True."""
        context = BuildContext(build_target="external", strict=False)
        assert context.strict is True

        context = BuildContext(build_target="dossier", strict=False)
        assert context.strict is True

    def test_internal_allows_non_strict(self):
        """Internal target allows strict=False."""
        context = BuildContext(build_target="internal", strict=False)
        assert context.strict is False

    def test_context_serialization(self):
        """BuildContext can be serialized."""
        context = BuildContext(
            build_target="external",
            render_target="pdf",
            project_root="/path/to/project",
        )
        json_str = context.to_json()
        data = json.loads(json_str)
        assert data["build_target"] == "external"
        assert data["render_target"] == "pdf"


# ============================================================================
# Test: FilterReport
# ============================================================================

class TestFilterReport:
    """Tests for FilterReport."""

    def test_report_merge(self):
        """Reports can be merged maintaining order."""
        report1 = FilterReport()
        report1.add("id-1", "removed", "VIS_REMOVED")

        report2 = FilterReport()
        report2.add("id-2", "stripped", "META_STRIP")

        merged = report1.merge(report2)
        assert len(merged) == 2
        assert merged.entries[0].semantic_id == "id-1"
        assert merged.entries[1].semantic_id == "id-2"

    def test_report_filter_by_action(self):
        """Report can filter by action."""
        report = FilterReport()
        report.add("id-1", "removed", "VIS_REMOVED")
        report.add("id-2", "stripped", "META_STRIP")
        report.add("id-3", "removed", "POL_REMOVED")

        removed = report.filter_by_action("removed")
        assert len(removed) == 2

    def test_report_to_json(self):
        """Report can be serialized to JSON."""
        report = FilterReport()
        report.add("id-1", "removed", "VIS_REMOVED", message="test")

        json_str = report.to_json()
        data = json.loads(json_str)
        assert data["total_actions"] == 1
        assert len(data["entries"]) == 1


# ============================================================================
# Test: Wrapper Utilities
# ============================================================================

class TestWrapperUtilities:
    """Tests for wrapper utility functions."""

    def test_is_semantic_wrapper(self):
        """is_semantic_wrapper detects valid wrappers."""
        wrapper = make_wrapper_div("test-id")
        assert is_semantic_wrapper(wrapper) is True

        non_wrapper = {"t": "Para", "c": [{"t": "Str", "c": "text"}]}
        assert is_semantic_wrapper(non_wrapper) is False

        empty_div = {"t": "Div", "c": [["", [], []], []]}
        assert is_semantic_wrapper(empty_div) is False

    def test_iter_wrappers_finds_all(self):
        """iter_wrappers finds all semantic wrappers."""
        ast = make_ast([
            make_wrapper_div("id-1"),
            {"t": "Para", "c": []},
            make_wrapper_div("id-2"),
        ])

        ids = {get_wrapper_id(d) for d, _, _ in iter_wrappers(ast)}
        assert ids == {"id-1", "id-2"}

    def test_iter_wrappers_includes_paths(self):
        """iter_wrappers provides correct paths."""
        ast = make_ast([
            make_wrapper_div("id-1"),
            make_wrapper_div("id-2"),
        ])

        paths = {path for _, path, _ in iter_wrappers(ast)}
        assert "blocks[0]" in paths
        assert "blocks[1]" in paths
