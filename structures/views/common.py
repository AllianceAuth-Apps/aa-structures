"""Common logic used by all views."""

from typing import Optional

from structures.models import Owner


def add_common_context(context: Optional[dict] = None) -> dict:
    """Add common context and return it."""
    new_context = {
        "last_updated": Owner.objects.structures_last_updated(),
    }
    if context:
        new_context.update(context)
    return new_context
