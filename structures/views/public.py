"""Views for public page."""

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from structures import __title__
from structures.constants import EveCategoryId
from structures.core.serializers import PocoListSerializer
from structures.models import Structure

from .common import add_common_context, add_common_data_export

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("structures.basic_access")
def public(request: HttpRequest) -> HttpResponse:
    """Return view to render Public page."""
    characters = (
        EveCharacter.objects.filter(character_ownership__user=request.user)
        .order_by("character_name")
        .values("character_id", "character_name")
    )
    character_id = int(request.GET.get("character_id", 0))
    if not character_id:
        try:
            character_id = request.user.profile.main_character.character_id
        except AttributeError:
            character_id = None

    pocos_count = _public_pocos_query().count()
    selected_character = get_object_or_404(EveCharacter, character_id=character_id)

    ajax_url = reverse(
        "structures:public_poco_list_data", args=[selected_character.character_id]
    )
    data_export = add_common_data_export(
        {
            "ajax_url": ajax_url,
            "filter_titles": {
                "alliance": _("Alliance"),
                "access": _("Access?"),
                "corporation": _("Corporation"),
                "constellation": _("Constellation"),
                "planet_type": _("Planet Type"),
                "region": _("Region"),
                "space_type": _("Space Type"),
                "solar_system": _("Solar System"),
            },
        }
    )
    context = {
        "characters": characters,
        "selected_character": selected_character,
        "pocos_count": pocos_count,
        "data_export": data_export,
    }
    return render(request, "structures/public.html", add_common_context(context))


def public_poco_list_data(request: HttpRequest, character_id: int) -> JsonResponse:
    """List of public POCOs for DataTables."""
    character = get_object_or_404(EveCharacter, character_id=character_id)
    pocos = _public_pocos_query()
    serializer = PocoListSerializer(
        queryset=pocos, request=request, character=character
    )
    data = serializer.to_list()
    return JsonResponse({"data": data})


def _public_pocos_query():
    pocos = Structure.objects.select_related_defaults().filter(
        eve_type__eve_group__eve_category_id=EveCategoryId.ORBITAL,
        owner__are_pocos_public=True,
    )
    return pocos
