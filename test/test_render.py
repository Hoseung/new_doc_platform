"""Tests for the rendering stage."""

import json
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from litepub_norm.render.config import RenderConfig, default_html_config, default_pdf_config
from litepub_norm.render.result import RenderResult, RenderWarning, RenderError
from litepub_norm.render.report import RenderReport, file_hash, get_pandoc_version
from litepub_norm.render.pandoc_runner import run as pandoc_run, PandocError, check_pandoc_version
from litepub_norm.render.latex_runner import is_engine_available
from litepub_norm.render.api import render
from litepub_norm.filters.context import BuildContext


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def minimal_ast():
    """Minimal Pandoc AST for testing."""
    return {
        "pandoc-api-version": [1, 23],
        "meta": {},
        "blocks": [
            {
                "t": "Header",
                "c": [1, ["test-heading", [], []], [{"t": "Str", "c": "Test Heading"}]]
            },
            {
                "t": "Para",
                "c": [{"t": "Str", "c": "This is a test paragraph."}]
            }
        ]
    }


@pytest.fixture
def ast_with_wrapper():
    """AST with a semantic wrapper Div."""
    return {
        "pandoc-api-version": [1, 23],
        "meta": {},
        "blocks": [
            {
                "t": "Header",
                "c": [1, ["introduction", [], []], [{"t": "Str", "c": "Introduction"}]]
            },
            {
                "t": "Div",
                "c": [
                    ["tbl.test.v1", [], [["kind", "table"], ["visibility", "external"]]],
                    [{"t": "Para", "c": [{"t": "Str", "c": "Table placeholder"}]}]
                ]
            }
        ]
    }


@pytest.fixture
def ast_with_foldable():
    """AST with a foldable Div."""
    return {
        "pandoc-api-version": [1, 23],
        "meta": {},
        "blocks": [
            {
                "t": "Header",
                "c": [1, ["test", [], []], [{"t": "Str", "c": "Test"}]]
            },
            {
                "t": "Div",
                "c": [
                    ["foldable-1", ["foldable"], [["data-title", "Click to expand"], ["data-collapsed", "true"]]],
                    [{"t": "Para", "c": [{"t": "Str", "c": "Hidden content here."}]}]
                ]
            }
        ]
    }


@pytest.fixture
def ast_with_korean():
    """AST with Korean text."""
    return {
        "pandoc-api-version": [1, 23],
        "meta": {},
        "blocks": [
            {
                "t": "Header",
                "c": [1, ["korean-test", [], []], [{"t": "Str", "c": "한글 테스트"}]]
            },
            {
                "t": "Para",
                "c": [{"t": "Str", "c": "이것은 한글 텍스트입니다. This is mixed Korean and English."}]
            }
        ]
    }


@pytest.fixture
def internal_context():
    """BuildContext for internal HTML build."""
    return BuildContext(build_target="internal", render_target="html", strict=False)


@pytest.fixture
def external_context():
    """BuildContext for external PDF build."""
    return BuildContext(build_target="external", render_target="pdf", strict=True)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory."""
    return tmp_path / "render_output"


# ============================================================================
# RenderConfig Tests
# ============================================================================

class TestRenderConfig:
    """Tests for RenderConfig."""

    def test_default_config(self):
        """Default config has sensible defaults."""
        config = RenderConfig()
        assert config.latex_engine == "xelatex"
        assert config.latex_runs == 2
        assert config.standalone is True
        assert config.copy_assets is True

    def test_with_output_dir(self, tmp_path):
        """with_output_dir creates new config with different output."""
        config = RenderConfig()
        new_config = config.with_output_dir(tmp_path / "new_output")
        assert new_config.output_dir == tmp_path / "new_output"
        # Original unchanged
        assert config.output_dir != new_config.output_dir

    def test_get_writer_options(self):
        """get_writer_options returns correct options."""
        config = RenderConfig(
            html_writer_options=("--toc",),
            latex_writer_options=("--pdf-engine=xelatex",),
        )
        assert config.get_writer_options("html") == ("--toc",)
        assert config.get_writer_options("pdf") == ("--pdf-engine=xelatex",)
        assert config.get_writer_options("md") == ()

    def test_default_html_config(self):
        """default_html_config has template and assets."""
        config = default_html_config()
        assert config.html_template_path is not None
        assert config.html_assets_dir is not None
        # html_lua_filters is empty by default (HTML handles div classes natively)
        assert isinstance(config.html_lua_filters, tuple)

    def test_default_pdf_config(self):
        """default_pdf_config has latex template."""
        config = default_pdf_config()
        assert config.latex_template_path is not None


# ============================================================================
# RenderResult Tests
# ============================================================================

class TestRenderResult:
    """Tests for RenderResult."""

    def test_initial_success(self):
        """New result starts as success."""
        result = RenderResult(success=True)
        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error_sets_failure(self):
        """Adding an error sets success to False."""
        result = RenderResult(success=True)
        result.add_error("ERR", "message", "stage")
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "ERR"

    def test_add_warning_preserves_success(self):
        """Adding a warning doesn't affect success."""
        result = RenderResult(success=True)
        result.add_warning("WARN", "message")
        assert result.success is True
        assert len(result.warnings) == 1

    def test_primary_output(self, tmp_path):
        """primary_output returns first file."""
        result = RenderResult(success=True)
        result.add_output_file(tmp_path / "first.html")
        result.add_output_file(tmp_path / "second.css")
        assert result.primary_output == tmp_path / "first.html"

    def test_to_dict(self, tmp_path):
        """to_dict produces serializable dict."""
        result = RenderResult(success=True)
        result.add_output_file(tmp_path / "output.html")
        result.add_warning("W001", "test warning")
        d = result.to_dict()
        assert d["success"] is True
        assert len(d["output_files"]) == 1
        assert len(d["warnings"]) == 1


# ============================================================================
# RenderReport Tests
# ============================================================================

class TestRenderReport:
    """Tests for RenderReport."""

    def test_start_and_complete(self):
        """start and complete set timestamps."""
        report = RenderReport()
        report.start()
        assert report.started_at != ""
        report.complete()
        assert report.completed_at != ""

    def test_set_template(self, tmp_path):
        """set_template computes hash."""
        template = tmp_path / "template.html"
        template.write_text("<html></html>")

        report = RenderReport()
        report.set_template(template)

        assert report.template_path == str(template)
        assert report.template_hash.startswith("sha256:")

    def test_to_json(self):
        """to_json produces valid JSON."""
        report = RenderReport()
        report.build_target = "internal"
        report.render_target = "html"
        report.start()
        report.complete()

        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["context"]["build_target"] == "internal"

    def test_save(self, tmp_path):
        """save writes to file."""
        report = RenderReport()
        report.build_target = "test"
        path = tmp_path / "report.json"
        report.save(path)

        assert path.exists()
        content = json.loads(path.read_text())
        assert content["context"]["build_target"] == "test"


class TestFileHash:
    """Tests for file_hash utility."""

    def test_existing_file(self, tmp_path):
        """Hash is computed for existing file."""
        f = tmp_path / "test.txt"
        f.write_text("test content")
        h = file_hash(f)
        assert h.startswith("sha256:")
        assert len(h) == 7 + 64  # "sha256:" + 64 hex chars

    def test_missing_file(self, tmp_path):
        """Returns empty for missing file."""
        f = tmp_path / "missing.txt"
        assert file_hash(f) == ""


# ============================================================================
# Pandoc Runner Tests
# ============================================================================

class TestPandocRunner:
    """Tests for pandoc_runner."""

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_check_pandoc_version(self):
        """check_pandoc_version returns version string."""
        version = check_pandoc_version()
        assert version is not None
        # Version format like "3.1.9"
        assert "." in version

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_run_basic(self, minimal_ast, tmp_path):
        """Basic pandoc run produces output."""
        output = tmp_path / "output.html"
        result = pandoc_run(
            input_ast=minimal_ast,
            to_format="html5",
            output_path=output,
        )
        assert result.success
        assert output.exists()
        content = output.read_text()
        assert "Test Heading" in content

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_run_with_wrapper(self, ast_with_wrapper, tmp_path):
        """Run preserves wrapper IDs."""
        output = tmp_path / "output.html"
        pandoc_run(
            input_ast=ast_with_wrapper,
            to_format="html5",
            output_path=output,
        )
        content = output.read_text()
        assert 'id="tbl.test.v1"' in content

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_run_korean(self, ast_with_korean, tmp_path):
        """Korean text is preserved."""
        output = tmp_path / "output.html"
        pandoc_run(
            input_ast=ast_with_korean,
            to_format="html5",
            output_path=output,
        )
        content = output.read_text()
        assert "한글" in content
        assert "테스트" in content


# ============================================================================
# HTML Renderer Tests
# ============================================================================

class TestHtmlRenderer:
    """Tests for HTML rendering."""

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_minimal(self, minimal_ast, internal_context, temp_output_dir):
        """Minimal HTML render produces output."""
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(minimal_ast, internal_context, config)

        assert result.success
        assert result.primary_output is not None
        assert result.primary_output.exists()

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_with_wrapper_preserves_id(self, ast_with_wrapper, internal_context, temp_output_dir):
        """Wrapper IDs appear in HTML output."""
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(ast_with_wrapper, internal_context, config)

        assert result.success
        content = result.primary_output.read_text()
        assert 'id="tbl.test.v1"' in content

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_report_generated(self, minimal_ast, internal_context, temp_output_dir):
        """Render report is generated."""
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(minimal_ast, internal_context, config)

        assert result.success
        report_path = temp_output_dir / "render_report.json"
        assert report_path.exists()

        report = json.loads(report_path.read_text())
        assert report["context"]["build_target"] == "internal"
        assert report["context"]["render_target"] == "html"


# ============================================================================
# Markdown Renderer Tests
# ============================================================================

class TestMdRenderer:
    """Tests for Markdown export."""

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_md_minimal(self, minimal_ast, temp_output_dir):
        """Minimal MD export produces output."""
        context = BuildContext(build_target="internal", render_target="md")
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(minimal_ast, context, config)

        assert result.success
        assert result.primary_output.exists()
        assert result.primary_output.suffix == ".md"

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_md_no_placeholders(self, ast_with_wrapper, temp_output_dir):
        """MD export contains no placeholders."""
        context = BuildContext(build_target="internal", render_target="md")
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(ast_with_wrapper, context, config)

        content = result.primary_output.read_text()
        assert "[[COMPUTED" not in content
        assert "[[PLACEHOLDER" not in content


# ============================================================================
# RST Renderer Tests
# ============================================================================

class TestRstRenderer:
    """Tests for RST export."""

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_rst_minimal(self, minimal_ast, temp_output_dir):
        """Minimal RST export produces output."""
        context = BuildContext(build_target="internal", render_target="rst")
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(minimal_ast, context, config)

        assert result.success
        assert result.primary_output.exists()
        assert result.primary_output.suffix == ".rst"

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_rst_best_effort_warning(self, minimal_ast, temp_output_dir):
        """RST export produces best-effort warning."""
        context = BuildContext(build_target="internal", render_target="rst")
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(minimal_ast, context, config)

        assert any(w.code == "RST_BEST_EFFORT" for w in result.warnings)


# ============================================================================
# PDF Renderer Tests (require XeLaTeX)
# ============================================================================

class TestPdfRenderer:
    """Tests for PDF rendering."""

    @pytest.mark.skipif(
        not is_engine_available("xelatex"),
        reason="XeLaTeX not installed"
    )
    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_pdf_minimal(self, minimal_ast, temp_output_dir):
        """Minimal PDF render produces output."""
        context = BuildContext(build_target="internal", render_target="pdf")
        config = RenderConfig(output_dir=temp_output_dir, latex_runs=1)
        result = render(minimal_ast, context, config)

        assert result.success
        assert result.primary_output is not None
        assert result.primary_output.suffix == ".pdf"
        # PDF should be non-trivial size
        assert result.primary_output.stat().st_size > 1000

    @pytest.mark.skipif(
        not is_engine_available("xelatex"),
        reason="XeLaTeX not installed"
    )
    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_pdf_creates_tex(self, minimal_ast, temp_output_dir):
        """PDF render also creates .tex intermediate."""
        context = BuildContext(build_target="internal", render_target="pdf")
        config = RenderConfig(output_dir=temp_output_dir, latex_runs=1)
        result = render(minimal_ast, context, config)

        assert result.success
        tex_files = list(temp_output_dir.glob("*.tex"))
        assert len(tex_files) >= 1


# ============================================================================
# API Tests
# ============================================================================

class TestRenderAPI:
    """Tests for the render API."""

    @pytest.mark.skipif(
        shutil.which("pandoc") is None,
        reason="Pandoc not installed"
    )
    def test_render_auto_output_name(self, minimal_ast, internal_context, temp_output_dir):
        """render auto-generates output name."""
        config = RenderConfig(output_dir=temp_output_dir)
        result = render(minimal_ast, internal_context, config)

        assert result.primary_output.name == "document.html"

    def test_render_unsupported_target(self, minimal_ast, temp_output_dir):
        """render raises for unsupported target."""
        context = BuildContext(build_target="internal", render_target="docx")  # type: ignore
        config = RenderConfig(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="Unsupported render target"):
            render(minimal_ast, context, config)
