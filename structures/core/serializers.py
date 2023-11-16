"""JSON serializers for Structures."""

# pylint: disable=missing-class-docstring

import re
from abc import ABC, abstractmethod
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from eveuniverse.core import dotlan
from eveuniverse.models import EvePlanet

from allianceauth.eveonline.models import EveCharacter
from app_utils.datetime import DATETIME_FORMAT, timeuntil_str
from app_utils.views import (
    BootstrapStyle,
    bootstrap_label_html,
    format_html_lazy,
    link_html,
    no_wrap_html,
    yesno_str,
    yesnonone_str,
)

from structures.app_settings import STRUCTURES_SHOW_FUEL_EXPIRES_RELATIVE
from structures.constants import EveGroupId
from structures.helpers import floating_icon_with_text_html
from structures.models import EveSpaceType, PocoDetails, Structure


class _AbstractStructureListSerializer(ABC):
    """Converting a list of structure objects into a dict for JSON."""

    ICON_RENDER_SIZE = 64

    def __init__(self, queryset: models.QuerySet, request: HttpRequest):
        self.queryset = queryset
        self._request = request

    def to_list(self) -> list:
        """Serialize all objects into a list."""
        return [self.serialize_object(obj) for obj in self.queryset]

    @abstractmethod
    def serialize_object(self, structure: Structure) -> dict:
        """Serialize one objects into a dict."""
        return {"id": structure.id}

    def _add_owner(self, structure: Structure, row: dict):
        corporation = structure.owner.corporation
        if corporation.alliance:
            alliance_name = corporation.alliance.alliance_name
            alliance_ticker = corporation.alliance.alliance_ticker
        else:
            alliance_name = alliance_ticker = ""

        if not structure.owner.is_structure_sync_fresh:
            update_warning_html = format_html(
                ' <i class="fas fa-exclamation-circle text-warning" '
                'title="Data has not been updated for a while and may be outdated."></i>'
            )
        else:
            update_warning_html = ""

        alliance_text = format_html(
            "<em>{}</em> {}", alliance_ticker, update_warning_html
        )
        owner_link = link_html(
            dotlan.corporation_url(corporation.corporation_name),
            corporation.corporation_name,
        )
        owner_display_html = floating_icon_with_text_html(
            corporation.logo_url(size=self.ICON_RENDER_SIZE),
            [owner_link, alliance_text],
        )
        row["owner"] = {
            "display": owner_display_html,
            "value": corporation.corporation_name,
        }
        row["alliance_name"] = (
            f"{alliance_name} [{alliance_ticker}]" if alliance_ticker else alliance_name
        )
        row["corporation_name"] = corporation.corporation_name

    def _add_location(self, structure: Structure, row: dict):
        solar_system = structure.eve_solar_system

        # location
        row["region_name"] = solar_system.eve_constellation.eve_region.name
        row["solar_system_name"] = solar_system.name
        solar_system_url = dotlan.solar_system_url(solar_system.name)
        if structure.eve_moon:
            location_name = structure.eve_moon.name
        elif structure.eve_planet:
            location_name = structure.eve_planet.name
        else:
            location_name = row["solar_system_name"]

        location_html = format_html(
            '<a href="{}">{}</a><br><em>{}</em>',
            solar_system_url,
            no_wrap_html(location_name),
            no_wrap_html(row["region_name"]),
        )
        row["location"] = {"display": location_html, "value": location_name}

    def _add_type(self, structure: Structure, row: dict):
        structure_type = structure.eve_type

        # category
        my_group = structure_type.eve_group
        row["group_name"] = my_group.name
        try:
            my_category = my_group.eve_category
            row["category_name"] = my_category.name
            row["is_starbase"] = structure.is_starbase
        except AttributeError:
            row["category_name"] = ""
            row["is_starbase"] = None

        # type
        type_link_html = link_html(structure_type.profile_url, structure_type.name)
        type_html = floating_icon_with_text_html(
            structure_type.icon_url(size=self.ICON_RENDER_SIZE),
            [type_link_html, format_html("<em>{}</em>", row["group_name"])],
        )
        row["type"] = {"display": type_html, "value": structure_type.name}
        row["type_name"] = structure_type.name

        # poco
        row["is_poco"] = structure.is_poco

    def _add_name_and_tags(
        self, structure: Structure, row: dict, check_tags: bool = True
    ):
        structure_name_html = escape(structure.name)
        tags = []
        if check_tags and structure.tags.exists():
            tags += [x.html for x in structure.tags.all()]
            structure_name_html += format_html("<br>{}", mark_safe(" ".join(tags)))

        row["structure_name_and_tags"] = structure_name_html

    def _add_reinforcement_infos(self, structure: Structure, row: dict):
        row["is_reinforced"] = structure.is_reinforced
        row["is_reinforced_str"] = yesno_str(structure.is_reinforced)

    def _add_fuel_and_power(self, structure: Structure, row: dict):
        fuel_expires_display, fuel_expires_timestamp = self._calc_fuel_infos(structure)
        last_online_at_display = self._calc_online_infos(structure)

        if fuel_expires_display or last_online_at_display:
            display = format_html(
                "{}<br>{}", no_wrap_html(fuel_expires_display), last_online_at_display
            )
        else:
            display = fuel_expires_display

        row["fuel_and_power"] = {
            "display": display,
            "fuel_expires_at": fuel_expires_timestamp,
        }
        row["power_mode_str"] = structure.get_power_mode_display()

    def _calc_fuel_infos(self, structure: Structure):
        if structure.is_poco:
            fuel_expires_display = ""
            fuel_expires_timestamp = None

        elif structure.is_low_power:
            fuel_expires_display = format_html_lazy(
                bootstrap_label_html(
                    structure.get_power_mode_display(), BootstrapStyle.WARNING
                )
            )
            fuel_expires_timestamp = None

        elif structure.is_abandoned:
            fuel_expires_display = format_html_lazy(
                bootstrap_label_html(
                    structure.get_power_mode_display(), BootstrapStyle.DANGER
                )
            )
            fuel_expires_timestamp = None

        elif structure.is_maybe_abandoned:
            fuel_expires_display = format_html_lazy(
                bootstrap_label_html(
                    structure.get_power_mode_display(), BootstrapStyle.WARNING
                )
            )
            fuel_expires_timestamp = None

        elif structure.fuel_expires_at:
            fuel_expires_timestamp = structure.fuel_expires_at.isoformat()
            if STRUCTURES_SHOW_FUEL_EXPIRES_RELATIVE:
                fuel_expires_display = timeuntil_str(
                    structure.fuel_expires_at - now(), show_seconds=False
                )
                if not fuel_expires_display:
                    fuel_expires_display = "?"
                    fuel_expires_timestamp = None
            else:
                if structure.fuel_expires_at >= now():
                    fuel_expires_display = structure.fuel_expires_at.strftime(
                        DATETIME_FORMAT
                    )
                else:
                    fuel_expires_display = "?"
                    fuel_expires_timestamp = None
        else:
            fuel_expires_display = "-"
            fuel_expires_timestamp = None
        return fuel_expires_display, fuel_expires_timestamp

    def _calc_online_infos(self, structure: Structure):
        if structure.is_poco:
            return ""

        if structure.is_full_power:
            last_online_at_display = format_html_lazy(
                bootstrap_label_html(
                    structure.get_power_mode_display(), BootstrapStyle.SUCCESS
                )
            )
        elif structure.is_maybe_abandoned:
            last_online_at_display = format_html_lazy(
                bootstrap_label_html(
                    structure.get_power_mode_display(), BootstrapStyle.WARNING
                )
            )

        elif structure.is_abandoned:
            last_online_at_display = format_html_lazy(
                bootstrap_label_html(
                    structure.get_power_mode_display(), BootstrapStyle.DANGER
                )
            )

        elif structure.last_online_at:
            if STRUCTURES_SHOW_FUEL_EXPIRES_RELATIVE:
                last_online_at_display = timeuntil_str(
                    now() - structure.last_online_at, show_seconds=False
                )
                if not last_online_at_display:
                    last_online_at_display = "?"
            else:
                last_online_at_display = structure.last_online_at.strftime(
                    DATETIME_FORMAT
                )
        else:
            last_online_at_display = ""

        return last_online_at_display

    def _add_state_and_core(
        self, structure: Structure, row: dict, request: HttpRequest
    ):
        state_str, state_details = self._calc_state_infos(structure, request)
        core_status, has_core = self._calc_core_infos(structure)

        row["state_str"] = state_str
        row["state_details"] = format_html("{}<br>{}", state_details, core_status)
        row["core_status_str"] = yesnonone_str(has_core)

    def _calc_state_infos(self, structure: Structure, request):
        if structure.is_poco:
            return "-", "-"

        state_str = structure.get_state_display().capitalize()  # type: ignore
        state_details = format_html(state_str)
        if structure.state_timer_end:
            state_details += format_html(
                "<br>{}",
                no_wrap_html(structure.state_timer_end.strftime(DATETIME_FORMAT)),
            )

        if (
            request.user.has_perm("structures.view_all_unanchoring_status")
            and structure.unanchors_at
        ):
            state_details += format_html(
                "<br>Unanchoring until {}",
                no_wrap_html(structure.unanchors_at.strftime(DATETIME_FORMAT)),
            )

        return state_str, state_details

    def _calc_core_infos(self, structure: Structure):
        if structure.eve_type.eve_group_id not in {  # type: ignore
            EveGroupId.CITADEL,
            EveGroupId.ENGINEERING_COMPLEX,
            EveGroupId.REFINERY,
        }:
            return "", None

        if structure.has_core is True:
            has_core = True
            core_status = ""

        elif structure.has_core is False:
            has_core = False
            core_status = bootstrap_label_html("Core missing", BootstrapStyle.DANGER)

        else:
            has_core = None
            core_status = bootstrap_label_html("No core status", BootstrapStyle.WARNING)

        return core_status, has_core

    def _add_jump_fuel_level(self, structure: Structure, row: dict):
        if hasattr(structure, "jump_fuel_quantity_2"):
            row["jump_fuel_quantity"] = structure.jump_fuel_quantity_2  # type: ignore
        else:
            row["jump_fuel_quantity"] = None

    def _add_details_widget(
        self, structure: Structure, row: dict, request: HttpRequest
    ):
        """Add details widget when applicable"""
        if structure.has_fitting and request.user.has_perm(  # type: ignore
            "structures.view_structure_fit"
        ):
            ajax_url = reverse("structures:structure_details", args=[structure.id])
            row["details"] = format_html(
                '<button type="button" class="btn btn-default" '
                'data-toggle="modal" data-target="#modalUpwellDetails" '
                f"data-ajax_url={ajax_url} "
                f'title="{_("Show fitting")}">'
                '<i class="fas fa-search"></i></button>'
            )

        elif structure.is_poco:
            ajax_url = reverse("structures:poco_details", args=[structure.id])
            row["details"] = format_html(
                '<button type="button" class="btn btn-default" '
                'data-toggle="modal" data-target="#modalPocoDetails" '
                f"data-ajax_url={ajax_url} "
                f'title="{_("Show details")}">'
                '<i class="fas fa-search"></i></button>'
            )

        elif structure.is_starbase:
            ajax_url = reverse("structures:starbase_detail", args=[structure.id])
            row["details"] = format_html(
                '<button type="button" class="btn btn-default" '
                'data-toggle="modal" data-target="#modalStarbaseDetail" '
                f"data-ajax_url={ajax_url} "
                f'title="{_("Show details")}">'
                '<i class="fas fa-search"></i></button>'
            )
        else:
            row["details"] = ""

    @staticmethod
    def extract_planet_type_name(eve_planet: EvePlanet) -> str:
        """Extract short name of planet type."""
        matches = re.findall(r"Planet \((\S*)\)", eve_planet.eve_type.name)
        return matches[0] if matches else ""


class StructureListSerializer(_AbstractStructureListSerializer):
    def __init__(self, queryset: models.QuerySet, request: HttpRequest):
        super().__init__(queryset, request=request)
        self.queryset = self.queryset.prefetch_related("tags")

    def serialize_object(self, structure: Structure) -> dict:
        row = super().serialize_object(structure)
        self._add_owner(structure, row)
        self._add_location(structure, row)
        self._add_type(structure, row)
        self._add_name_and_tags(structure, row)
        self._add_reinforcement_infos(structure, row)
        self._add_fuel_and_power(structure, row)
        self._add_state_and_core(structure, row, self._request)
        self._add_details_widget(structure, row, self._request)
        self._add_jump_fuel_level(structure, row)
        return row


class PocoListSerializer(_AbstractStructureListSerializer):
    def __init__(
        self,
        queryset: models.QuerySet,
        request: HttpRequest,
        character: Optional[EveCharacter] = None,
    ):
        super().__init__(queryset, request=request)
        self.queryset = self.queryset.select_related(
            "eve_planet",
            "eve_planet__eve_type",
            "eve_planet__eve_type__eve_group",
            "eve_type",
            "eve_type__eve_group",
            "eve_solar_system",
            "eve_solar_system__eve_constellation__eve_region",
            "poco_details",
            "owner__corporation",
            "owner__corporation__alliance",
        )
        if not request:
            raise ValueError("request can not be None")

        self.character = character

    def serialize_object(self, structure: Structure) -> dict:
        row = super().serialize_object(structure)
        self._add_owner(structure, row)
        self._add_location(structure, row)
        self._add_planet(structure, row)
        self._add_has_access_and_tax(structure, row, self.character)
        return row

    def _add_location(self, structure: Structure, row: dict):
        if structure.eve_solar_system.is_low_sec:
            space_badge_type = "warning"
        elif structure.eve_solar_system.is_high_sec:
            space_badge_type = "success"
        else:
            space_badge_type = "danger"
        space_type = EveSpaceType.from_solar_system(structure.eve_solar_system)

        solar_system_name = structure.eve_solar_system.name
        solar_system_html = format_html(
            "{}<br>{}",
            link_html(dotlan.solar_system_url(solar_system_name), solar_system_name),
            bootstrap_label_html(text=space_type.label, label=space_badge_type),
        )

        constellation_name = structure.eve_solar_system.eve_constellation.name
        region_name = structure.eve_solar_system.eve_constellation.eve_region.name
        constellation_html = format_html(
            "{}<br><em>{}</em>", constellation_name, region_name
        )

        row["constellation_html"] = {
            "display": constellation_html,
            "sort": constellation_name,
        }
        row["solar_system_html"] = {
            "display": solar_system_html,
            "sort": solar_system_name,
        }
        row["solar_system"] = solar_system_name
        row["constellation"] = f"{region_name} - {constellation_name}"
        row["region"] = region_name
        row["space_type"] = space_type.value

    def _add_planet(self, structure: Structure, row: dict):
        if structure.eve_planet:
            planet_type_name = self.extract_planet_type_name(structure.eve_planet)
            planet_name = structure.eve_planet.name
            icon_url = structure.eve_planet.eve_type.icon_url(
                size=self.ICON_RENDER_SIZE
            )
        else:
            planet_name = planet_type_name = "?"
            icon_url = ""

        planet_plus_icon_html = floating_icon_with_text_html(
            icon_url, [planet_name, format_html("<em>{}</em>", planet_type_name)]
        )

        row["planet_plus_icon"] = {
            "display": planet_plus_icon_html,
            "sort": planet_name,
        }
        row["planet_type_name"] = planet_type_name
        row["planet_name"] = planet_name

    def _add_has_access_and_tax(
        self, structure: Structure, row: dict, character: Optional[EveCharacter]
    ):
        if character:
            access_info = self._determine_access_and_tax_for_character(
                structure, character
            )
        else:
            access_info = None

        has_access_html = ""
        has_access_str = "?"
        tax = None
        tax_html = "?"
        if not access_info:
            has_access_html = format_html_lazy(
                '<i class="fas fa-question" title="{}"></i>',
                _("Unknown if character has access"),
            )

        else:
            dubious_access_text = _(
                "Access and tax for characters, which are not a member of "
                "the owner corporation or it's alliance may not be accurate."
            )

            if not access_info.has_access:
                has_access_html = format_html_lazy(
                    '<i class="fas fa-times text-danger text-tooltip" title="{}"></i>',
                    _("No access"),
                )
                has_access_str = _("no")

            elif access_info.has_access:
                if access_info.is_confident:
                    has_access_html = format_html_lazy(
                        '<i class="fas fa-check text-success text-tooltip" title="{}"></i>',
                        _("Has access"),
                    )
                    has_access_str = _("yes")

                else:
                    has_access_html = format_html_lazy(
                        '<span class="text-tooltip" title="{}">'
                        '(<i class="fas fa-check text-success text-tooltip"></i>)</span>',
                        dubious_access_text,
                    )
                    has_access_str = _("yes(?)")

            if access_info.has_access and access_info.tax_rate is not None:
                tax = access_info.tax_rate * 100
                tax_str = f"{tax:.0f} %"
                if not access_info.is_confident:
                    tax_html = format_html_lazy(
                        '<span class="text-tooltip" title="{}">{}</span>',
                        dubious_access_text,
                        tax_str,
                    )
                else:
                    tax_html = tax_str
            else:
                tax = None
                tax_html = "?"

        row["has_access_html"] = {"display": has_access_html, "sort": has_access_str}
        row["has_access_str"] = has_access_str
        row["tax"] = {"display": tax_html, "sort": tax}

    def _determine_access_and_tax_for_character(
        self, structure, character
    ) -> Optional[PocoDetails.PocoCharacterAccessInfo]:
        try:
            details: PocoDetails = structure.poco_details  # type: ignore
        except (AttributeError, ObjectDoesNotExist):
            return None

        return details.determine_access_and_tax_for_character(character)
