"""functions for loading test data and for building mocks"""

import datetime as dt
import json
import logging
from collections import namedtuple
from pathlib import Path
from random import randrange
from typing import Any, Dict, List

from django.forms.models import model_to_dict
from django.utils.timezone import now
from eveuniverse.tests.testdata.factories_2 import EveMoonFactory, EvePlanetFactory

from structures.core.notification_types import NotificationType
from structures.models import Notification, Owner
from structures.tests.testdata.factories import (
    CustomsOfficeFactory,
    EveEntityAllianceFactory,
    EveEntityCharacterFactory,
    EveEntityCorporationFactory,
    EveSolarSystemLowSecFactory,
    EveSolarSystemNullSecFactory,
    IHUBTypeFactory,
    MoonOreTypeFactory,
    NotificationFactory,
    RefineryFactory,
    SkyhookFactory,
    StarbaseFactory,
    StructureFactory,
    TCUTypeFactory,
)

_current_folder = Path(__file__).parent
_FILENAME_EVEUNIVERSE_TESTDATA = "eveuniverse.json"

logger = logging.getLogger(__name__)


def test_data_filename():
    return f"{_current_folder}/{_FILENAME_EVEUNIVERSE_TESTDATA}"


##############################
# internal functions


def _load_notifications() -> List[Dict[str, Any]]:
    with (_current_folder / "notifications.json").open("r", encoding="utf-8") as f:
        _notifications = json.load(f)

    # update timestamp to current
    for notification in _notifications:
        notification["timestamp"] = now() - dt.timedelta(
            hours=randrange(3), minutes=randrange(60), seconds=randrange(60)
        )

    return _notifications


notifications = _load_notifications()


###################################
# helper functions
#


def load_notification_by_type(
    owner: Owner, notif_type: NotificationType
) -> Notification:
    for notification in notifications:
        if notification["type"] == notif_type.value:
            return NotificationFactory(
                owner=owner,
                notif_type=notif_type.value,
                text=notification.get("text", ""),
            )
    raise ValueError(f"Could not find notif for type: {notif_type}")


def load_notification_entities(owner: Owner):
    EveSolarSystemLowSecFactory(id=30002537, name="Amamake")
    EveSolarSystemNullSecFactory(id=30000474, name="1-PGSG")
    EvePlanetFactory(id=40161469, eve_type__id=2016, eve_solar_system__id=30000474)
    EveMoonFactory(id=40161465, eve_planet__id=40161469)
    EveMoonFactory(id=40161466, eve_planet__id=40161469)

    IHUBTypeFactory()
    MoonOreTypeFactory(id=46300)
    MoonOreTypeFactory(id=46301)
    MoonOreTypeFactory(id=46302)
    MoonOreTypeFactory(id=46303)
    TCUTypeFactory()

    EveEntityAllianceFactory(id=3001)
    EveEntityAllianceFactory(id=3002)
    EveEntityAllianceFactory(id=3011)
    EveEntityAllianceFactory(id=500012, name="Blood Raider Covenant")
    EveEntityCharacterFactory(id=1001)
    EveEntityCharacterFactory(id=1011)
    EveEntityCorporationFactory(id=1000134, name="Blood Raiders")
    EveEntityCorporationFactory(id=1000137, name="DED")
    EveEntityCorporationFactory(id=2001)
    EveEntityCorporationFactory(id=2002)
    EveEntityCorporationFactory(id=2011)
    EveEntityCorporationFactory(id=2021)
    EveEntityCorporationFactory(id=2901)
    EveEntityCorporationFactory(id=2902)

    CustomsOfficeFactory(
        eve_type__id=2233,
        eve_planet__id=40161469,
        owner=owner,
    )
    RefineryFactory(
        eve_moon__id=40161465,
        eve_type__id=35835,
        id=1000000000002,
        owner=owner,
    )
    StarbaseFactory(
        eve_moon__id=40161465,
        eve_type__id=16213,
        owner=owner,
    )
    StructureFactory(
        eve_solar_system__id=30002537,
        eve_type__id=35832,
        id=1000000000001,
        owner=owner,
    )
    SkyhookFactory(
        eve_planet__id=40161469,
        eve_type__id=81080,
        id=1000000010001,
        owner=owner,
    )


def load_notification_objects(owner: Owner, in_bulk=True):
    """Loads notification fixtures for an owner.

    Note that the notification require some entities to exit,
    which can be created with ``load_notification_entities()``.

    Args:
    - in_bulk: When disabled, will load notifications one by one (for debugging)
    """
    timestamp_start = now() - dt.timedelta(hours=2)
    objs = [
        _generate_notif_obj_for_owner(owner, timestamp_start, notification)
        for notification in notifications
    ]
    if in_bulk:
        Notification.objects.bulk_create(objs)
    else:
        for obj in objs:
            logger.info("Creating notif: %s", model_to_dict(obj))
            obj.save()


def _generate_notif_obj_for_owner(
    owner: Owner, timestamp_start: dt.datetime, notification: dict
):
    notification_id = notification["notification_id"]
    text = notification["text"] if "text" in notification else None
    is_read = notification["is_read"] if "is_read" in notification else None
    timestamp_start = timestamp_start + dt.timedelta(minutes=5)
    params = {
        "notification_id": notification_id,
        "owner": owner,
        "sender_id": notification["sender_id"],
        "timestamp": timestamp_start,
        "notif_type": notification["type"],
        "text": text,
        "is_read": is_read,
        "last_updated": now(),
        "is_sent": False,
    }
    return Notification(**params)


# def generate_eve_entities_from_auth_entities():
#     """Generate EveEntity objects from existing Auth EveOnline objects."""

#     def add_eve_entity(id, name, category):
#         if id not in existing_ids:
#             objs.append(EveEntity(id=id, category=category, name=name))
#             existing_ids.add(id)

#     existing_ids = set(EveEntity.objects.values_list("id", flat=True))
#     objs = []
#     for character in EveCharacter.objects.exclude(character_id__in=existing_ids):
#         add_eve_entity(
#             id=character.character_id,
#             name=character.character_name,
#             category=EveEntity.CATEGORY_CHARACTER,
#         )
#         add_eve_entity(
#             id=character.corporation_id,
#             name=character.corporation_name,
#             category=EveEntity.CATEGORY_CORPORATION,
#         )
#         if character.alliance_id:
#             add_eve_entity(
#                 id=character.alliance_id,
#                 name=character.alliance_name,
#                 category=EveEntity.CATEGORY_ALLIANCE,
#             )

#     for corporation in EveCorporationInfo.objects.exclude(
#         corporation_id__in=existing_ids
#     ):
#         add_eve_entity(
#             id=corporation.corporation_id,
#             name=corporation.corporation_name,
#             category=EveEntity.CATEGORY_CORPORATION,
#         )

#     for alliance in EveAllianceInfo.objects.exclude(alliance_id__in=existing_ids):
#         add_eve_entity(
#             id=alliance.alliance_id,
#             name=alliance.alliance_name,
#             category=EveEntity.CATEGORY_ALLIANCE,
#         )

#     EveEntity.objects.bulk_create(objs)


def clone_notification(obj: Notification) -> Notification:
    """Return clone of a Notification."""
    new_object = NotificationFactory(
        sender=obj.sender, notif_type=obj.notif_type, owner=obj.owner, text=obj.text
    )
    return new_object


NearestCelestial = namedtuple(
    "NearestCelestial", ["eve_type", "eve_object", "distance"]
)
