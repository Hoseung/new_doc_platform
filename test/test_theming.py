"""Tests for HTML theming system."""

import pytest
from pathlib import Path

from litepub_norm.theming import (
    # Contract
    REQUIRED_IDS,
    REQUIRED_CLASSES,
    validate_template_hooks,
    # Manifest
    ThemeManifest,
    load_manifest,
    # Resolver
    ThemeBundle,
    resolve_theme,
    list_available_themes,
    # Selection
    with_theme,
)
from litepub_norm.theming.resolver import ThemeNotFoundError, ThemeValidationError
from litepub_norm.theming.manifest import ThemeEntry, create_default_manifest
from litepub_norm.render import (
    RenderConfig,
    default_html_config,
    default_html_site_config,
    themed_html_config,
)


# =============================================================================
# Contract Tests
# =============================================================================

class TestContract:
    """Tests for DOM contract (hook points)."""

    def test_required_ids_defined(self):
        """Required IDs are defined."""
        assert "lp-content" in REQUIRED_IDS
        assert "lp-header" in REQUIRED_IDS
        assert "lp-footer" in REQUIRED_IDS
        assert "lp-nav" in REQUIRED_IDS
        assert "lp-sidebar" in REQUIRED_IDS
        assert "lp-toc" in REQUIRED_IDS

    def test_required_classes_defined(self):
        """Required classes are defined."""
        assert "computed-figure" in REQUIRED_CLASSES
        assert "computed-table" in REQUIRED_CLASSES
        assert "computed-metric" in REQUIRED_CLASSES
        assert "foldable" in REQUIRED_CLASSES

    def test_validate_template_hooks_valid(self):
        """Valid template passes validation."""
        template = """
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <main id="lp-content">$body$</main>
        </body>
        </html>
        """
        result = validate_template_hooks(template)
        assert result.valid is True
        assert len(result.missing_mandatory) == 0

    def test_validate_template_hooks_missing_body(self):
        """Template missing $body$ fails validation."""
        template = """
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <main id="lp-content"></main>
        </body>
        </html>
        """
        result = validate_template_hooks(template)
        assert result.valid is False
        assert "$body$ (Pandoc variable)" in result.missing_mandatory

    def test_validate_template_hooks_missing_content_id(self):
        """Template missing lp-content fails validation."""
        template = """
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <main>$body$</main>
        </body>
        </html>
        """
        result = validate_template_hooks(template)
        assert result.valid is False
        assert "lp-content" in result.missing_mandatory


# =============================================================================
# Manifest Tests
# =============================================================================

class TestManifest:
    """Tests for theme manifest parsing."""

    def test_theme_manifest_from_dict(self):
        """ThemeManifest.from_dict creates manifest correctly."""
        data = {
            "id": "my_theme",
            "name": "My Theme",
            "version": "1.0.0",
            "entry": {
                "template": "template.html",
                "css": ["assets/theme.css"],
                "js": ["assets/theme.js"],
            },
        }
        manifest = ThemeManifest.from_dict(data)
        assert manifest.id == "my_theme"
        assert manifest.name == "My Theme"
        assert manifest.version == "1.0.0"
        assert manifest.entry.template == "template.html"
        assert manifest.entry.css == ("assets/theme.css",)
        assert manifest.entry.js == ("assets/theme.js",)

    def test_theme_manifest_defaults(self):
        """ThemeManifest uses defaults for missing fields."""
        data = {"id": "minimal"}
        manifest = ThemeManifest.from_dict(data)
        assert manifest.id == "minimal"
        assert manifest.version == "1.0.0"
        assert manifest.entry.template == "template.html"
        assert manifest.supports_single is True
        assert manifest.supports_site is True

    def test_create_default_manifest(self):
        """create_default_manifest creates valid manifest."""
        manifest = create_default_manifest("my_theme")
        assert manifest.id == "my_theme"
        assert manifest.name == "My Theme"  # Auto-formatted from ID


# =============================================================================
# Resolver Tests
# =============================================================================

class TestResolver:
    """Tests for theme resolution."""

    def test_list_available_themes(self):
        """list_available_themes returns built-in themes."""
        themes = list_available_themes()
        assert "base" in themes
        assert "sidebar_docs" in themes
        assert "topbar_classic" in themes
        assert "book_tutorial" in themes

    def test_resolve_theme_base(self):
        """resolve_theme resolves base theme."""
        bundle = resolve_theme("base")
        assert bundle.theme_id == "base"
        assert bundle.template_path.exists()
        assert bundle.assets_dir.exists()
        assert bundle.template_hash.startswith("sha256:")
        assert bundle.assets_hash.startswith("sha256:")

    def test_resolve_theme_sidebar_docs(self):
        """resolve_theme resolves sidebar_docs theme."""
        bundle = resolve_theme("sidebar_docs")
        assert bundle.theme_id == "sidebar_docs"
        assert bundle.template_path.exists()
        assert (bundle.assets_dir / "theme.css").exists()
        assert (bundle.assets_dir / "theme.js").exists()

    def test_resolve_theme_not_found(self):
        """resolve_theme raises error for unknown theme."""
        with pytest.raises(ThemeNotFoundError) as exc_info:
            resolve_theme("nonexistent_theme")
        assert "nonexistent_theme" in str(exc_info.value)
        assert "Available themes" in str(exc_info.value)

    def test_theme_bundle_relative_paths(self):
        """ThemeBundle.get_relative_css returns relative paths."""
        bundle = resolve_theme("base")
        css_paths = bundle.get_relative_css()
        assert len(css_paths) >= 1
        assert css_paths[0].startswith("assets/")

    def test_theme_manifest_loaded(self):
        """Theme manifest is loaded when present."""
        bundle = resolve_theme("base")
        assert bundle.manifest.id == "base"
        assert bundle.manifest.name == "Base Theme"


# =============================================================================
# Selection Tests
# =============================================================================

class TestSelection:
    """Tests for theme selection helpers."""

    def test_with_theme_function(self):
        """with_theme applies theme to config."""
        from litepub_norm.theming.selection import with_theme

        base_config = RenderConfig()
        themed_config = with_theme(base_config, "sidebar_docs")

        assert themed_config.html_template_path is not None
        assert themed_config.html_assets_dir is not None
        assert "sidebar_docs" in str(themed_config.html_template_path)


# =============================================================================
# RenderConfig Integration Tests
# =============================================================================

class TestRenderConfigIntegration:
    """Tests for RenderConfig theme integration."""

    def test_default_html_config_with_theme(self):
        """default_html_config accepts theme_id parameter."""
        config = default_html_config("sidebar_docs")
        assert config.html_theme == "sidebar_docs"
        assert "sidebar_docs" in str(config.html_template_path)
        assert "sidebar_docs" in str(config.html_assets_dir)

    def test_default_html_site_config_with_theme(self):
        """default_html_site_config accepts theme_id parameter."""
        config = default_html_site_config(split_level=2, theme_id="book_tutorial")
        assert config.html_theme == "book_tutorial"
        assert config.html_mode == "site"
        assert config.html_site_split_level == 2

    def test_themed_html_config_single_mode(self):
        """themed_html_config creates config with theme."""
        config = themed_html_config("topbar_classic")
        assert config.html_theme == "topbar_classic"
        assert config.html_mode == "single"
        assert config.html_template_path.exists()

    def test_themed_html_config_site_mode(self):
        """themed_html_config supports site mode."""
        config = themed_html_config("sidebar_docs", mode="site", split_level=2)
        assert config.html_theme == "sidebar_docs"
        assert config.html_mode == "site"
        assert config.html_site_split_level == 2

    def test_render_config_with_theme_method(self):
        """RenderConfig.with_theme method works."""
        base_config = RenderConfig(output_dir=Path("/tmp/test"))
        themed = base_config.with_theme("base")

        # Output dir should be preserved
        assert themed.output_dir == Path("/tmp/test")
        # Theme should be applied
        assert themed.html_theme == "base"
        assert themed.html_template_path.exists()

    def test_render_config_chaining(self):
        """RenderConfig methods can be chained."""
        config = (
            RenderConfig()
            .with_theme("sidebar_docs")
            .with_html_mode("site", split_level=2)
            .with_output_dir("/tmp/output")
        )
        assert config.html_theme == "sidebar_docs"
        assert config.html_mode == "site"
        assert config.html_site_split_level == 2
        assert config.output_dir == Path("/tmp/output")


# =============================================================================
# Template Validation Tests
# =============================================================================

class TestBuiltInThemeValidation:
    """Tests that all built-in themes pass validation."""

    @pytest.mark.parametrize("theme_id", ["base", "sidebar_docs", "topbar_classic", "book_tutorial"])
    def test_theme_template_has_required_hooks(self, theme_id):
        """Each theme template has required hook points."""
        bundle = resolve_theme(theme_id)
        template_content = bundle.template_path.read_text(encoding="utf-8")

        result = validate_template_hooks(template_content)

        assert result.valid, f"Theme '{theme_id}' failed validation: {result.missing_mandatory}"

    @pytest.mark.parametrize("theme_id", ["base", "sidebar_docs", "topbar_classic", "book_tutorial"])
    def test_theme_has_css(self, theme_id):
        """Each theme has CSS file."""
        bundle = resolve_theme(theme_id)
        css_path = bundle.assets_dir / "theme.css"
        assert css_path.exists(), f"Theme '{theme_id}' missing theme.css"

    @pytest.mark.parametrize("theme_id", ["base", "sidebar_docs", "topbar_classic", "book_tutorial"])
    def test_theme_has_js(self, theme_id):
        """Each theme has JS file."""
        bundle = resolve_theme(theme_id)
        js_path = bundle.assets_dir / "theme.js"
        assert js_path.exists(), f"Theme '{theme_id}' missing theme.js"

    @pytest.mark.parametrize("theme_id", ["base", "sidebar_docs", "topbar_classic", "book_tutorial"])
    def test_theme_has_manifest(self, theme_id):
        """Each theme has theme.json manifest."""
        bundle = resolve_theme(theme_id)
        manifest_path = bundle.theme_dir / "theme.json"
        assert manifest_path.exists(), f"Theme '{theme_id}' missing theme.json"
