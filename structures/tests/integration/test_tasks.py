import datetime as dt
from unittest.mock import patch

import pook

from django.test import TestCase, override_settings
from django.utils.timezone import now
from eveuniverse.models import EvePlanet, EveSolarSystem
from eveuniverse.tests.testdata.factories_2 import EveMoonFactory, EveTypeFactory

from app_utils.django import app_labels
from app_utils.testing import queryset_pks, reset_celery_once_locks

from structures import tasks
from structures.core.notification_types import NotificationType
from structures.tests.testdata.factories import (
    CitadelTypeFactory,
    CustomsOfficeTypeFactory,
    EveEntityAllianceFactory,
    EveEntityCorporationFactory,
    FuelBlockTypeFactory,
    NotificationFactory,
    OwnerFactory,
    PositionFactory,
    RawNotificationFactory,
    SkyhookTypeFactory,
    StarbaseFactory,
    StarbaseTypeFactory,
    StructureFactory,
    WebhookFactory,
)

if "structuretimers" in app_labels():
    from structuretimers.models import Timer as StructureTimer
else:
    StructureTimer = None

if "timerboard" in app_labels():
    from allianceauth.timerboard.models import Timer as AuthTimer
else:
    AuthTimer = None

MANAGERS_PATH = "structures.managers"
OWNERS_PATH = "structures.models.owners"
NOTIFICATIONS_PATH = "structures.models.notifications"
TASKS_PATH = "structures.tasks"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestTasks(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        reset_celery_once_locks("structures")

    @patch(OWNERS_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", True)
    @patch(OWNERS_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
    @patch(OWNERS_PATH + ".STRUCTURES_FEATURE_SKYHOOKS", True)
    @pook.on
    def test_should_fetch_new_structures_from_esi(self):
        # given
        owner = OwnerFactory()
        corporation_id = owner.corporation.corporation_id
        moon = EveMoonFactory(eve_planet__eve_solar_system__enabled_sections=1)
        planet: EvePlanet = moon.eve_planet
        solar_system: EveSolarSystem = moon.eve_planet.eve_solar_system

        structure_id = 1000000000001
        structure_type = CitadelTypeFactory()

        customs_office_id = 1200000000003
        CustomsOfficeTypeFactory()

        starbase_id = 1300000000001
        fuel_1_type = EveTypeFactory()
        fuel_2_type = EveTypeFactory()
        moon = EveMoonFactory()
        starbase_type = StarbaseTypeFactory()

        skyhook_id = 1000000010001
        skyhook_type = SkyhookTypeFactory()

        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": skyhook_id,
                    "location_flag": "AutoFit",
                    "location_id": planet.eve_solar_system.id,
                    "location_type": "solar_system",
                    "quantity": 1,
                    "type_id": skyhook_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/locations",
            reply=200,
            json=[customs_office_id],
            response_json=[
                {
                    "item_id": customs_office_id,
                    "position": PositionFactory(),
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/locations",
            reply=200,
            json=[starbase_id],
            response_json=[
                {
                    "item_id": starbase_id,
                    "position": PositionFactory(),
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/locations",
            reply=200,
            json=[skyhook_id],
            response_json=[
                {
                    "item_id": skyhook_id,
                    "position": PositionFactory(),
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/names",
            reply=200,
            json=[starbase_id],
            response_json=[
                {"item_id": starbase_id, "name": "Home Sweat Home"},
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/names",
            reply=200,
            json=[customs_office_id],
            response_json=[
                {
                    "item_id": customs_office_id,
                    "name": f"Customs Office ({planet.name})",
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/customs_offices",
            reply=200,
            response_json=[
                {
                    "alliance_tax_rate": 0.02,
                    "allow_access_with_standings": True,
                    "allow_alliance_access": True,
                    "bad_standing_tax_rate": 0.3,
                    "corporation_tax_rate": 0.02,
                    "excellent_standing_tax_rate": 0.02,
                    "good_standing_tax_rate": 0.02,
                    "neutral_standing_tax_rate": 0.02,
                    "office_id": customs_office_id,
                    "reinforce_exit_end": 21,
                    "reinforce_exit_start": 19,
                    "standing_level": "terrible",
                    "system_id": planet.eve_solar_system.id,
                    "terrible_standing_tax_rate": 0.5,
                }
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/starbases",
            reply=200,
            response_json=[
                {
                    "moon_id": moon.id,
                    "starbase_id": starbase_id,
                    "state": "online",
                    "system_id": moon.eve_planet.eve_solar_system.id,
                    "type_id": starbase_type.id,
                }
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/starbases/{starbase_id}",
            reply=200,
            response_json={
                "allow_alliance_members": True,
                "allow_corporation_members": True,
                "anchor": "config_starbase_equipment_role",
                "attack_if_at_war": False,
                "attack_if_other_security_status_dropping": False,
                "fuel_bay_take": "config_starbase_equipment_role",
                "fuel_bay_view": "starbase_fuel_technician_role",
                "fuels": [
                    {
                        "quantity": 960,
                        "type_id": fuel_1_type.id,
                    },
                    {
                        "quantity": 11678,
                        "type_id": fuel_2_type.id,
                    },
                ],
                "offline": "config_starbase_equipment_role",
                "online": "config_starbase_equipment_role",
                "unanchor": "config_starbase_equipment_role",
                "use_alliance_standings": True,
            },
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": corporation_id,
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure_id,
                    "system_id": solar_system.id,
                    "type_id": structure_type.id,
                },
            ],
        )
        pook.get(
            "https://esi.evetech.net/sovereignty/map",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure_id}",
            reply=200,
            response_json={
                "owner_id": corporation_id,
                "name": f"{solar_system.name} - Test Structure Alpha",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": solar_system.id,
                "type_id": structure_type.id,
            },
        )
        pook.get(
            f"https://evesdeapi.kalkoken.net/latest/universe/systems/{solar_system.id}/nearest_celestials",
            reply=200,
            response_json=[
                {
                    "distance": 10,
                    "group_id": 7,
                    "group_name": "Planet",
                    "item_id": planet.id,
                    "name": planet.name,
                    "position": PositionFactory(),
                    "type_id": planet.eve_type.id,
                    "type_name": planet.eve_type.name,
                },
            ],
        )

        # when
        tasks.update_all_structures.delay()

        # then
        got = queryset_pks(owner.structures.all())
        want = {
            customs_office_id,
            skyhook_id,
            starbase_id,
            structure_id,
        }
        self.assertSetEqual(got, want)
        self.assertTrue(pook.isdone(), msg=pook.pending_mocks())

    @patch(OWNERS_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
    @pook.on
    def test_should_send_notification_and_create_timers_for_reinforced_starbase(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.TOWER_REINFORCED_EXTRA]
        )
        owner = OwnerFactory(webhooks=[webhook])
        corporation_id = owner.corporation.corporation_id
        eve_character = owner.characters.first().character_ownership.character

        starbase = StarbaseFactory(owner=owner)
        reinforced_until = now() + dt.timedelta(hours=12)
        fuel_type = FuelBlockTypeFactory()

        discord_mock = pook.post(webhook.url, reply=204)
        pook.get(
            f"https://esi.evetech.net/characters/{eve_character.character_id}/notifications",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets",
            reply=200,
            response_json=[],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/locations",
            reply=200,
            json=[starbase.id],
            response_json=[
                {
                    "item_id": starbase.id,
                    "position": PositionFactory(),
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{corporation_id}/assets/names",
            reply=200,
            json=[starbase.id],
            response_json=[
                {"item_id": starbase.id, "name": starbase.name},
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/customs_offices",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/starbases",
            reply=200,
            response_json=[
                {
                    "moon_id": starbase.eve_moon.id,
                    "starbase_id": starbase.id,
                    "state": "reinforced",
                    "system_id": starbase.eve_moon.eve_planet.eve_solar_system.id,
                    "type_id": starbase.eve_type.id,
                    "reinforced_until": reinforced_until.isoformat(),
                }
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/starbases/{starbase.id}",
            reply=200,
            response_json={
                "allow_alliance_members": True,
                "allow_corporation_members": True,
                "anchor": "config_starbase_equipment_role",
                "attack_if_at_war": False,
                "attack_if_other_security_status_dropping": False,
                "fuel_bay_take": "config_starbase_equipment_role",
                "fuel_bay_view": "starbase_fuel_technician_role",
                "fuels": [
                    {
                        "quantity": 960,
                        "type_id": fuel_type.id,
                    },
                ],
                "offline": "config_starbase_equipment_role",
                "online": "config_starbase_equipment_role",
                "unanchor": "config_starbase_equipment_role",
                "use_alliance_standings": True,
            },
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            "https://esi.evetech.net/sovereignty/map",
            reply=200,
            response_json=[],
        )

        # when
        tasks.update_all_structures.delay()
        tasks.fetch_all_notifications.delay()

        # then
        self.assertEqual(discord_mock.calls, 1)
        self.assertIn(
            starbase.name, discord_mock.matches[0].json["embeds"][0]["description"]
        )

        if StructureTimer:
            self.assertTrue(StructureTimer.objects.exists())

        if AuthTimer:
            self.assertTrue(AuthTimer.objects.exists())

        self.assertTrue(pook.isdone(), msg=pook.pending_mocks())

    @pook.on
    def test_should_fetch_and_send_notification_when_enabled_for_webhook(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE]
        )
        owner = OwnerFactory(webhooks=[webhook], is_alliance_main=True)
        eve_character = owner.characters.first().character_ownership.character
        notif = RawNotificationFactory()

        discord_mock = pook.post(webhook.url, reply=204)
        pook.get(
            f"https://esi.evetech.net/characters/{eve_character.character_id}/notifications",
            reply=200,
            response_json=[notif],
        )

        # when
        tasks.fetch_all_notifications.delay()

        # then
        self.assertEqual(discord_mock.calls, 1)
        self.assertIn(
            "now eligible", discord_mock.matches[0].json["embeds"][0]["description"]
        )

    @pook.on
    def test_should_fetch_and_send_notification_when_enabled_for_webhook_all_anchoring(
        self,
    ):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.SOV_ALL_ANCHORING_MSG]
        )
        owner = OwnerFactory(webhooks=[webhook], is_alliance_main=False)
        eve_character = owner.characters.first().character_ownership.character
        alliance = EveEntityAllianceFactory(
            id=owner.corporation.alliance_id,
            name=owner.corporation.alliance.alliance_name,
        )
        corporation = EveEntityCorporationFactory(
            id=owner.corporation.corporation_id, name=owner.corporation.corporation_name
        )
        starbase = StarbaseFactory(owner=owner)
        notif = RawNotificationFactory(
            type="AllAnchoringMsg",
            sender=corporation,
            data={
                "allianceID": alliance.id,
                "corpID": corporation.id,
                "corpsPresent": [{"allianceID": alliance.id, "corpID": corporation.id}],
                "moonID": starbase.eve_moon.id,
                "solarSystemID": starbase.eve_solar_system.id,
                "towers": [
                    {"moonID": starbase.eve_moon.id, "typeID": starbase.eve_type.id}
                ],
                "typeID": starbase.eve_type.id,
            },
        )

        discord_mock = pook.post(webhook.url, reply=204)
        pook.get(
            f"https://esi.evetech.net/characters/{eve_character.character_id}/notifications",
            reply=200,
            response_json=[notif],
        )

        # when
        tasks.fetch_all_notifications.delay()

        # then
        self.assertEqual(discord_mock.calls, 1)
        self.assertIn(
            "has anchored in", discord_mock.matches[0].json["embeds"][0]["description"]
        )

    @patch(NOTIFICATIONS_PATH + ".STRUCTURES_ADD_TIMERS", True)
    @pook.on
    def test_should_fetch_new_notification_and_send_to_webhook_and_create_timers(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_LOST_SHIELD]
        )
        owner = OwnerFactory(webhooks=[webhook])
        eve_character = owner.characters.first().character_ownership.character
        structure = StructureFactory(owner=owner)

        discord_mock = pook.post(webhook.url, reply=204)
        pook.get(
            f"https://esi.evetech.net/characters/{eve_character.character_id}/notifications",
            reply=200,
            response_json=[
                RawNotificationFactory(
                    type="StructureLostShields",
                    data={
                        "solarsystemID": structure.eve_solar_system.id,
                        "structureID": structure.id,
                        "structureShowInfoData": [
                            "showinfo",
                            structure.eve_type.id,
                            structure.id,
                        ],
                        "structureTypeID": structure.eve_type.id,
                        "timeLeft": 3432362784823,
                        "timestamp": 132977978640000000,
                        "vulnerableTime": 9000000000,
                    },
                ),
            ],
        )

        # when
        tasks.fetch_all_notifications.delay()

        # then
        self.assertEqual(discord_mock.calls, 1)
        self.assertIn(
            structure.name, discord_mock.matches[0].json["embeds"][0]["description"]
        )

        if StructureTimer:
            obj = StructureTimer.objects.first()
            self.assertEqual(obj.eve_solar_system.id, structure.eve_solar_system.id)

        if AuthTimer:
            obj = AuthTimer.objects.first()
            self.assertEqual(obj.system, structure.eve_solar_system.name)

    @patch(NOTIFICATIONS_PATH + ".STRUCTURES_ADD_TIMERS", False)
    @pook.on
    def test_should_send_selected_notif_types_only(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE]
        )
        owner = OwnerFactory(webhooks=[webhook], is_alliance_main=True)
        eve_character = owner.characters.first().character_ownership.character
        NotificationFactory(
            owner=owner, notif_type=NotificationType.WAR_CORPORATION_NO_LONGER_ELIGIBLE
        )
        NotificationFactory(
            owner=owner, notif_type=NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE
        )

        discord_mock = pook.post(webhook.url, reply=204)
        pook.get(
            f"https://esi.evetech.net/characters/{eve_character.character_id}/notifications",
            reply=200,
            response_json=[],
        )

        # when
        tasks.fetch_all_notifications.delay()

        # then
        self.assertEqual(discord_mock.calls, 1)
        self.assertIn(
            "war declarations", discord_mock.matches[0].json["embeds"][0]["title"]
        )


# class TestPlayground(TestCase):
#     def test_playground(self):
#         x = WebhookFactory()
#         print(x.url)


# end
