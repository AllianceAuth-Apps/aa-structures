"""JSON serializers for Structures."""

# pylint: disable=missing-class-docstring

import re
from abc import ABC, abstractmethod

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EvePlanet

from allianceauth.eveonline.evelinks import dotlan
from app_utils.datetime import DATETIME_FORMAT, timeuntil_str
from app_utils.views import (
    BootstrapStyle,
    bootstrap_label_html,
    format_html_lazy,
    image_html,
    link_html,
    no_wrap_html,
    yesno_str,
    yesnonone_str,
)

from structures.app_settings import STRUCTURES_SHOW_FUEL_EXPIRES_RELATIVE
from structures.constants import EveGroupId, EveTypeId
from structures.helpers import icon_with_two_lines_html
from structures.models import EveSpaceType, Structure, StructureItem, StructureService


class _AbstractStructureListSerializer(ABC):
    """Converting a list of structure objects into a dict for JSON."""

    ICON_RENDER_SIZE = 64
    ICON_OUTPUT_SIZE = 40

    def __init__(self, queryset: models.QuerySet, request=None):
        self.queryset = queryset
        self._request = request

    def has_data(self) -> bool:
        """Return True if this query returns any data, else False."""
        return self.queryset.exists()

    def count(self) -> bool:
        """Return number of objects in this query."""
        return self.queryset.count()

    def to_list(self) -> list:
        """Serialize all objects into a list."""
        return [self.serialize_object(obj) for obj in self.queryset]

    @abstractmethod
    def serialize_object(self, structure: Structure) -> dict:
        """Serialize one objects into a dict."""
        return {"id": structure.id}

    def _icon_html(self, url) -> str:  # TODO: Try to remove
        return image_html(url, size=self.ICON_OUTPUT_SIZE)

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

        secondary_text = format_html("{}{}", alliance_ticker, update_warning_html)
        owner_display_html = icon_with_two_lines_html(
            icon_url=corporation.logo_url(size=self.ICON_RENDER_SIZE),
            primary_text=corporation.corporation_name,
            primary_url=dotlan.corporation_url(corporation.corporation_name),
            secondary_text=secondary_text,
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
        type_html = icon_with_two_lines_html(
            icon_url=structure_type.icon_url(size=self.ICON_RENDER_SIZE),
            primary_text=structure_type.name,
            primary_url=structure_type.profile_url,
            secondary_text=row["group_name"],
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

    def _add_services(self, structure: Structure, row: dict):
        if row["is_poco"] or row["is_starbase"]:
            row["services"] = "-"
            return
        services = []
        for service in structure.services.all():
            service_name_html = no_wrap_html(
                format_html("<small>{}</small>", service.name)
            )
            if service.state == StructureService.State.OFFLINE:
                service_name_html = format_html("<del>{}</del>", service_name_html)
            services.append({"name": service.name, "html": service_name_html})
        row["services"] = (
            "<br>".join(
                map(lambda x: x["html"], sorted(services, key=lambda x: x["name"]))
            )
            if services
            else "-"
        )

    def _add_reinforcement_infos(self, structure: Structure, row: dict):
        row["is_reinforced"] = structure.is_reinforced
        row["is_reinforced_str"] = yesno_str(structure.is_reinforced)
        if structure.is_starbase:
            row["reinforcement"] = "-"
        else:
            if structure.reinforce_hour is not None:
                row["reinforcement"] = f"{structure.reinforce_hour:02d}:00"
            else:
                row["reinforcement"] = ""

    def _add_fuel_and_power(self, structure: Structure, row: dict):
        fuel_expires_display, fuel_expires_timestamp = self._calc_fuel_infos(structure)
        last_online_at_display = self._calc_online_infos(structure)

        display = format_html(
            "{}<br>{}", no_wrap_html(fuel_expires_display), last_online_at_display
        )
        row["fuel_and_power"] = {
            "display": display,
            "fuel_expires_at": fuel_expires_timestamp,
        }
        row["power_mode_str"] = structure.get_power_mode_display()

    def _calc_fuel_infos(self, structure: Structure):
        if structure.is_poco:
            fuel_expires_display = "-"
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
            return "-"

        elif structure.is_full_power:
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
                    last_online_at_display = "- " + last_online_at_display
            else:
                last_online_at_display = structure.last_online_at.strftime(
                    DATETIME_FORMAT
                )
        else:
            last_online_at_display = "-"

        return last_online_at_display

    def _add_state_and_core(self, structure: Structure, row: dict, request):
        state_str, state_details = self._calc_state_infos(structure, request)
        core_status, has_core = self._calc_core_infos(structure)

        row["state_str"] = state_str
        row["state_details"] = format_html("{}<br>{}", state_details, core_status)
        row["core_status_str"] = yesnonone_str(has_core)

    def _calc_state_infos(self, structure: Structure, request):
        if structure.is_poco:
            return "-", "-"

        state_str = structure.get_state_display().capitalize()
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
        if structure.eve_type.eve_group_id not in {
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

    def _add_details_widget(self, structure: Structure, row: dict, request):
        """Add details widget when applicable"""
        if structure.has_fitting and request.user.has_perm(
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
        elif structure.has_poco_details:
            ajax_url = reverse("structures:poco_details", args=[structure.id])
            row["details"] = format_html(
                '<button type="button" class="btn btn-default" '
                'data-toggle="modal" data-target="#modalPocoDetails" '
                f"data-ajax_url={ajax_url} "
                f'title="{_("Show details")}">'
                '<i class="fas fa-search"></i></button>'
            )
        elif structure.has_starbase_detail:
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
    def __init__(self, queryset: models.QuerySet, request=None):
        super().__init__(queryset, request=request)
        self.queryset = (
            self.queryset.prefetch_related("tags", "services")
            .annotate_has_poco_details()
            .annotate_has_starbase_detail()
        )

    def serialize_object(self, structure: Structure) -> dict:
        row = super().serialize_object(structure)
        self._add_owner(structure, row)
        self._add_location(structure, row)
        self._add_type(structure, row)
        self._add_name_and_tags(structure, row)
        self._add_services(structure, row)
        self._add_reinforcement_infos(structure, row)
        self._add_fuel_and_power(structure, row)
        self._add_state_and_core(structure, row, self._request)
        self._add_details_widget(structure, row, self._request)
        return row


class JumpGatesListSerializer(_AbstractStructureListSerializer):
    def __init__(self, queryset: models.QuerySet, request=None):
        super().__init__(queryset, request=request)
        self.queryset = self.queryset.annotate(
            jump_fuel_quantity_2=Sum(
                "items__quantity",
                filter=Q(
                    items__eve_type=EveTypeId.LIQUID_OZONE,
                    items__location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
                ),
            )
        )

    def serialize_object(self, structure: Structure) -> dict:
        row = super().serialize_object(structure)
        self._add_owner(structure, row)
        self._add_location(structure, row)
        self._add_type(structure, row)
        self._add_name_and_tags(structure, row, check_tags=False)
        self._add_jump_fuel_level(structure, row)
        self._add_fuel_and_power(structure, row)
        self._add_reinforcement_infos(structure, row)
        self._add_state_and_core(structure, row, self._request)
        return row

    def _add_jump_fuel_level(self, structure: Structure, row: dict):
        row["jump_fuel_quantity"] = structure.jump_fuel_quantity_2


class PocoListSerializer(_AbstractStructureListSerializer):
    def __init__(self, queryset: models.QuerySet, request=None):
        super().__init__(queryset, request=request)
        self.queryset = self.queryset.select_related(
            "eve_planet",
            "eve_planet__eve_type",
            "eve_type",
            "eve_type__eve_group",
            "eve_solar_system",
            "eve_solar_system__eve_constellation__eve_region",
            "poco_details",
            "owner__corporation",
        )
        if not request:
            raise ValueError("request can not be None")
        try:
            self.main_character = request.user.profile.main_character
        except (AttributeError, ObjectDoesNotExist):
            self.main_character = None

    def serialize_object(self, structure: Structure) -> dict:
        row = super().serialize_object(structure)
        self._add_solar_system(structure, row)
        self._add_planet(structure, row)
        self._add_has_access_and_tax(structure, row, self.main_character)
        return row

    def _add_solar_system(self, structure: Structure, row: dict):
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
            bootstrap_label_html(text=space_type.value, label=space_badge_type),
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
        row["constellation"] = constellation_name
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

        planet_plus_icon_html = icon_with_two_lines_html(
            icon_url=structure.eve_type.icon_url(size=self.ICON_RENDER_SIZE),
            primary_text=planet_name,
        )
        row["planet_plus_icon"] = {
            "display": planet_plus_icon_html,
            "sort": planet_name,
        }
        planet_type_plus_icon_html = icon_with_two_lines_html(
            icon_url=icon_url, primary_text=planet_type_name
        )
        row["planet_type_plus_icon"] = {
            "display": planet_type_plus_icon_html,
            "sort": planet_type_name,
        }
        row["planet_type_name"] = planet_type_name

    def _add_has_access_and_tax(self, structure: Structure, row: dict, main_character):
        tax = None
        has_access = None
        if main_character:
            try:
                details = structure.poco_details
            except (AttributeError, ObjectDoesNotExist):
                pass
            else:
                tax = details.tax_for_character(main_character)
                has_access = details.has_character_access(main_character)

        if has_access is True:
            has_access_html = (
                '<i class="fas fa-check text-success" title="Has access"></i>'
            )
            has_access_str = _("yes")
        elif has_access is False:
            has_access_html = (
                '<i class="fas fa-times text-danger" title="No access"></i>'
            )
            has_access_str = _("no")
        else:
            has_access_html = '<i class="fas fa-question" title="Unknown"></i>'
            has_access_str = "?"

        row["has_access_html"] = {"display": has_access_html, "sort": has_access_str}
        row["has_access_str"] = has_access_str
        row["tax"] = f"{tax * 100:.0f} %" if tax else "?"
