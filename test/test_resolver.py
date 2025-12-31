"""
Tests for the resolution module.

Uses aarc_example_pack/ for test fixtures.
"""

import json
from pathlib import Path

import pytest

from litepub_norm.resolver import (
    resolve,
    build_resolution_plan,
    load_registry,
    ResolutionConfig,
    RegistrySnapshot,
    RegistryError,
    PayloadError,
    ValidationError,
    PlaceholderError,
)
from litepub_norm.resolver.registry import RegistryEntry
from litepub_norm.resolver.plan import build_plan
from litepub_norm.resolver.loaders.metric_v1 import load_metric_v1
from litepub_norm.resolver.loaders.table_simple_v1 import load_table_simple_v1
from litepub_norm.resolver.loaders.table_pandoc_v1 import load_table_pandoc_v1
from litepub_norm.resolver.loaders.figure_v1 import load_figure_v1, load_figure_meta_v1
from litepub_norm.validator import (
    validate_metric_v1,
    validate_table_simple_v1,
    validate_table_pandoc_v1,
    validate_figure_meta_v1,
)
from litepub_norm.resolver.emitters.metric_v1 import emit_metric_as_table
from litepub_norm.resolver.emitters.table_simple_v1 import emit_simple_table
from litepub_norm.resolver.emitters.table_pandoc_v1 import emit_pandoc_table
from litepub_norm.resolver.emitters.figure_v1 import emit_figure


# Path to test fixtures
AARC_PACK = Path(__file__).parent.parent / "aarc_example_pack"
REGISTRY_PATH = AARC_PACK / "registry_demo_aarc_1_1.json"


@pytest.fixture
def registry() -> RegistrySnapshot:
    """Load the demo registry."""
    return load_registry(REGISTRY_PATH)


class TestRegistryLoader:
    """Tests for AARC registry loading."""

    def test_load_registry(self):
        """Test loading registry from file."""
        reg = load_registry(REGISTRY_PATH)
        assert reg.registry_version == "aarc-1.1"
        assert len(reg.entries) == 6

    def test_registry_run_info(self, registry: RegistrySnapshot):
        """Test that run provenance is loaded."""
        assert registry.run.run_id == "run_demo_2025-12-31T00-00-00Z_demo"
        assert registry.run.pipeline_name == "demo-analysis-pipeline"
        assert registry.run.code_commit == "deadbeefdeadbeef"
        assert registry.run.code_dirty is False

    def test_registry_get_entry(self, registry: RegistrySnapshot):
        """Test entry lookup by ID."""
        entry = registry.get("metric.face.yaw_mae.v1")
        assert entry.artifact_type == "metric"
        assert entry.spec == "metric.json@v1"
        assert entry.origin_producer == "eval_yaw.py"

    def test_registry_missing_entry(self, registry: RegistrySnapshot):
        """Test that missing entry raises error."""
        with pytest.raises(RegistryError):
            registry.get("nonexistent.id")

    def test_registry_has(self, registry: RegistrySnapshot):
        """Test has() method."""
        assert registry.has("metric.face.yaw_mae.v1")
        assert not registry.has("nonexistent.id")

    def test_registry_resolve_path(self, registry: RegistrySnapshot):
        """Test URI resolution."""
        entry = registry.get("metric.face.yaw_mae.v1")
        path = registry.resolve_entry_path(entry)
        assert path.exists()
        assert path.name == "yaw_mae.json"


class TestMetricPipeline:
    """Tests for metric.json@v1 loader/validator/emitter."""

    def test_load_metric(self, registry: RegistrySnapshot):
        """Test loading a metric payload."""
        entry = registry.get("metric.face.yaw_mae.v1")
        payload = load_metric_v1(registry, entry, verify=False)
        assert payload["label"] == "Face yaw MAE (얼굴 yaw 평균절대오차)"
        assert payload["value"] == 3.72193
        assert payload["unit"] == "deg"

    def test_validate_metric(self, registry: RegistrySnapshot):
        """Test metric validation passes for valid payload."""
        entry = registry.get("metric.face.yaw_mae.v1")
        payload = load_metric_v1(registry, entry, verify=False)
        # Should not raise
        validate_metric_v1(payload, entry.id)

    def test_validate_metric_missing_label(self):
        """Test that missing label fails validation."""
        payload = {"value": 1.0}
        with pytest.raises(ValidationError):
            validate_metric_v1(payload, "test.metric")

    def test_emit_metric_produces_table(self, registry: RegistrySnapshot):
        """Test that emit produces a Pandoc Table."""
        entry = registry.get("metric.face.yaw_mae.v1")
        payload = load_metric_v1(registry, entry, verify=False)
        table = emit_metric_as_table(payload)
        assert table["t"] == "Table"
        # Check it has the right structure
        assert len(table["c"]) == 6  # Table has 6 parts


class TestSimpleTablePipeline:
    """Tests for table.simple.json@v1 loader/validator/emitter."""

    def test_load_simple_table(self, registry: RegistrySnapshot):
        """Test loading a simple table payload."""
        entry = registry.get("tbl.kpi.face.yaw_mae.v1")
        payload = load_table_simple_v1(registry, entry, verify=False)
        assert len(payload["columns"]) == 3
        assert len(payload["rows"]) == 5

    def test_validate_simple_table(self, registry: RegistrySnapshot):
        """Test simple table validation."""
        entry = registry.get("tbl.kpi.face.yaw_mae.v1")
        payload = load_table_simple_v1(registry, entry, verify=False)
        config = ResolutionConfig()
        # Should not raise
        validate_table_simple_v1(payload, entry.id, config.limits)

    def test_emit_simple_table(self, registry: RegistrySnapshot):
        """Test simple table emission."""
        entry = registry.get("tbl.kpi.face.yaw_mae.v1")
        payload = load_table_simple_v1(registry, entry, verify=False)
        table = emit_simple_table(payload)
        assert table["t"] == "Table"


class TestPandocTablePipeline:
    """Tests for table.pandoc.json@v1 loader/validator/emitter."""

    def test_load_pandoc_table(self, registry: RegistrySnapshot):
        """Test loading a Pandoc table payload."""
        entry = registry.get("tbl.summary.category_hierarchy.v1")
        payload = load_table_pandoc_v1(registry, entry, verify=False)
        assert payload["t"] == "Table"

    def test_validate_pandoc_table(self, registry: RegistrySnapshot):
        """Test Pandoc table validation."""
        entry = registry.get("tbl.summary.category_hierarchy.v1")
        payload = load_table_pandoc_v1(registry, entry, verify=False)
        config = ResolutionConfig()
        # Should not raise
        validate_table_pandoc_v1(payload, entry.id, config)

    def test_emit_pandoc_table_passthrough(self, registry: RegistrySnapshot):
        """Test Pandoc table emission is passthrough."""
        entry = registry.get("tbl.summary.category_hierarchy.v1")
        payload = load_table_pandoc_v1(registry, entry, verify=False)
        result = emit_pandoc_table(payload)
        # Should be same object/structure
        assert result["t"] == "Table"
        assert result == payload


class TestFigurePipeline:
    """Tests for figure.binary@v1 loader/validator/emitter."""

    def test_load_figure(self, registry: RegistrySnapshot):
        """Test loading a figure."""
        entry = registry.get("fig.demo.dummy_plot.v1")
        path = load_figure_v1(registry, entry, verify=False)
        assert path.exists()
        assert path.suffix == ".png"

    def test_load_figure_meta(self, registry: RegistrySnapshot):
        """Test loading figure metadata sidecar."""
        entry = registry.get("fig.demo.dummy_plot.v1")
        meta = load_figure_meta_v1(registry, entry, verify=False)
        assert meta is not None
        assert meta["caption"] == "Dummy plot for resolution tests (샘플 캡션)."
        assert meta["alt"] == "A placeholder image with a box and toy bars."

    def test_validate_figure_meta(self, registry: RegistrySnapshot):
        """Test figure metadata validation."""
        entry = registry.get("fig.demo.dummy_plot.v1")
        meta = load_figure_meta_v1(registry, entry, verify=False)
        # Should not raise
        validate_figure_meta_v1(meta, entry.id)

    def test_emit_figure(self, registry: RegistrySnapshot):
        """Test figure emission."""
        entry = registry.get("fig.demo.dummy_plot.v1")
        path = load_figure_v1(registry, entry, verify=False)
        meta = load_figure_meta_v1(registry, entry, verify=False)
        figure = emit_figure(path, meta, entry.id)
        assert figure["t"] == "Figure"


class TestResolutionPlan:
    """Tests for resolution plan building."""

    def _make_ast_with_placeholder(
        self, semantic_id: str, kind: str
    ) -> dict:
        """Create a minimal AST with one computed wrapper."""
        placeholder_text = f"[[COMPUTED:{kind}]]"
        return {
            "pandoc-api-version": [1, 23],
            "meta": {},
            "blocks": [
                {
                    "t": "Div",
                    "c": [
                        [
                            semantic_id,
                            [],
                            [
                                ["role", "computed"],
                                ["kind", kind.lower()],
                                ["lock", "true"],
                            ],
                        ],
                        [
                            {
                                "t": "Para",
                                "c": [{"t": "Str", "c": placeholder_text}],
                            }
                        ],
                    ],
                }
            ],
        }

    def test_build_plan_metric(self, registry: RegistrySnapshot):
        """Test building a plan for a metric placeholder."""
        ast = self._make_ast_with_placeholder("metric.face.yaw_mae.v1", "METRIC")
        config = ResolutionConfig()
        plan = build_plan(ast, registry, config)
        assert len(plan) == 1
        assert plan.items[0].semantic_id == "metric.face.yaw_mae.v1"
        assert plan.items[0].placeholder.kind == "METRIC"

    def test_build_plan_table(self, registry: RegistrySnapshot):
        """Test building a plan for a table placeholder."""
        ast = self._make_ast_with_placeholder("tbl.kpi.face.yaw_mae.v1", "TABLE")
        config = ResolutionConfig()
        plan = build_plan(ast, registry, config)
        assert len(plan) == 1
        assert plan.items[0].placeholder.kind == "TABLE"

    def test_build_plan_missing_entry_strict(self, registry: RegistrySnapshot):
        """Test that missing entry raises in strict mode."""
        ast = self._make_ast_with_placeholder("nonexistent.id", "TABLE")
        config = ResolutionConfig(strict=True)
        with pytest.raises(RegistryError):
            build_plan(ast, registry, config)


class TestResolveAPI:
    """Tests for the resolve() API."""

    def _make_ast_with_placeholder(
        self, semantic_id: str, kind: str
    ) -> dict:
        """Create a minimal AST with one computed wrapper."""
        placeholder_text = f"[[COMPUTED:{kind}]]"
        return {
            "pandoc-api-version": [1, 23],
            "meta": {},
            "blocks": [
                {
                    "t": "Div",
                    "c": [
                        [
                            semantic_id,
                            [],
                            [
                                ["role", "computed"],
                                ["kind", kind.lower()],
                                ["lock", "true"],
                            ],
                        ],
                        [
                            {
                                "t": "Para",
                                "c": [{"t": "Str", "c": placeholder_text}],
                            }
                        ],
                    ],
                }
            ],
        }

    def test_resolve_metric(self, registry: RegistrySnapshot):
        """Test resolving a metric placeholder."""
        ast = self._make_ast_with_placeholder("metric.face.yaw_mae.v1", "METRIC")
        config = ResolutionConfig(strict=False)  # Skip hash verification
        result = resolve(ast, registry, config)

        # Check the placeholder was replaced with a Table
        div = result["blocks"][0]
        content = div["c"][1]
        assert len(content) == 1
        assert content[0]["t"] == "Table"

    def test_resolve_simple_table(self, registry: RegistrySnapshot):
        """Test resolving a simple table placeholder."""
        ast = self._make_ast_with_placeholder("tbl.kpi.face.yaw_mae.v1", "TABLE")
        config = ResolutionConfig(strict=False)
        result = resolve(ast, registry, config)

        div = result["blocks"][0]
        content = div["c"][1]
        assert len(content) == 1
        assert content[0]["t"] == "Table"

    def test_resolve_pandoc_table(self, registry: RegistrySnapshot):
        """Test resolving a Pandoc table placeholder."""
        ast = self._make_ast_with_placeholder(
            "tbl.summary.category_hierarchy.v1", "TABLE"
        )
        config = ResolutionConfig(strict=False)
        result = resolve(ast, registry, config)

        div = result["blocks"][0]
        content = div["c"][1]
        assert len(content) == 1
        assert content[0]["t"] == "Table"

    def test_resolve_figure(self, registry: RegistrySnapshot):
        """Test resolving a figure placeholder."""
        ast = self._make_ast_with_placeholder("fig.demo.dummy_plot.v1", "FIGURE")
        config = ResolutionConfig(strict=False)
        result = resolve(ast, registry, config)

        div = result["blocks"][0]
        content = div["c"][1]
        assert len(content) == 1
        assert content[0]["t"] == "Figure"

    def test_resolve_does_not_mutate_original(self, registry: RegistrySnapshot):
        """Test that resolve() returns new AST, not mutating original."""
        ast = self._make_ast_with_placeholder("metric.face.yaw_mae.v1", "METRIC")
        original_str = json.dumps(ast)

        config = ResolutionConfig(strict=False)
        result = resolve(ast, registry, config)

        # Original should be unchanged
        assert json.dumps(ast) == original_str
        # Result should be different
        assert result != ast

    def test_resolve_with_registry_path(self):
        """Test resolve() with registry path string."""
        ast = {
            "pandoc-api-version": [1, 23],
            "meta": {},
            "blocks": [
                {
                    "t": "Div",
                    "c": [
                        [
                            "metric.face.yaw_mae.v1",
                            [],
                            [
                                ["role", "computed"],
                                ["kind", "metric"],
                                ["lock", "true"],
                            ],
                        ],
                        [
                            {
                                "t": "Para",
                                "c": [{"t": "Str", "c": "[[COMPUTED:METRIC]]"}],
                            }
                        ],
                    ],
                }
            ],
        }
        config = ResolutionConfig(strict=False)
        result = resolve(ast, REGISTRY_PATH, config)
        div = result["blocks"][0]
        content = div["c"][1]
        assert content[0]["t"] == "Table"
