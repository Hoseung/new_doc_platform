"""Filter stage - produces target-specific documents.

Filters implement monotonic condensation:
Internal → External → Dossier

Downstream targets may only remove or redact content,
never introduce new analytic results.

Filter pipeline order:
1. Visibility filter - remove wrappers by visibility level
2. Policy filter - remove wrappers by forbidden policy tags
3. Metadata strip filter - strip provenance attributes
4. Presentation filter - transform for PDF/HTML output
"""

from .api import apply_filters, apply_filter
from .context import BuildContext, BuildTarget, RenderTarget
from .config import FilterConfig, PresentationThresholds, AppendixOptions
from .report import FilterReport, FilterReportEntry

# Individual filters
from .visibility import filter_visibility
from .policy import filter_policy
from .metadata_strip import filter_metadata_strip
from .presentation import filter_presentation

__all__ = [
    # Main API
    "apply_filters",
    "apply_filter",
    # Context and config
    "BuildContext",
    "BuildTarget",
    "RenderTarget",
    "FilterConfig",
    "PresentationThresholds",
    "AppendixOptions",
    # Report
    "FilterReport",
    "FilterReportEntry",
    # Individual filters
    "filter_visibility",
    "filter_policy",
    "filter_metadata_strip",
    "filter_presentation",
]
