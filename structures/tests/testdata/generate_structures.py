# flake8: noqa
"""scripts generates large amount of random structures for load testing"""

import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
myauth_dir = (
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    + "/myauth"
)
sys.path.insert(0, myauth_dir)


import django
from django.apps import apps

# init and setup django project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings.local")
django.setup()

if not apps.is_installed("structures"):
    raise RuntimeError("The app structures is not installed")

from datetime import timedelta
from random import randrange

from tqdm import tqdm

from django.utils.timezone import now
from esi.clients import esi_client_factory
from eveuniverse.models import EveMoon, EvePlanet, EveSolarSystem, EveType

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from structures.constants import EveTypeId
from structures.models import Owner, Structure, StructureService, StructureTag
from structures.tests.testdata.factories import (
    JumpGateFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    WebhookFactory,
)

# TODO: Add data for assets, e.g. fittings

print(
    "generate_structure - "
    "scripts generates large amount of random structures for load testing "
)

STRUCTURES_COUNT = 50
POCOS_COUNT = 25
STARBASES_COUNT = 10

# random pick of most active corporations on zKillboard in Jan 2020
corporation_ids = [
    98388312,
    98558506,
    98370861,
    98410772,
    98148549,
    98431483,
    667531913,
    427125032,
    98514543,
    98013740,
]
structure_type_ids = [35825, 35826, 35827, 35832, 35832, 35834, 35835, 35836, 35841]
solar_system_ids = [30000142, 30001445, 30002355, 30004046, 30003833, 30045338]
planet_ids = [
    40477808,
    40393603,
    40423560,
    40024173,
    40189130,
    40133677,
    40161704,
    40045256,
    40026932,
    40147622,
]
moon_ids = [
    40423562,
    40171691,
    40419806,
    40133313,
    40380849,
    40411632,
    40379111,
    40325304,
    40393615,
    40380579,
]
services = [
    "Clone Bay",
    "Moondrilling",
    "Reprocessing",
    "Market Hub",
    "Manufacturing (Standard)",
    "Blueprint Copying",
    "Material Efficiency Research",
    "Time Efficiency Research",
]
tag_names = [
    "Top Secret",
    "Priority",
    "Trash",
    "Needs caretaker",
    "Taskforce Bravo",
    "Not so friendly",
]


def get_random(lst: list) -> object:
    return lst[randrange(len(lst))]


def get_random_subset(lst: list, max_members: int = None) -> list:
    lst2 = lst.copy()
    subset = []
    if not max_members:
        max_members = len(lst)
    else:
        max_members = min(max_members, len(lst))

    for x in range(randrange(max_members) + 1):
        m = lst2.pop(randrange(len(lst2)))
        subset.append(m)

    return subset


print("Connecting to ESI ...")
client = esi_client_factory()

# generating data
webhook = WebhookFactory(name="Generated webhook")
owners = []
for corporation_id in tqdm(corporation_ids, desc="Creating owners"):
    try:
        corporation = client.Corporation.get_corporations_corporation_id(
            corporation_id=corporation_id
        ).result()
        try:
            EveAllianceInfo.objects.get(alliance_id=corporation["alliance_id"])
        except EveAllianceInfo.DoesNotExist:
            EveAllianceInfo.objects.create_alliance(corporation["alliance_id"])
    except Exception:
        pass

    try:
        corporation = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(corporation_id)

    owner, created = Owner.objects.get_or_create(
        corporation=corporation, defaults={"is_active": False}
    )
    if created:
        owner.webhooks.add(webhook)

    owner.assets_last_update_at = now()
    owner.structures_last_update_at = now()
    owner.save()
    owners.append(owner)

# fetching data from ESI
structure_eve_types = [
    EveType.objects.get_or_create_esi(id=type_id)[0] for type_id in structure_type_ids
]
EveType.objects.get_or_create_esi(id=EveTypeId.CUSTOMS_OFFICE)
starbase_eve_type_ids = [
    12235,
    12236,
    16213,
    16214,
    16286,
    20059,
    20060,
    20061,
    20062,
    20063,
    20064,
    20065,
    20066,
]
starbase_eve_types = [
    EveType.objects.get_or_create_esi(id=type_id)[0]
    for type_id in starbase_eve_type_ids
]
eve_solar_systems = [
    EveSolarSystem.objects.get_or_create_esi(id=system_id)[0]
    for system_id in solar_system_ids
]
eve_planets = [
    EvePlanet.objects.get_or_create_esi(id=system_id)[0] for system_id in planet_ids
]
eve_moons = [
    EveMoon.objects.get_or_create_esi(id=system_id)[0] for system_id in moon_ids
]

# generate random tags
tags = []
for name in tag_names:
    tag, _ = StructureTag.objects.update_or_create(
        name=name,
        defaults={"style": get_random([x[0] for x in StructureTag.Style.choices])},
    )
    tags.append(tag)

# remove old structures
Structure.objects.filter(owner__in=owners).delete()

# creating upwell structures
for i in tqdm(range(1, STRUCTURES_COUNT + 1), desc="Creating upwell structures"):
    eve_type = get_random(structure_eve_types)
    eve_solar_system = get_random(eve_solar_systems)
    reinforce_hour = randrange(24)
    owner = get_random(owners)
    state = get_random(
        [
            Structure.State.SHIELD_VULNERABLE,
            Structure.State.SHIELD_VULNERABLE,
            Structure.State.SHIELD_VULNERABLE,
            Structure.State.SHIELD_VULNERABLE,
            Structure.State.SHIELD_VULNERABLE,
            Structure.State.SHIELD_VULNERABLE,
            Structure.State.ARMOR_REINFORCE,
            Structure.State.HULL_REINFORCE,
        ]
    )
    is_low_power = get_random([True, False]) or state == Structure.State.HULL_REINFORCE

    unanchors_at = None

    if not is_low_power:
        fuel_expires_at = now() + timedelta(days=randrange(14), hours=randrange(12))
        last_online_at = now()
        if randrange(1, 10) == 1:
            unanchors_at = now() + timedelta(days=randrange(6), hours=randrange(12))
    else:
        fuel_expires_at = None
        last_online_at = now() - timedelta(days=get_random([1, 2, 3, 10]))

    params = {
        "owner": owner,
        "name": f"Generated structure #{i:05d}",
        "eve_solar_system": eve_solar_system,
        "reinforce_hour": reinforce_hour,
        "state": state,
        "fuel_expires_at": fuel_expires_at,
        "last_online_at": last_online_at,
        "unanchors_at": unanchors_at,
    }
    if eve_type.id == EveTypeId.JUMP_GATE:
        structure = JumpGateFactory(**params)

    else:
        structure = StructureFactory(**{**params, **{"eve_type": eve_type}})
        if is_low_power:
            state = StructureService.State.OFFLINE
        else:
            state = StructureService.State.ONLINE
        for name in get_random_subset(services, 3):
            StructureService.objects.create(structure=structure, name=name, state=state)

    if structure.is_reinforced:
        state_timer_start = now() - timedelta(days=randrange(3), hours=randrange(12))
        state_timer_end = now() + timedelta(days=randrange(3), hours=randrange(12))
        structure.state_timer_start = state_timer_start
        structure.state_timer_end = state_timer_end
        structure.save()

    # common
    structure.tags.add(*get_random_subset(tags))


# creating pocos
for i in tqdm(range(1, POCOS_COUNT + 1), desc="Creating pocos"):
    eve_planet = get_random(eve_planets)
    reinforce_hour = randrange(24)
    owner = get_random(owners)

    structure = PocoFactory(
        owner=owner, eve_planet=eve_planet, reinforce_hour=reinforce_hour
    )

    structure.tags.add(*get_random_subset(tags))

# creating starbases
for i in tqdm(range(1, STARBASES_COUNT + 1), desc="Creating starbases"):
    eve_type = get_random(starbase_eve_types)
    eve_moon = get_random(eve_moons)
    reinforce_hour = randrange(24)
    owner = get_random(owners)
    state = get_random(
        [
            Structure.State.POS_ONLINE,
            Structure.State.POS_ONLINE,
            Structure.State.POS_ONLINE,
            Structure.State.POS_ONLINE,
            Structure.State.POS_ONLINE,
            Structure.State.POS_ONLINE,
            Structure.State.POS_ONLINING,
            Structure.State.POS_OFFLINE,
            Structure.State.POS_REINFORCED,
            Structure.State.POS_UNANCHORING,
        ]
    )

    structure = StarbaseFactory(owner=owner, eve_type=eve_type, eve_moon=eve_moon)

    if structure.is_reinforced:
        state_timer_start = now() - timedelta(days=randrange(3), hours=randrange(12))
        state_timer_end = now() + timedelta(days=randrange(3), hours=randrange(12))
        structure.state_timer_start = state_timer_start
        structure.state_timer_end = state_timer_end
        structure.save()

    # common
    structure.tags.add(*get_random_subset(tags))


print("DONE")
