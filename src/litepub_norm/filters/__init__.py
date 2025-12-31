"""Filter stage - produces target-specific documents.

Filters implement monotonic condensation:
Internal → External → Dossier

Downstream targets may only remove or redact content,
never introduce new analytic results.
"""

# TODO: Implement visibility filters
# - filter_for_internal()
# - filter_for_external()
# - filter_for_dossier()

__all__ = []
