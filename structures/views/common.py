"""Common logic used by all views."""

from typing import Optional

from structures.app_settings import (
    STRUCTURES_DEFAULT_PAGE_LENGTH,
    STRUCTURES_PAGING_ENABLED,
)
from structures.models import Owner


def add_common_context(context: Optional[dict] = None) -> dict:
    """Add common context and return it."""
    new_context = {
        "last_updated": Owner.objects.structures_last_updated(),
    }
    if context:
        new_context.update(context)
    return new_context


def add_common_data_export(data_export: dict) -> dict:
    """Add common data export entries to dictionary and return it."""
    add_on = {
        "data_tables_page_length": STRUCTURES_DEFAULT_PAGE_LENGTH,
        "data_tables_paging": int(STRUCTURES_PAGING_ENABLED),
    }
    data_export.update(add_on)
    return data_export
