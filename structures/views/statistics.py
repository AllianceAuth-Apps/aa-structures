"""Views for statistics page."""

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, F, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from eveuniverse.core import dotlan, eveimageserver

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag
from app_utils.views import link_html

from structures import __title__
from structures.constants import EveCategoryId, EveGroupId, EveTypeId
from structures.helpers import floating_icon_with_text_html
from structures.models import Structure

from .common import add_common_context, add_common_data_export

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def _default_if_none(value, default=None):
    """Return default if a value is None."""
    if value is None:
        return default
    return value


@login_required
@permission_required("structures.basic_access")
def statistics(request: HttpRequest) -> HttpResponse:
    """Return view to render Statistics page."""
    ajax_url = reverse("structures:structure_summary_data")
    data_export = add_common_data_export(
        {
            "ajax_url": ajax_url,
            "filter_titles": {"alliance": _("Alliance")},
        }
    )
    context = {"data_export": data_export}
    return render(request, "structures/statistics.html", add_common_context(context))


@login_required
@permission_required("structures.basic_access")
def structure_summary_data(request: HttpRequest) -> JsonResponse:
    """View returning data for structure summary page."""
    summary_qs = (
        Structure.objects.visible_for_user(request.user)
        .values(
            corporation_id=F("owner__corporation__corporation_id"),
            corporation_name=F("owner__corporation__corporation_name"),
            alliance_name=F("owner__corporation__alliance__alliance_name"),
            alliance_ticker=F("owner__corporation__alliance__alliance_ticker"),
        )
        .annotate(
            ec_count=Count(
                "id", filter=Q(eve_type__eve_group=EveGroupId.ENGINEERING_COMPLEX)
            )
        )
        .annotate(
            refinery_count=Count(
                "id", filter=Q(eve_type__eve_group=EveGroupId.REFINERY)
            )
        )
        .annotate(
            citadel_count=Count("id", filter=Q(eve_type__eve_group=EveGroupId.CITADEL))
        )
        .annotate(
            upwell_count=Count(
                "id",
                filter=Q(eve_type__eve_group__eve_category=EveCategoryId.STRUCTURE),
            )
        )
        .annotate(poco_count=Count("id", filter=Q(eve_type=EveTypeId.CUSTOMS_OFFICE)))
        .annotate(
            starbase_count=Count(
                "id", filter=Q(eve_type__eve_group__eve_category=EveCategoryId.STARBASE)
            )
        )
    )
    data = []
    for row in summary_qs:
        other_count = (
            row["upwell_count"]
            - row["ec_count"]
            - row["refinery_count"]
            - row["citadel_count"]
        )
        total = row["upwell_count"] + row["poco_count"] + row["starbase_count"]

        corporation_id = row["corporation_id"]
        corporation_name = row["corporation_name"]
        alliance_name = _default_if_none(row["alliance_name"], "")
        alliance_ticker = _default_if_none(row["alliance_ticker"], "")
        corporation_icon_url = eveimageserver.corporation_logo_url(
            corporation_id, size=64
        )
        owner_link = link_html(
            dotlan.corporation_url(corporation_name), corporation_name
        )
        owner_display_html = floating_icon_with_text_html(
            corporation_icon_url, [owner_link, alliance_ticker]
        )
        owner_html = {"display": owner_display_html, "value": corporation_name}
        alliance_name_str = (
            f"{alliance_name} [{alliance_ticker}]" if alliance_ticker else alliance_name
        )

        data.append(
            {
                "id": int(corporation_id),
                "owner": owner_html,
                "corporation_name": corporation_name,
                "alliance_name": alliance_name_str,
                "citadel_count": row["citadel_count"],
                "ec_count": row["ec_count"],
                "refinery_count": row["refinery_count"],
                "other_count": other_count,
                "poco_count": row["poco_count"],
                "starbase_count": row["starbase_count"],
                "total": total,
            }
        )
    return JsonResponse({"data": data})
