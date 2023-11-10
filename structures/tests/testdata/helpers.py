"""functions for loading test data and for building mocks"""
import datetime as dt
import json
import logging
import math
import unicodedata
from copy import deepcopy
from pathlib import Path
from random import randrange
from typing import Optional, Tuple
from unittest.mock import Mock

from bravado.exception import HTTPNotFound
from bs4 import BeautifulSoup
from markdown import markdown

from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from eveuniverse.models import EveEntity

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from app_utils.esi_testing import BravadoOperationStub, BravadoResponseStub
from app_utils.testing import create_user_from_evecharacter

from structures.core.notification_types import NotificationType
from structures.models import (
    EveSovereigntyMap,
    Notification,
    Owner,
    Structure,
    StructureService,
    StructureTag,
    Webhook,
)

from .factories_2 import NotificationFactory

ESI_CORP_STRUCTURES_PAGE_SIZE = 2

_current_folder = Path(__file__).parent
_FILENAME_EVEUNIVERSE_TESTDATA = "eveuniverse.json"

logger = logging.getLogger(__name__)


def test_data_filename():
    return f"{_current_folder}/{_FILENAME_EVEUNIVERSE_TESTDATA}"


##############################
# internal functions


def _load_esi_data():
    with (_current_folder / "esi_data.json").open("r") as f:
        data = json.load(f)

    return data


def _load_testdata_entities() -> dict:
    with (_current_folder / "entities.json").open("r") as f:
        entities = json.load(f)

    # update timestamp to current
    for notification in entities["Notification"]:
        notification["timestamp"] = now() - dt.timedelta(
            hours=randrange(3), minutes=randrange(60), seconds=randrange(60)
        )

    # update timestamps on structures
    for structure in entities["Structure"]:
        if "fuel_expires_at" in structure:
            fuel_expires_at = now() + dt.timedelta(days=1 + randrange(5))
            structure["fuel_expires_at"] = fuel_expires_at

        if "state_timer_start" in structure:
            state_timer_start = now() + dt.timedelta(days=1 + randrange(3))
            structure["state_timer_start"] = state_timer_start
            state_timer_end = state_timer_start + dt.timedelta(minutes=15)
            structure["state_timer_end"] = state_timer_end

        if "reinforced_until" in structure:
            structure["reinforced_until"] = parse_datetime(
                structure["reinforced_until"]
            )

        if "unanchors_at" in structure:
            unanchors_at = now() + dt.timedelta(days=3 + randrange(5))
            structure["unanchors_at"] = unanchors_at

    return entities


esi_data = _load_esi_data()
esi_corp_structures_data = esi_data["Corporation"][
    "get_corporations_corporation_id_structures"
]
entities_testdata = _load_testdata_entities()


##############################
# functions for mocking calls to ESI with test data

ESI_LANGUAGES = {
    "de",
    "en-us",
    "fr",
    "ja",
    "ru",
    "ko",
    # "zh"
}


def esi_get_universe_planets_planet_id(planet_id, language=None, **kwargs):
    """simulates ESI endpoint of same name for mock test
    will use the respective test data
    unless the function property override_data is set
    """

    entity = None
    for obj in entities_testdata["EvePlanet"]:
        if obj["id"] == planet_id:
            entity = obj.copy()
            break

    if entity is None:
        raise ValueError("entity with id {} not found in testdata".format(planet_id))

    entity["planet_id"] = entity.pop("id")
    entity["system_id"] = entity.pop("eve_solar_system_id")
    entity["type_id"] = entity.pop("eve_type_id")
    entity["position"] = {"x": 1, "y": 2, "z": 3}

    if language in ESI_LANGUAGES.difference({"en-us"}):
        entity["name"] += "_" + language

    return BravadoOperationStub(data=entity)


def esi_get_corporations_corporation_id_structures(
    corporation_id, token, page=None, language=None, **kwargs
):
    """simulates ESI endpoint of same name for mock test
    will use the respective test data
    unless the function property override_data is set
    """
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    page_size = ESI_CORP_STRUCTURES_PAGE_SIZE
    if not page:
        page = 1

    if esi_get_corporations_corporation_id_structures.override_data is None:
        my_corp_structures_data = esi_corp_structures_data
    else:
        if not isinstance(
            esi_get_corporations_corporation_id_structures.override_data, dict
        ):
            raise TypeError("data must be dict")

        my_corp_structures_data = (
            esi_get_corporations_corporation_id_structures.override_data
        )

    if str(corporation_id) in my_corp_structures_data:
        corp_data = deepcopy(my_corp_structures_data[str(corporation_id)])
    else:
        corp_data = list()

    # add pseudo localization
    if language:
        for obj in corp_data:
            if "services" in obj and obj["services"]:
                for service in obj["services"]:
                    if language != "en-us":
                        service["name"] += "_%s" % language

    # convert datetime
    for obj in corp_data:
        for key in obj:
            if isinstance(obj[key], str):
                my_dt = parse_datetime(obj[key])
                if my_dt:
                    obj[key] = my_dt

    start = (page - 1) * page_size
    stop = start + page_size
    pages_count = int(math.ceil(len(corp_data) / page_size))

    return BravadoOperationStub(
        data=corp_data[start:stop], headers={"x-pages": pages_count}
    )


esi_get_corporations_corporation_id_structures.override_data = None


def esi_get_corporations_corporation_id_structures_2(
    corporation_id, token, page=None, language=None, **kwargs
):
    """simulates ESI endpoint of same name for mock test
    will use the respective test data
    unless the function property override_data is set

    VARIANT that simulates django-esi 2.0
    """

    if not isinstance(token, str):
        raise ValueError("token must be a string")

    page_size = ESI_CORP_STRUCTURES_PAGE_SIZE
    if not page:
        page = 1

    if esi_get_corporations_corporation_id_structures.override_data is None:
        my_corp_structures_data = esi_corp_structures_data
    else:
        if not isinstance(
            esi_get_corporations_corporation_id_structures.override_data, dict
        ):
            raise TypeError("data must be dict")

        my_corp_structures_data = (
            esi_get_corporations_corporation_id_structures.override_data
        )

    if str(corporation_id) in my_corp_structures_data:
        corp_data = deepcopy(my_corp_structures_data[str(corporation_id)])
    else:
        corp_data = list()

    # add pseudo localization
    if language:
        for obj in corp_data:
            if "services" in obj and obj["services"]:
                for service in obj["services"]:
                    if language != "en-us":
                        service["name"] += "_%s" % language

    # convert datetime
    for obj in corp_data:
        if "fuel_expires" in obj and obj["fuel_expires"]:
            obj["fuel_expires"] = parse_datetime(obj["fuel_expires"])

    start = (page - 1) * page_size
    stop = start + page_size
    pages_count = int(math.ceil(len(corp_data) / page_size))

    return BravadoOperationStub(
        data=corp_data[start:stop], headers={"x-pages": pages_count}
    )


def esi_get_corporations_corporation_id_starbases(
    corporation_id, token, page=None, **kwargs
):
    """simulates ESI endpoint of same name for mock test
    will use the respective test data
    unless the function property override_data is set
    """
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    page_size = ESI_CORP_STRUCTURES_PAGE_SIZE
    if not page:
        page = 1

    if esi_get_corporations_corporation_id_starbases.override_data is None:
        my_corp_starbases_data = esi_data["Corporation"][
            "get_corporations_corporation_id_starbases"
        ]
    else:
        if not isinstance(
            esi_get_corporations_corporation_id_starbases.override_data, dict
        ):
            raise TypeError("data must be dict")

        my_corp_starbases_data = (
            esi_get_corporations_corporation_id_starbases.override_data
        )

    if str(corporation_id) in my_corp_starbases_data:
        corp_data = deepcopy(my_corp_starbases_data[str(corporation_id)])
    else:
        corp_data = list()

    start = (page - 1) * page_size
    stop = start + page_size
    pages_count = int(math.ceil(len(corp_data) / page_size))
    return BravadoOperationStub(
        data=corp_data[start:stop], headers={"x-pages": pages_count}
    )


esi_get_corporations_corporation_id_starbases.override_data = None


def esi_get_corporations_corporation_id_starbases_starbase_id(
    corporation_id, starbase_id, system_id, token, *args, **kwargs
):
    """simulates ESI endpoint of same name for mock test"""
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    corporation_starbase_details = esi_data["Corporation"][
        "get_corporations_corporation_id_starbases_starbase_id"
    ]  # noqa
    if str(starbase_id) not in corporation_starbase_details:
        mock_response = Mock()
        mock_response.status_code = 404
        message = "Can not find starbase with ID %s" % starbase_id
        raise HTTPNotFound(mock_response, message=message)

    return BravadoOperationStub(
        data=corporation_starbase_details[str(starbase_id)],
        headers={
            "Last-Modified": dt.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        },
    )


def esi_get_universe_structures_structure_id(structure_id, token, *args, **kwargs):
    """simulates ESI endpoint of same name for mock test"""
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    if not esi_get_universe_structures_structure_id.override_data:
        universe_structures_data = esi_data["Universe"][
            "get_universe_structures_structure_id"
        ]
    else:
        universe_structures_data = (
            esi_get_universe_structures_structure_id.override_data
        )

    if str(structure_id) in universe_structures_data:
        return BravadoOperationStub(data=universe_structures_data[str(structure_id)])

    else:
        mock_response = Mock()
        mock_response.status_code = 404
        message = "Can not find structure with ID %s" % structure_id
        raise HTTPNotFound(mock_response, message=message)


esi_get_universe_structures_structure_id.override_data = None


def esi_get_characters_character_id_notifications(character_id, token, *args, **kwargs):
    """simulates ESI endpoint of same name for mock test"""
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    return BravadoOperationStub(data=entities_testdata["Notification"])


def esi_get_corporations_corporation_id_customs_offices(
    corporation_id, token, page=None, **kwargs
):
    """simulates ESI endpoint of same name for mock test
    will use the respective test data
    unless the function property override_data is set
    """
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    page_size = ESI_CORP_STRUCTURES_PAGE_SIZE
    if not page:
        page = 1

    if (
        esi_get_corporations_corporation_id_customs_offices.override_data is None
    ):  # noqa: E501
        my_corp_customs_offices_data = esi_data["Planetary_Interaction"][
            "get_corporations_corporation_id_customs_offices"
        ]

    else:
        if not isinstance(
            esi_get_corporations_corporation_id_customs_offices.override_data, dict
        ):
            raise TypeError("data must be dict")

        my_corp_customs_offices_data = (
            esi_get_corporations_corporation_id_customs_offices.override_data
        )

    if str(corporation_id) in my_corp_customs_offices_data:
        corp_data = deepcopy(my_corp_customs_offices_data[str(corporation_id)])
    else:
        corp_data = list()

    start = (page - 1) * page_size
    stop = start + page_size
    pages_count = int(math.ceil(len(corp_data) / page_size))
    return BravadoOperationStub(
        data=corp_data[start:stop], headers={"x-pages": pages_count}
    )


esi_get_corporations_corporation_id_customs_offices.override_data = None


def esi_get_corporations_corporation_id_assets(
    corporation_id: int, token: str, **kwargs
):
    """simulates ESI endpoint of same name for mock test"""
    try:
        my_esi_data = esi_data["Assets"]["get_corporations_corporation_id_assets"][
            str(corporation_id)
        ]
    except KeyError:
        raise HTTPNotFound(
            response=BravadoResponseStub(
                404, f"No asset data found for {corporation_id} "
            )
        ) from None
    return BravadoOperationStub(data=my_esi_data)


def _esi_post_corporations_corporation_id_assets(
    category: str,
    corporation_id: int,
    item_ids: list,
    my_esi_data: Optional[list] = None,
) -> list:
    """simulates ESI endpoint of same name for mock test"""

    if my_esi_data is None:
        my_esi_data = esi_data["Corporation"][category]

    if str(corporation_id) not in my_esi_data:
        raise RuntimeError(
            "No asset data found for corporation {} in {}".format(
                corporation_id, category
            )
        )
    else:
        return BravadoOperationStub(data=my_esi_data[str(corporation_id)])


def esi_post_corporations_corporation_id_assets_locations(
    corporation_id: int, item_ids: list, token, *args, **kwargs
) -> list:
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    return _esi_post_corporations_corporation_id_assets(
        "post_corporations_corporation_id_assets_locations",
        corporation_id,
        item_ids,
        esi_post_corporations_corporation_id_assets_locations.override_data,
    )


esi_post_corporations_corporation_id_assets_locations.override_data = None


def esi_post_corporations_corporation_id_assets_names(
    corporation_id: int, item_ids: list, token: str, *args, **kwargs
) -> list:
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    return _esi_post_corporations_corporation_id_assets(
        "post_corporations_corporation_id_assets_names",
        corporation_id,
        item_ids,
        esi_post_corporations_corporation_id_assets_names.override_data,
    )


esi_post_corporations_corporation_id_assets_names.override_data = None


def esi_get_universe_categories_category_id(category_id, language=None):
    obj_data = {"id": 65, "name": "Structure"}
    if language in ESI_LANGUAGES.difference({"en-us"}):
        obj_data["name"] += "_" + language

    return BravadoOperationStub(data=obj_data)


def esi_get_universe_moons_moon_id(moon_id, language=None):
    obj_data = {
        "id": 40161465,
        "name": "Amamake II - Moon 1",
        "system_id": 30002537,
        "position": {"x": 1, "y": 2, "z": 3},
    }
    if language in ESI_LANGUAGES.difference({"en-us"}):
        obj_data["name"] += "_" + language

    return BravadoOperationStub(data=obj_data)


def esi_return_data(data):
    return lambda **kwargs: BravadoOperationStub(data=data)


def esi_mock_client(version=1.6):
    """provides a mocked ESI client

    version is the supported version of django-esi
    """
    mock_client = Mock()

    # Assets
    mock_client.Assets.get_corporations_corporation_id_assets = (
        esi_get_corporations_corporation_id_assets
    )
    mock_client.Assets.post_corporations_corporation_id_assets_locations = (
        esi_post_corporations_corporation_id_assets_locations
    )
    mock_client.Assets.post_corporations_corporation_id_assets_names = (
        esi_post_corporations_corporation_id_assets_names
    )
    # Character
    mock_client.Character.get_characters_character_id_notifications.side_effect = (
        esi_get_characters_character_id_notifications
    )
    # Corporation
    mock_client.Corporation.get_corporations_corporation_id_structures.side_effect = (
        esi_get_corporations_corporation_id_structures_2
    )
    # mock_client.Corporation.get_corporations_corporation_id_starbases.side_effect = (
    #     RuntimeError
    # )
    # mock_client.Corporation.get_corporations_corporation_id_starbases_starbase_id.side_effect = (
    #     esi_get_corporations_corporation_id_starbases_starbase_id
    # )
    # Planetary Interaction
    mock_client.Planetary_Interaction.get_corporations_corporation_id_customs_offices = (
        esi_get_corporations_corporation_id_customs_offices
    )
    # Sovereignty
    mock_client.Sovereignty.get_sovereignty_map.side_effect = esi_return_data(
        esi_data["Sovereignty"]["get_sovereignty_map"]
    )
    # Universe
    mock_client.Universe.get_universe_categories_category_id.side_effect = (
        esi_get_universe_categories_category_id
    )

    mock_client.Universe.get_universe_groups_group_id.side_effect = esi_return_data(
        {
            "id": 1657,
            "name": "Citadel",
            "category_id": 65,
        }
    )
    mock_client.Universe.get_universe_types_type_id.side_effect = esi_return_data(
        {
            "id": 35832,
            "name": "Astrahus",
            "group_id": 1657,
        }
    )
    mock_client.Universe.get_universe_regions_region_id.side_effect = esi_return_data(
        {
            "id": 10000005,
            "name": "Detorid",
        }
    )
    mock_client.Universe.get_universe_constellations_constellation_id.side_effect = (
        esi_return_data(
            {
                "id": 20000069,
                "name": "1RG-GU",
                "region_id": 10000005,
            }
        )
    )
    mock_client.Universe.get_universe_systems.side_effect = esi_return_data(
        esi_data["Universe"]["get_universe_systems"]
    )
    mock_client.Universe.get_universe_systems_system_id.side_effect = esi_return_data(
        {
            "id": 30000474,
            "name": "1-PGSG",
            "security_status": -0.496552765369415,
            "constellation_id": 20000069,
            "star_id": 99,
            "planets": [
                {"planet_id": 40029526},
                {"planet_id": 40029528},
                {"planet_id": 40029529},
            ],
        }
    )
    mock_client.Universe.get_universe_planets_planet_id.side_effect = (
        esi_get_universe_planets_planet_id
    )
    mock_client.Universe.get_universe_moons_moon_id.side_effect = (
        esi_get_universe_moons_moon_id
    )
    mock_client.Universe.post_universe_names.side_effect = esi_return_data(
        [{"id": 3011, "category": "alliance", "name": "Big Bad Alliance"}]
    )
    mock_client.Universe.get_universe_structures_structure_id.side_effect = (
        esi_get_universe_structures_structure_id
    )
    return mock_client


###################################
# helper functions
#


def load_entity(EntityClass):
    """loads testdata for given entity class"""
    entity_name = EntityClass.__name__
    for obj in entities_testdata[entity_name]:
        if EntityClass is EveCharacter:
            EveCharacter.objects.create(**obj)

            if "alliance_id" in obj:
                alliance, _ = EveAllianceInfo.objects.get_or_create(
                    alliance_id=obj["alliance_id"],
                    defaults={
                        "alliance_name": obj["alliance_name"],
                        "executor_corp_id": obj["corporation_id"],
                    },
                )
            else:
                alliance = None

            corp_defaults = {
                "corporation_name": obj["corporation_name"],
                "member_count": 99,
                "alliance": alliance,
            }
            EveCorporationInfo.objects.get_or_create(
                corporation_id=obj["corporation_id"], defaults=corp_defaults
            )

            continue

        elif EntityClass is Webhook:
            obj["notification_types"] = NotificationType.values

        EntityClass.objects.create(**obj)

    assert len(entities_testdata[entity_name]) == EntityClass.objects.count()


def load_entities(entities_def: Optional[list] = None):
    """loads testdata for given entities classes"""
    entities_def_master = [
        EveSovereigntyMap,
        EveCharacter,
        EveEntity,
        StructureTag,
        Webhook,
    ]
    for EntityClass in entities_def_master:
        if not entities_def or EntityClass in entities_def:
            load_entity(EntityClass)


def create_structures(dont_load_entities: bool = False) -> object:
    """create structure entities from test data"""
    if not dont_load_entities:
        load_entities()

    create_owners()

    generate_eve_entities_from_auth_entities()

    StructureTag.objects.get(name="tag_a")
    tag_b = StructureTag.objects.get(name="tag_b")
    tag_c = StructureTag.objects.get(name="tag_c")

    for structure in entities_testdata["Structure"]:
        structure_2 = structure.copy()
        structure_2["last_updated_at"] = now()
        structure_2["owner"] = Owner.objects.get(
            corporation__corporation_id=structure_2["owner_corporation_id"]
        )
        del structure_2["owner_corporation_id"]

        if "services" in structure_2:
            del structure_2["services"]

        obj = Structure.objects.create(**structure_2)
        if obj.state != Structure.State.SHIELD_VULNERABLE:
            obj.state_timer_start = now() - dt.timedelta(days=randrange(3) + 1)
            obj.state_timer_end = obj.state_timer_start + dt.timedelta(
                days=randrange(4) + 1
            )

        if obj.id in [1000000000002, 1000000000003]:
            obj.tags.add(tag_c)

        if obj.id in [1000000000003]:
            obj.tags.add(tag_b)

        if "services" in structure:
            objs = [
                StructureService(
                    structure=obj,
                    name=service["name"],
                    state=StructureService.State.from_esi_name(service["state"]),
                )
                for service in structure["services"]
            ]
            StructureService.objects.bulk_create(objs)


def create_owners():
    owners = [
        Owner(corporation=corporation)
        for corporation in EveCorporationInfo.objects.all()
    ]
    owners = Owner.objects.bulk_create(owners)
    default_webhooks = list(Webhook.objects.filter(is_default=True))
    for owner in owners:
        owner.webhooks.add(*default_webhooks)


def create_user(character_id, load_data=False) -> User:
    """create a user from the given character id and returns it

    Needs: EveCharacter
    """
    if load_data:
        load_entity(EveCharacter)

    my_character = EveCharacter.objects.get(character_id=character_id)
    my_user = User.objects.create_user(
        my_character.character_name, "abc@example.com", "password"
    )
    CharacterOwnership.objects.create(
        character=my_character,
        owner_hash="x1" + my_character.character_name,
        user=my_user,
    )
    my_user.profile.main_character = my_character
    return my_user


def set_owner_character(character_id: int) -> Tuple[User, Owner]:
    """Set owner character for the owner related to the given character.
    Creates a new user.
    """
    my_user, character_ownership = create_user_from_evecharacter(
        character_id,
        permissions=["structures.add_structure_owner"],
        scopes=Owner.get_esi_scopes(),
    )
    my_character = my_user.profile.main_character
    my_owner = Owner.objects.get(
        corporation__corporation_id=my_character.corporation_id
    )
    my_owner.characters.create(character_ownership=character_ownership)
    return my_user, my_owner


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


def generate_eve_entities_from_auth_entities():
    """Generate EveEntity objects from existing Auth EveOnline objects."""

    def add_eve_entity(id, name, category):
        if id not in existing_ids:
            objs.append(EveEntity(id=id, category=category, name=name))
            existing_ids.add(id)

    existing_ids = set(EveEntity.objects.values_list("id", flat=True))
    objs = []
    for character in EveCharacter.objects.exclude(character_id__in=existing_ids):
        add_eve_entity(
            id=character.character_id,
            name=character.character_name,
            category=EveEntity.CATEGORY_CHARACTER,
        )
        add_eve_entity(
            id=character.corporation_id,
            name=character.corporation_name,
            category=EveEntity.CATEGORY_CORPORATION,
        )
        if character.alliance_id:
            add_eve_entity(
                id=character.alliance_id,
                name=character.alliance_name,
                category=EveEntity.CATEGORY_ALLIANCE,
            )

    for corporation in EveCorporationInfo.objects.exclude(
        corporation_id__in=existing_ids
    ):
        add_eve_entity(
            id=corporation.corporation_id,
            name=corporation.corporation_name,
            category=EveEntity.CATEGORY_CORPORATION,
        )

    for alliance in EveAllianceInfo.objects.exclude(alliance_id__in=existing_ids):
        add_eve_entity(
            id=alliance.alliance_id,
            name=alliance.alliance_name,
            category=EveEntity.CATEGORY_ALLIANCE,
        )

    EveEntity.objects.bulk_create(objs)


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
