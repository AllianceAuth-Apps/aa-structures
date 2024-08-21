"""functions for loading test data and for building mocks"""

import datetime as dt
import json
import logging
import unicodedata
from collections import namedtuple
from pathlib import Path
from random import randrange

import pytz
from bs4 import BeautifulSoup
from markdown import markdown

from django.forms.models import model_to_dict
from django.utils.timezone import now
from eveuniverse.models import EveEntity

from structures.core.notification_types import NotificationType
from structures.models import Notification, Owner

from .factories import NotificationFactory

_current_folder = Path(__file__).parent
_FILENAME_EVEUNIVERSE_TESTDATA = "eveuniverse.json"

logger = logging.getLogger(__name__)


def test_data_filename():
    return f"{_current_folder}/{_FILENAME_EVEUNIVERSE_TESTDATA}"


##############################
# internal functions


def _load_testdata_entities() -> dict:
    with (_current_folder / "entities.json").open("r") as f:
        entities = json.load(f)

    # update timestamp to current
    for notification in entities["Notification"]:
        notification["timestamp"] = now() - dt.timedelta(
            hours=randrange(3), minutes=randrange(60), seconds=randrange(60)
        )

    return entities


entities_testdata = _load_testdata_entities()


###################################
# helper functions
#


def load_notification_by_type(
    owner: Owner, notif_type: NotificationType
) -> Notification:
    for notification in entities_testdata["Notification"]:
        if notification["type"] == notif_type.value:
            return NotificationFactory(
                owner=owner,
                notif_type=notif_type.value,
                text=notification.get("text", ""),
            )
    raise ValueError(f"Could not find notif for type: {notif_type}")


def load_notification_entities(owner: Owner, in_bulk=True):
    """Loads notification fixtures for this owner.

    Note that the notification require some EveEntity objects to exit,
    which can be created with ``load_eve_entities()``.

    Args:
    - in_bulk: When disabled, will load notifications one by one (for debugging)
    """
    timestamp_start = now() - dt.timedelta(hours=2)
    objs = [
        _generate_notif_obj_for_owner(owner, timestamp_start, notification)
        for notification in entities_testdata["Notification"]
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


def markdown_to_plain(text: str) -> str:
    """Convert text in markdown to plain text."""
    html = markdown(text)
    text = "".join(BeautifulSoup(html, features="html.parser").findAll(text=True))
    return unicodedata.normalize("NFKD", text)


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


def load_eve_entities():
    """Load eve entity fixtures. Will skip already existing objs."""
    existing_ids = set(EveEntity.objects.values_list("id", flat=True))
    data = {obj["id"]: obj for obj in entities_testdata["EveEntity"]}
    incoming_ids = set(data.keys())
    missing_ids = incoming_ids - existing_ids
    objs = [EveEntity(**data[entity_id]) for entity_id in missing_ids]
    if objs:
        EveEntity.objects.bulk_create(objs)
    logger.info("Loaded %d EveEntity objects", len(objs))
    return objs


def clone_notification(obj: Notification) -> Notification:
    """Return clone of a Notification."""
    new_object = NotificationFactory(
        sender=obj.sender, notif_type=obj.notif_type, owner=obj.owner, text=obj.text
    )
    return new_object


def datetime_to_ldap(my_dt: dt.datetime) -> int:
    """Return a standard datetime as ldap datetime."""
    return (
        ((my_dt - dt.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
        + 11644473600
    ) * 10000000


NearestCelestial = namedtuple(
    "NearestCelestial", ["eve_type", "eve_object", "distance"]
)
