import datetime as dt
from unittest.mock import patch

import pook
import yaml

from django.test import TestCase, override_settings
from django.utils.timezone import now
from esi.exceptions import HTTPServerError
from esi.models import Token
from eveuniverse.tests.testdata.factories_2 import EveMoonFactory, EvePlanetFactory

from app_utils.testing import NoSocketsTestCase, queryset_pks

from structures.core.notification_types import NotificationType
from structures.models import Notification, Structure, StructureItem
from structures.tests.helpers import datetime_to_ldap
from structures.tests.testdata.factories import (
    CitadelServiceModuleTypeFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveEntityCorporationFactory,
    JumpFuelAlertConfigFactory,
    LiquidOzoneTypeFactory,
    MoonOreTypeFactory,
    OwnerFactory,
    PositionFactory,
    QuantumCoreTypeFactory,
    RefineryFactory,
    SkyhookFactory,
    SkyhookTypeFactory,
    StarbaseFactory,
    StructureFactory,
    StructureItemFactory,
    UserMainDefaultOwnerFactory,
    WebhookFactory,
)
from structures.tests.testdata.helpers import (
    NearestCelestial,
    load_notification_entities,
    load_notification_objects,
)

OWNERS_PATH = "structures.models.owners"
NOTIFICATIONS_PATH = "structures.models.notifications"


class TestFetchNotificationsEsi(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.sender_corporation = EveEntityCorporationFactory()
        cls.character = EveCharacterFactory()
        cls.user = UserMainDefaultOwnerFactory(main_character__character=cls.character)

    @pook.on
    def test_should_create_notifications_from_scratch(self):
        # given
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        notification_id = 1000000916
        recruit = EveCharacterFactory()
        timestamp = now()
        data = {
            "charID": recruit.character_id,
            "corpID": recruit.corporation_id,
        }
        text = yaml.dump(data)
        pook.get(
            f"https://esi.evetech.net/characters/{self.character.character_id}/notifications",
            reply=200,
            response_json=[
                {
                    "notification_id": notification_id,
                    "type": "CharLeftCorpMsg",
                    "sender_id": self.sender_corporation.id,
                    "sender_type": "corporation",
                    "timestamp": timestamp.isoformat(),
                    "text": text,
                    "is_read": True,
                },
            ],
        )

        # when
        owner.fetch_notifications_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_notification_sync_fresh)
        self.assertEqual(owner.notification_set.count(), 1)
        notif: Notification = owner.notification_set.get(
            notification_id=notification_id
        )
        self.assertEqual(notif.notification_id, notification_id)
        self.assertEqual(notif.notif_type, NotificationType.CHAR_LEFT_CORP_MSG)
        self.assertEqual(notif.sender, self.sender_corporation)
        self.assertEqual(notif.timestamp, timestamp)
        self.assertEqual(notif.text, text)
        self.assertTrue(notif.is_read)
        self.assertFalse(notif.is_sent)
        self.assertEqual(notif.parsed_text(), data)

    @pook.on
    def test_should_handle_other_sender_correctly(self):
        # given
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        notification_id = 1000000916
        pook.get(
            f"https://esi.evetech.net/characters/{self.character.character_id}/notifications",
            reply=200,
            response_json=[
                {
                    "notification_id": notification_id,
                    "type": "CorpBecameWarEligible",
                    "sender_id": 42,
                    "sender_type": "other",
                    "timestamp": now().isoformat(),
                    "text": "",
                },
            ],
        )

        # when
        owner.fetch_notifications_esi()

        # then
        obj = owner.notification_set.get(notification_id=notification_id)
        self.assertIsNone(obj.sender)

    @patch(OWNERS_PATH + ".notify", spec=True)
    @pook.on
    def test_should_inform_user_about_successful_update(self, mock_notify):
        # given
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        notification_id = 1000000916
        pook.get(
            f"https://esi.evetech.net/characters/{self.character.character_id}/notifications",
            reply=200,
            response_json=[
                {
                    "notification_id": notification_id,
                    "type": "CorpBecameWarEligible",
                    "sender_id": self.sender_corporation.id,
                    "sender_type": "corporation",
                    "timestamp": now().isoformat(),
                    "text": "",
                },
            ],
        )

        # when
        owner.fetch_notifications_esi(self.user)

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_notification_sync_fresh)
        self.assertTrue(mock_notify.called)

    @pook.on
    def test_should_set_moon_for_structure_when_missing(self):
        # given
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        notification_id = 1000000404
        ore_1 = MoonOreTypeFactory()
        ore_2 = MoonOreTypeFactory()
        ore_3 = MoonOreTypeFactory()
        refinery = RefineryFactory(owner=owner, eve_moon=None)
        moon = EveMoonFactory(eve_planet__eve_solar_system=refinery.eve_solar_system)
        timestamp = now()
        ready_time = timestamp + dt.timedelta(days=3)
        data = {
            "autoTime": datetime_to_ldap(ready_time + dt.timedelta(hours=2)),
            "moonID": moon.id,
            "oreVolumeByType": {
                ore_1.id: 1288475.124715103,
                ore_2.id: 544691.7637724016,
                ore_3.id: 526825.4047522942,
            },
            "readyTime": datetime_to_ldap(ready_time),
            "solarSystemID": refinery.eve_solar_system.id,
            "startedBy": self.character.character_id,
            "startedByLink": (
                f'<a href="showinfo:1383//{self.character.character_id}">'
                f"{self.character.character_name}</a>"
            ),
            "structureID": refinery.id,
            "structureLink": (
                f'<a href="showinfo:{refinery.eve_type.id}//{refinery.id}">'
                f"{refinery.name}</a>"
            ),
            "structureName": "Dummy",
            "structureTypeID": refinery.eve_type.id,
        }
        pook.get(
            f"https://esi.evetech.net/characters/{self.character.character_id}/notifications",
            reply=200,
            response_json=[
                {
                    "notification_id": notification_id,
                    "type": "MoonminingExtractionStarted",
                    "sender_id": self.sender_corporation.id,
                    "sender_type": "corporation",
                    "timestamp": timestamp.isoformat(),
                    "text": yaml.dump(data),
                },
            ],
        )

        # when
        owner.fetch_notifications_esi()

        # then
        refinery.refresh_from_db()
        self.assertEqual(refinery.eve_moon_id, moon.id)

    @pook.on
    def test_should_bubble_up_http_error_during_sync(self):
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        pook.get(
            f"https://esi.evetech.net/characters/{self.character.character_id}/notifications",
            reply=502,
            response_json={"error": "some error"},
        )
        # when
        with self.assertRaises(HTTPServerError):
            owner.fetch_notifications_esi()

        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_notification_sync_fresh)


@override_settings(DEBUG=True)
@patch(NOTIFICATIONS_PATH + ".STRUCTURES_REPORT_NPC_ATTACKS", True)
@patch(NOTIFICATIONS_PATH + ".Webhook.send_message", spec=True)
class TestSendNewNotifications(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory(
            is_alliance_main=True, webhooks=False, forwarding_last_update_at=None
        )
        load_notification_entities(cls.owner)
        load_notification_objects(cls.owner)

    def setUp(self) -> None:
        self.owner.webhooks.clear()

    # TODO: Temporarily disabled
    # @patch(
    #     NOTIFICATIONS_PATH + ".STRUCTURES_NOTIFICATION_DISABLE_ESI_FUEL_ALERTS", False
    # )
    def test_should_send_all_notifications(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(notification_types=NotificationType.values)
        self.owner.webhooks.add(webhook)

        # when
        self.owner.send_new_notifications()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_forwarding_sync_fresh)
        notifications_processed = {
            int(args[1]["embeds"][0].footer.text[-10:])
            for args in mock_send_message.call_args_list
        }
        notifications_expected = set(
            self.owner.notification_set.filter(
                notif_type__in=NotificationType.values
            ).values_list("notification_id", flat=True)
        )
        self.assertSetEqual(notifications_processed, notifications_expected)

    # TODO: temporary disabled
    # @patch(
    #     NOTIFICATIONS_PATH + ".STRUCTURES_NOTIFICATION_DISABLE_ESI_FUEL_ALERTS", True
    # )
    # def test_should_send_all_notifications_except_fuel_alerts(self, mock_send_message):
    #     # given
    #     mock_send_message.return_value = True
    #     self.user = AuthUtils.add_permission_to_user_by_name(
    #         "structures.add_structure_owner", self.user
    #     )
    #     # when
    #     self.self.owner.send_new_notifications()
    #     # then
    #     self.self.owner.refresh_from_db()
    #     self.assertTrue(self.self.owner.is_forwarding_sync_fresh)
    #     notifications_processed = {
    #         int(args[1]["embeds"][0].footer.text[-10:])
    #         for args in mock_send_message.call_args_list
    #     }
    #     notif_types = set(NotificationType.values)
    #     notif_types.discard(NotificationType.STRUCTURE_FUEL_ALERT)
    #     notif_types.discard(NotificationType.TOWER_RESOURCE_ALERT_MSG)
    #     notifications_expected = set(
    #         self.self.owner.notifications.filter(notif_type__in=notif_types).values_list(
    #             "notification_id", flat=True
    #         )
    #     )
    #     self.assertSetEqual(notifications_processed, notifications_expected)

    def test_should_send_all_notifications_corp(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        corporation = EveCorporationInfoFactory(corporation_id=2011)
        character = EveCharacterFactory(corporation=corporation)
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        owner = OwnerFactory(
            user=user,
            is_alliance_main=True,
            webhooks__notification_types=NotificationType.values,
            forwarding_last_update_at=None,
        )
        load_notification_entities(owner)
        load_notification_objects(owner)

        # when
        owner.send_new_notifications()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_forwarding_sync_fresh)
        notifications_processed = {
            int(args[1]["embeds"][0].footer.text[-10:])
            for args in mock_send_message.call_args_list
        }
        notifications_expected = set(
            owner.notification_set.filter(
                notif_type__in=NotificationType.values
            ).values_list("notification_id", flat=True)
        )
        self.assertSetEqual(notifications_processed, notifications_expected)

    def test_should_only_send_selected_notification_types(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        selected_notif_types = [
            NotificationType.ORBITAL_ATTACKED,
            NotificationType.STRUCTURE_DESTROYED,
        ]
        webhook = WebhookFactory(notification_types=selected_notif_types)
        self.owner.webhooks.add(webhook)

        # when
        self.owner.send_new_notifications()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_forwarding_sync_fresh)
        notifications_processed = {
            int(args[1]["embeds"][0].footer.text[-10:])
            for args in mock_send_message.call_args_list
        }
        notifications_expected = set(
            Notification.objects.filter(
                notif_type__in=selected_notif_types
            ).values_list("notification_id", flat=True)
        )
        self.assertSetEqual(notifications_processed, notifications_expected)


class TestOwnerUpdateAssetEsi(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.character = EveCharacterFactory()
        cls.user = UserMainDefaultOwnerFactory(main_character__character=cls.character)
        cls.owner = OwnerFactory(user=cls.user, assets_last_update_at=None)

    @pook.on
    def test_should_fetch_new_assets(self):
        # given
        structure = StructureFactory(owner=self.owner, quantum_core=False)
        service_module_type = CitadelServiceModuleTypeFactory()
        item_id = 1300000001001
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": item_id,
                    "location_flag": "ServiceSlot0",
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1,
                    "type_id": service_module_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_assets_sync_fresh)
        obj = structure.items.get(pk=item_id)
        self.assertEqual(obj.eve_type_id, service_module_type.id)
        self.assertEqual(obj.location_flag, "ServiceSlot0")
        self.assertEqual(obj.quantity, 1)
        self.assertTrue(obj.is_singleton)

    @pook.on
    def test_should_updating_existing_assets(self):
        # given

        structure = StructureFactory(owner=self.owner, quantum_core=False)
        item = StructureItemFactory(structure=structure, is_singleton=False, quantity=3)
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": item.is_singleton,
                    "item_id": item.id,
                    "location_flag": item.location_flag,
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 5,
                    "type_id": item.eve_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_assets_sync_fresh)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    @pook.on
    def test_should_update_quantum_core(self):
        # given

        structure = StructureFactory(owner=self.owner, quantum_core=False)
        quantum_core_type = QuantumCoreTypeFactory()
        service_module_type = CitadelServiceModuleTypeFactory()
        item_1_id = 1300000001001
        item_2_id = 1300000002001
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": False,
                    "item_id": item_1_id,
                    "location_flag": "QuantumCoreRoom",
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1,
                    "type_id": quantum_core_type.id,
                },
                {
                    "is_singleton": True,
                    "item_id": item_2_id,
                    "location_flag": "ServiceSlot0",
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1,
                    "type_id": service_module_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_assets_sync_fresh)
        obj = structure.items.get(pk=item_1_id)
        self.assertEqual(obj.eve_type_id, quantum_core_type.id)
        self.assertEqual(
            obj.location_flag, StructureItem.LocationFlag.QUANTUM_CORE_ROOM
        )
        self.assertEqual(obj.quantity, 1)
        self.assertFalse(obj.is_singleton)

        obj = structure.items.get(pk=item_2_id)
        self.assertEqual(obj.eve_type_id, service_module_type.id)
        self.assertEqual(obj.location_flag, "ServiceSlot0")
        self.assertEqual(obj.quantity, 1)
        self.assertTrue(obj.is_singleton)

        structure.refresh_from_db()
        self.assertTrue(structure.has_fitting)
        self.assertTrue(structure.has_core)

    @patch(OWNERS_PATH + ".notify", spec=True)
    @pook.on
    def test_should_inform_user_about_successful_update(self, mock_notify):
        # given

        structure = StructureFactory(owner=self.owner, quantum_core=False)
        service_module_type = CitadelServiceModuleTypeFactory()
        item_2_id = 1300000002001
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": item_2_id,
                    "location_flag": "ServiceSlot0",
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1,
                    "type_id": service_module_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi(user=self.user)

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_assets_sync_fresh)
        self.assertTrue(mock_notify.called)

    @pook.on
    def test_should_add_item_when_location_not_found(self):
        # given

        structure = StructureFactory(owner=self.owner, quantum_core=False)
        service_module_type = CitadelServiceModuleTypeFactory()
        item_id = 1300000001001
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": item_id,
                    "location_flag": "ServiceSlot0",
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1,
                    "type_id": service_module_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=404,
            response_json={"error": "not found"},
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_assets_sync_fresh)
        obj = structure.items.get(pk=item_id)
        self.assertEqual(obj.eve_type_id, service_module_type.id)
        self.assertEqual(obj.location_flag, "ServiceSlot0")
        self.assertEqual(obj.quantity, 1)
        self.assertTrue(obj.is_singleton)

    @pook.on
    def test_should_raise_exception_when_esi_returns_http_error(self):
        # given

        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=500,
            response_json={"error": "some error"},
        )

        # when
        with self.assertRaises(HTTPServerError):
            self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_assets_sync_fresh)

    @pook.on
    def test_should_remove_assets_that_no_longer_exist_for_existing_structure(self):
        # given

        structure = StructureFactory(owner=self.owner, quantum_core=False)
        service_module_type = CitadelServiceModuleTypeFactory()
        added_item_id = 1300000002001
        StructureItemFactory(structure=structure)  # should be removed
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": added_item_id,
                    "location_flag": "ServiceSlot0",
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1,
                    "type_id": service_module_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi()

        # then
        got = set(structure.items.values_list("id", flat=True))
        self.assertSetEqual(got, {added_item_id})

    @pook.on
    def test_should_handle_asset_moved_to_another_structure(self):
        # given

        structure_1 = StructureFactory(owner=self.owner, quantum_core=False)
        structure_2 = StructureFactory(owner=self.owner, quantum_core=False)
        item = StructureItemFactory(structure=structure_2)
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": item.id,
                    "location_flag": item.location_flag,
                    "location_id": structure_1.id,
                    "location_type": "item",
                    "quantity": item.quantity,
                    "type_id": item.eve_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.assertSetEqual(queryset_pks(structure_2.items.all()), set())
        self.assertSetEqual(queryset_pks(structure_1.items.all()), {item.id})

    @pook.on
    def test_should_remove_outdated_jump_fuel_alerts(self):
        # given

        structure = StructureFactory(owner=self.owner)
        config = JumpFuelAlertConfigFactory(threshold=100)
        structure.jump_fuel_alerts.create(structure=structure, config=config)

        fuel_type = LiquidOzoneTypeFactory()
        item_id = 1000000000004
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": False,
                    "item_id": item_id,
                    "location_flag": StructureItem.LocationFlag.STRUCTURE_FUEL,
                    "location_id": structure.id,
                    "location_type": "item",
                    "quantity": 1000,
                    "type_id": fuel_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[],
        )

        # when
        self.owner.update_asset_esi()
        # then
        self.assertEqual(structure.jump_fuel_alerts.count(), 0)

    # TODO: Add tests for error cases

    @pook.on
    def test_should_update_starbase_items(self):
        # given

        starbase = StarbaseFactory(owner=self.owner)  # position needs to match assets
        item_id = 1000000000004
        item_type = LiquidOzoneTypeFactory()
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": False,
                    "item_id": item_id,
                    "location_flag": StructureItem.LocationFlag.AUTOFIT,
                    "location_id": starbase.eve_solar_system.id,
                    "location_type": "solar_system",
                    "quantity": 3,
                    "type_id": item_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": item_id,
                    "position": {
                        "x": starbase.position_x,
                        "y": starbase.position_y,
                        "z": starbase.position_z,
                    },
                },
            ],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_assets_sync_fresh)
        self.assertSetEqual(queryset_pks(starbase.items.all()), {item_id})


@patch(OWNERS_PATH + ".STRUCTURES_FEATURE_SKYHOOKS", True)
@patch(OWNERS_PATH + ".EveSolarSystem.nearest_celestial")
class TestOwnerUpdateSkyhooks(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.character = EveCharacterFactory()
        cls.user = UserMainDefaultOwnerFactory(main_character__character=cls.character)
        cls.owner = OwnerFactory(user=cls.user, assets_last_update_at=None)
        cls.planet = EvePlanetFactory()

    @pook.on
    def test_should_create_new_skyhooks_from_scratch(self, mock_nearest_celestial):
        # given
        mock_nearest_celestial.return_value = NearestCelestial(
            eve_object=self.planet, distance=35_000_000, eve_type=self.planet.eve_type
        )
        skyhook_id = 1000000010001
        skyhook_type = SkyhookTypeFactory()
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": skyhook_id,
                    "location_flag": "AutoFit",
                    "location_id": self.planet.eve_solar_system.id,
                    "location_type": "solar_system",
                    "quantity": 1,
                    "type_id": skyhook_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": skyhook_id,
                    "position": PositionFactory(),
                },
            ],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.structures.count(), 1)
        structure: Structure = self.owner.structures.get(pk=1000000010001)
        self.assertTrue(structure.is_skyhook)
        self.assertEqual(structure.eve_planet, self.planet)

    @pook.on
    def test_should_remove_obsolete_skyhooks(self, mock_nearest_celestial):
        # given
        mock_nearest_celestial.return_value = NearestCelestial(
            eve_object=self.planet, distance=35_000_000, eve_type=self.planet.eve_type
        )

        SkyhookFactory(owner=self.owner)  # should be removed
        skyhook = SkyhookFactory(owner=self.owner)  # should not be removed
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": skyhook.id,
                    "location_flag": StructureItem.LocationFlag.AUTOFIT,
                    "location_id": skyhook.eve_solar_system.id,
                    "location_type": "solar_system",
                    "quantity": 1,
                    "type_id": skyhook.eve_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": skyhook.id,
                    "position": PositionFactory(),
                },
            ],
        )

        # when
        self.owner.update_asset_esi()

        # then
        self.owner.refresh_from_db()
        self.assertEqual(queryset_pks(self.owner.structures.all()), {skyhook.id})

    @pook.on
    def test_should_handle_expected_errors_when_resolving_planet(
        self, mock_nearest_celestial
    ):
        # given
        mock_nearest_celestial.side_effect = ValueError

        skyhook_id = 1000000010001
        skyhook_type = SkyhookTypeFactory()
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": skyhook_id,
                    "location_flag": StructureItem.LocationFlag.AUTOFIT,
                    "location_id": self.planet.eve_solar_system.id,
                    "location_type": "solar_system",
                    "quantity": 1,
                    "type_id": skyhook_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": skyhook_id,
                    "position": PositionFactory(),
                },
            ],
        )
        # when
        self.owner.update_asset_esi()

        # then
        structure: Structure = self.owner.structures.first()
        self.assertEqual(structure.id, skyhook_id)
        self.assertTrue(structure.is_skyhook)
        self.assertIsNone(structure.eve_planet)

    @pook.on
    def test_should_ignore_no_reply_when_resolving_planet(self, mock_nearest_celestial):
        # given
        mock_nearest_celestial.return_value = None

        skyhook_id = 1000000010001
        skyhook_type = SkyhookTypeFactory()
        pook.get(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets",
            reply=200,
            response_json=[
                {
                    "is_singleton": True,
                    "item_id": skyhook_id,
                    "location_flag": StructureItem.LocationFlag.AUTOFIT,
                    "location_id": self.planet.eve_solar_system.id,
                    "location_type": "solar_system",
                    "quantity": 1,
                    "type_id": skyhook_type.id,
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.character.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": skyhook_id,
                    "position": PositionFactory(),
                },
            ],
        )
        # when
        self.owner.update_asset_esi()

        # then
        structure: Structure = self.owner.structures.first()
        self.assertEqual(structure.id, skyhook_id)
        self.assertTrue(structure.is_skyhook)
        self.assertIsNone(structure.eve_planet)


class TestOwnerToken(TestCase):
    def test_should_return_valid_token(self):
        # given
        character = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        owner = OwnerFactory(user=user, characters=[character])
        # when
        token = owner.characters.first().valid_token()
        # then
        self.assertIsInstance(token, Token)
        self.assertEqual(token.user, user)
        self.assertEqual(token.character_id, character.character_id)

    def test_should_return_none_if_no_valid_token_found(self):
        # given
        character = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        owner = OwnerFactory(user=user, characters=[character])
        user.token_set.first().scopes.clear()
        # when
        token = owner.characters.first().valid_token()
        # then
        self.assertIsNone(token)


@patch(OWNERS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", True)
@patch(OWNERS_PATH + ".notify_admins")
class TestOwnerUpdateIsUp(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.corporation = EveCorporationInfoFactory()

    @patch(OWNERS_PATH + ".Owner.are_all_syncs_ok", True)
    def test_should_do_nothing_when_still_up(self, mock_notify_admins):
        # given
        owner = OwnerFactory(
            corporation=self.corporation, is_up=True, is_alliance_main=True
        )
        # when
        result = owner.update_is_up()
        # then
        self.assertTrue(result)
        self.assertFalse(mock_notify_admins.called)
        owner.refresh_from_db()
        self.assertTrue(owner.is_up)

    @patch(OWNERS_PATH + ".Owner.are_all_syncs_ok", False)
    def test_should_report_when_down(self, mock_notify_admins):
        # given
        owner = OwnerFactory(
            corporation=self.corporation, is_up=True, is_alliance_main=True
        )
        # when
        result = owner.update_is_up()
        # then
        self.assertFalse(result)
        self.assertTrue(mock_notify_admins.called)
        owner.refresh_from_db()
        self.assertFalse(owner.is_up)

    @patch(OWNERS_PATH + ".Owner.are_all_syncs_ok", False)
    def test_should_not_report_again_when_still_down(self, mock_notify_admins):
        # given
        owner = OwnerFactory(
            corporation=self.corporation, is_up=False, is_alliance_main=True
        )
        # when
        result = owner.update_is_up()
        # then
        self.assertFalse(result)
        self.assertFalse(mock_notify_admins.called)
        owner.refresh_from_db()
        self.assertFalse(owner.is_up)

    @patch(OWNERS_PATH + ".Owner.are_all_syncs_ok", True)
    def test_should_report_when_up_again(self, mock_notify_admins):
        # given
        owner = OwnerFactory(
            corporation=self.corporation, is_up=False, is_alliance_main=True
        )
        # when
        result = owner.update_is_up()
        # then
        self.assertTrue(result)
        self.assertTrue(mock_notify_admins.called)
        owner.refresh_from_db()
        self.assertTrue(owner.is_up)

    @patch(OWNERS_PATH + ".Owner.are_all_syncs_ok", True)
    def test_should_report_when_up_for_the_first_time(self, mock_notify_admins):
        # given
        owner = OwnerFactory(
            corporation=self.corporation, is_up=None, is_alliance_main=True
        )
        # when
        result = owner.update_is_up()
        # then
        self.assertTrue(result)
        self.assertTrue(mock_notify_admins.called)
        owner.refresh_from_db()
        self.assertTrue(owner.is_up)
