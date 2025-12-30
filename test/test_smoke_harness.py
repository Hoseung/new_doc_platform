"""
Smoke tests for the normalization harness.

Basic tests to verify the pipeline doesn't crash.
"""

import pytest

from litepub_norm import normalize_text, Registry
from litepub_norm.errors import (
    FenceMismatchError,
    FenceOverlapError,
    UnknownSemanticIdError,
)


@pytest.fixture
def simple_registry() -> Registry:
    """A simple registry for testing."""
    return Registry.from_dict({
        "test.block.v1": {
            "role": "computed",
            "kind": "table",
            "source": "test.json",
            "schema": "test_v1",
            "visibility": "internal",
        },
        "test.annotation.v1": {
            "role": "hybrid",
            "kind": "annotation",
            "bind-to": "test.block.v1",
        },
    })


class TestSmokeHarness:
    """Smoke tests for parse->adapt->normalize pipeline."""

    def test_simple_md_parses(self, simple_registry: Registry):
        """Test that simple markdown parses without crashing."""
        text = """# Test

Some prose.

<!-- BEGIN test.block.v1 -->
Test content.
<!-- END test.block.v1 -->
"""
        result = normalize_text(text, "markdown", simple_registry)
        assert "blocks" in result
        assert len(result["blocks"]) > 0

    def test_simple_md_produces_div(self, simple_registry: Registry):
        """Test that markdown fences become Divs."""
        text = """<!-- BEGIN test.block.v1 -->
Content here.
<!-- END test.block.v1 -->
"""
        result = normalize_text(text, "markdown", simple_registry)
        blocks = result["blocks"]

        # Find the Div
        divs = [b for b in blocks if b.get("t") == "Div"]
        assert len(divs) == 1

        # Check identifier
        attr = divs[0]["c"][0]
        assert attr[0] == "test.block.v1"

    def test_metadata_injected(self, simple_registry: Registry):
        """Test that registry metadata is injected into Div attributes."""
        text = """<!-- BEGIN test.block.v1 -->
Content.
<!-- END test.block.v1 -->
"""
        result = normalize_text(text, "markdown", simple_registry)
        blocks = result["blocks"]

        div = next(b for b in blocks if b.get("t") == "Div")
        attr = div["c"][0]
        attrs_dict = {k: v for k, v in attr[2]}

        assert attrs_dict["role"] == "computed"
        assert attrs_dict["kind"] == "table"
        assert attrs_dict["lock"] == "true"

    def test_mismatched_fences_error(self, simple_registry: Registry):
        """Test that mismatched fences raise an error."""
        text = """<!-- BEGIN test.block.v1 -->
Content.
<!-- END wrong.id -->
"""
        with pytest.raises(FenceMismatchError):
            normalize_text(text, "markdown", simple_registry)

    def test_unclosed_fence_error(self, simple_registry: Registry):
        """Test that unclosed fences raise an error."""
        text = """<!-- BEGIN test.block.v1 -->
Content without end.
"""
        with pytest.raises(FenceMismatchError):
            normalize_text(text, "markdown", simple_registry)

    def test_nested_fences_error(self, simple_registry: Registry):
        """Test that nested fences raise an error (v1 disallows nesting)."""
        registry = Registry.from_dict({
            "outer.v1": {"role": "authored", "kind": "prose"},
            "inner.v1": {"role": "authored", "kind": "prose"},
        })
        text = """<!-- BEGIN outer.v1 -->
<!-- BEGIN inner.v1 -->
Nested content.
<!-- END inner.v1 -->
<!-- END outer.v1 -->
"""
        with pytest.raises(FenceOverlapError):
            normalize_text(text, "markdown", registry)

    def test_unknown_id_error_strict(self):
        """Test that unknown IDs raise an error in strict mode."""
        registry = Registry.from_dict({}, strict=True)
        text = """<!-- BEGIN unknown.id -->
Content.
<!-- END unknown.id -->
"""
        with pytest.raises(UnknownSemanticIdError):
            normalize_text(text, "markdown", registry, mode="strict")

    def test_unknown_id_warning_draft(self):
        """Test that unknown IDs don't crash in draft mode."""
        registry = Registry.from_dict({}, strict=False)
        text = """<!-- BEGIN unknown.id -->
Content.
<!-- END unknown.id -->
"""
        # Should not raise
        result = normalize_text(text, "markdown", registry, mode="draft")
        assert "blocks" in result

    def test_placeholder_injected(self, simple_registry: Registry):
        """Test that computed blocks get placeholder markers."""
        text = """<!-- BEGIN test.block.v1 -->
Caption text.
<!-- END test.block.v1 -->
"""
        result = normalize_text(text, "markdown", simple_registry)
        blocks = result["blocks"]

        div = next(b for b in blocks if b.get("t") == "Div")
        content = div["c"][1]

        # Check for placeholder
        import json
        content_str = json.dumps(content)
        assert "[[COMPUTED:TABLE]]" in content_str
