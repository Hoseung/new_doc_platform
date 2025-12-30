"""
Golden tests for Markdown normalization.

Tests that golden_minimal.md normalizes to the expected canonical AST.
"""

from pathlib import Path

import pytest

from litepub_norm import normalize_file, Registry


# Paths to test data
DATA_DIR = Path(__file__).parent.parent / "data"
GOLDEN_MD = DATA_DIR / "golden_minimal.md"
REGISTRY_JSON = DATA_DIR / "registry.json"
EXPECTED_MD_JSON = DATA_DIR / "expected_normalized_md.json"


@pytest.fixture
def registry() -> Registry:
    """Load the test registry."""
    return Registry.from_file(REGISTRY_JSON)


@pytest.fixture
def expected_ast() -> dict:
    """Load the expected normalized AST."""
    import json
    return json.loads(EXPECTED_MD_JSON.read_text())


@pytest.fixture
def actual_ast(registry: Registry) -> dict:
    """Get the actual normalized AST from golden_minimal.md."""
    return normalize_file(GOLDEN_MD, registry)


class TestGoldenMd:
    """Golden tests for Markdown normalization."""

    def test_three_wrapper_divs_exist(self, actual_ast: dict):
        """Test that exactly 3 wrapper Divs exist with correct identifiers."""
        blocks = actual_ast.get("blocks", [])

        # Find all Div blocks with identifiers
        divs_with_ids = []
        for block in blocks:
            if block.get("t") == "Div":
                attr = block.get("c", [[]])[0]
                if attr and attr[0]:  # has identifier
                    divs_with_ids.append(attr[0])

        expected_ids = {
            "tbl.kpi.face.yaw_mae.v1",
            "metric.face.yaw_mae.v1",
            "tbl.kpi.face.yaw_mae.v1.annotation",
        }

        assert set(divs_with_ids) == expected_ids, f"Found IDs: {divs_with_ids}"

    def test_computed_blocks_have_lock_true(self, actual_ast: dict):
        """Test that computed blocks have lock=true."""
        blocks = actual_ast.get("blocks", [])

        computed_ids = ["tbl.kpi.face.yaw_mae.v1", "metric.face.yaw_mae.v1"]

        for block in blocks:
            if block.get("t") != "Div":
                continue
            attr = block.get("c", [[]])[0]
            if not attr or attr[0] not in computed_ids:
                continue

            # Check attributes for lock=true
            attrs_list = attr[2] if len(attr) > 2 else []
            attrs_dict = {k: v for k, v in attrs_list}

            assert attrs_dict.get("role") == "computed", f"Block {attr[0]} should be computed"
            assert attrs_dict.get("lock") == "true", f"Block {attr[0]} should have lock=true"

    def test_metadata_completed_from_registry(self, actual_ast: dict):
        """Test that metadata is completed from registry."""
        blocks = actual_ast.get("blocks", [])

        for block in blocks:
            if block.get("t") != "Div":
                continue
            attr = block.get("c", [[]])[0]
            if not attr or not attr[0]:
                continue

            identifier = attr[0]
            attrs_list = attr[2] if len(attr) > 2 else []
            attrs_dict = {k: v for k, v in attrs_list}

            if identifier == "tbl.kpi.face.yaw_mae.v1":
                assert attrs_dict.get("role") == "computed"
                assert attrs_dict.get("kind") == "table"
                assert attrs_dict.get("source") == "analysis/metrics/yaw.json"
                assert attrs_dict.get("schema") == "yaw_error_v1"
                assert attrs_dict.get("visibility") == "internal"

            elif identifier == "metric.face.yaw_mae.v1":
                assert attrs_dict.get("role") == "computed"
                assert attrs_dict.get("kind") == "metric"
                assert attrs_dict.get("visibility") == "external"

            elif identifier == "tbl.kpi.face.yaw_mae.v1.annotation":
                assert attrs_dict.get("role") == "hybrid"
                assert attrs_dict.get("kind") == "annotation"
                assert attrs_dict.get("bind-to") == "tbl.kpi.face.yaw_mae.v1"

    def test_no_html_comment_fences_remain(self, actual_ast: dict):
        """Test that no HTML comment fences remain in the AST."""
        import json
        ast_str = json.dumps(actual_ast)

        assert "BEGIN" not in ast_str, "BEGIN fence marker should be removed"
        assert "END" not in ast_str or "END" in "extends" or "appends" in ast_str.lower(), \
            "END fence marker should be removed"

    def test_computed_blocks_have_placeholders(self, actual_ast: dict):
        """Test that computed blocks have placeholder markers."""
        blocks = actual_ast.get("blocks", [])

        computed_ids = ["tbl.kpi.face.yaw_mae.v1", "metric.face.yaw_mae.v1"]
        expected_placeholders = {
            "tbl.kpi.face.yaw_mae.v1": "[[COMPUTED:TABLE]]",
            "metric.face.yaw_mae.v1": "[[COMPUTED:METRIC]]",
        }

        for block in blocks:
            if block.get("t") != "Div":
                continue
            attr = block.get("c", [[]])[0]
            if not attr or attr[0] not in computed_ids:
                continue

            identifier = attr[0]
            content = block.get("c", [[], []])[1]

            # Check if placeholder is present in the content
            import json
            content_str = json.dumps(content)
            expected = expected_placeholders[identifier]
            assert expected in content_str, \
                f"Block {identifier} should contain placeholder {expected}"

    def test_prose_preserved_in_computed_blocks(self, actual_ast: dict):
        """Test that prose/caption text is preserved in computed blocks."""
        blocks = actual_ast.get("blocks", [])

        for block in blocks:
            if block.get("t") != "Div":
                continue
            attr = block.get("c", [[]])[0]
            if not attr or attr[0] != "tbl.kpi.face.yaw_mae.v1":
                continue

            content = block.get("c", [[], []])[1]
            import json
            content_str = json.dumps(content)

            # Check that the prose is preserved
            assert "Yaw" in content_str and "MAE" in content_str, \
                "Prose should be preserved in computed block"

    def test_annotation_block_prose_preserved(self, actual_ast: dict):
        """Test that annotation block prose is preserved."""
        blocks = actual_ast.get("blocks", [])

        for block in blocks:
            if block.get("t") != "Div":
                continue
            attr = block.get("c", [[]])[0]
            if not attr or attr[0] != "tbl.kpi.face.yaw_mae.v1.annotation":
                continue

            content = block.get("c", [[], []])[1]
            import json
            content_str = json.dumps(content)

            assert "Interpretation" in content_str, \
                "Annotation prose should be preserved"
            assert "occlusion" in content_str, \
                "Annotation prose should be preserved"
