"""Skyhook embeds."""

# pylint: disable=missing-class-docstring

import dhooks_lite

from django.utils.translation import gettext as _

from app_utils.datetime import ldap_time_2_datetime

from structures.models import Notification, Webhook

from .helpers import (
    gen_corporation_link,
    gen_solar_system_text,
    target_datetime_formatted,
)
from .main import NotificationBaseEmbed


class NotificationSkyhookEmbed(NotificationBaseEmbed):
    """Base class for most structure related notification embeds."""

    def __init__(self, n: Notification) -> None:
        super().__init__(n)
        type_ = n.eve_structure_type("typeID")
        solar_system = n.eve_solar_system("solarsystemID")
        self._description = _(
            "The %(structure_type)s at **%(planet)s** "
            "in %(solar_system)s belonging to %(owner_link)s "
        ) % {
            "structure_type": type_,
            "planet": n.eve_planet(),
            "solar_system": gen_solar_system_text(solar_system),
            "owner_link": gen_corporation_link(str(n.owner)),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            type_.icon_url(size=self.ICON_DEFAULT_SIZE)
        )


class NotificationSkyhookDeployed(NotificationSkyhookEmbed):
    def __init__(self, n: Notification) -> None:
        super().__init__(n)
        self._title = _("Skyhook has started onlining")
        self._description += _("has started onlining.")
        self._color = Webhook.Color.INFO


class NotificationSkyhookDestroyed(NotificationSkyhookEmbed):
    def __init__(self, n: Notification) -> None:
        super().__init__(n)
        self._title = _("Skyhook destroyed")
        self._description += _("has been destroyed.")
        self._color = Webhook.Color.DANGER


class NotificationSkyhookLostShield(NotificationSkyhookEmbed):
    def __init__(self, n: Notification) -> None:
        super().__init__(n)
        self._title = _("Skyhook lost shield")
        timer_ends_at = ldap_time_2_datetime(self._data["timestamp"])
        self._description += _(
            "has lost its shields and is now in reinforcement state until : %s"
        ) % target_datetime_formatted(timer_ends_at)
        self._color = Webhook.Color.DANGER


class NotificationSkyhookOnline(NotificationSkyhookEmbed):
    def __init__(self, n: Notification) -> None:
        super().__init__(n)
        self._title = _("Skyhook online")
        self._description += _("is now online.")
        self._color = Webhook.Color.SUCCESS


class NotificationSkyhookUnderAttack(NotificationSkyhookEmbed):
    def __init__(self, n: Notification) -> None:
        super().__init__(n)
        self._title = _("Skyhook under attack")
        self._description += _(
            "is under attack by %(attacker)s.\n"
            "%(damage_text)s"
            % {
                "attacker": self.gen_attacker_link(),
                "damage_text": self.compile_damage_text("Percentage"),
            }
        )
        self._color = Webhook.Color.DANGER
