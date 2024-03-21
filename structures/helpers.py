"""Helpers for Structures."""

import datetime as dt
from typing import Any, List, Optional, Union
from urllib.parse import urlparse

from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeText, mark_safe
from django.utils.timezone import now
from eveuniverse.models import EveEntity, EveType


def hours_until_deadline(
    deadline: dt.datetime, start: Optional[dt.datetime] = None
) -> float:
    """Currently remaining hours until a given deadline."""
    if not isinstance(deadline, dt.datetime):
        raise TypeError("deadline must be of type datetime")
    if not start:
        start = now()
    return (deadline - start).total_seconds() / 3600


def datetime_almost_equal(
    first: Optional[dt.datetime], second: Optional[dt.datetime], threshold: int
) -> bool:
    """True when first and second datetime are within threshold in seconds.
    False when first or second is None.
    """
    if not first or not second:
        return False
    dif = abs((first - second).total_seconds())
    return dif <= abs(threshold)


def is_absolute_url(url: str) -> bool:
    """Return True if URL is absolute else False."""
    return bool(urlparse(url).netloc)


def get_or_create_esi_obj(model_class: type, *args, **kwargs) -> Any:
    """Get or create an object from ESI and return it."""
    obj, _ = model_class.objects.get_or_create_esi(*args, **kwargs)
    return obj


def get_or_create_eve_entity(*args, **kwargs) -> EveEntity:
    """Get or create an EveEntity object from ESI and return it."""
    obj = get_or_create_esi_obj(EveEntity, *args, **kwargs)
    return obj


def get_or_create_eve_type(*args, **kwargs) -> EveType:
    """Get or create an EveEntity object from ESI and return it."""
    obj = get_or_create_esi_obj(EveType, *args, **kwargs)
    return obj


def floating_icon_with_text_html(
    icon_url: str, lines: List[Union[str, SafeText]]
) -> SafeText:
    """Return HTML for a multi-line paragraph with a floating icon on the left.

    HTML in lines will not be escaped if they are marked as safe.
    """
    icon_html = format_html(('<img src="{}" class="floating-icon">'), icon_url)
    text_html = format_html_join(mark_safe("<br>"), "{}", ((line,) for line in lines))
    result_html = format_html("<p>{}{}</p>", icon_html, text_html)
    return result_html
