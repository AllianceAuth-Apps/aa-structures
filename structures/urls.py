"""Tasks for Structures."""

from django.urls import path
from django.views.decorators.cache import never_cache

from .views import public, statistics, status, structures

app_name = "structures"

urlpatterns = [
    path("", structures.index, name="index"),
    path("list", structures.structure_list, name="structure_list"),
    path(
        "structure_list_data/<str:selection>",
        structures.structure_list_data,
        name="structure_list_data",
    ),
    path(
        "add_structure_owner",
        structures.add_structure_owner,
        name="add_structure_owner",
    ),
    path("service_status", never_cache(status.service_status), name="service_status"),
    path(
        "<int:structure_id>/structure_details",
        structures.structure_details,
        name="structure_details",
    ),
    path(
        "<int:structure_id>/poco_details",
        structures.poco_details,
        name="poco_details",
    ),
    path(
        "<int:structure_id>/starbase_detail",
        structures.starbase_detail,
        name="starbase_detail",
    ),
    # public
    path("public", public.public, name="public"),
    path(
        "public_poco_list_data/<int:character_id>",
        public.public_poco_list_data,
        name="public_poco_list_data",
    ),
    # statistics
    path("statistics", statistics.statistics, name="statistics"),
    path(
        "summary_data", statistics.structure_summary_data, name="structure_summary_data"
    ),
]
