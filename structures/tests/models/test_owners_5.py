import datetime as dt
from unittest.mock import patch

from bravado.exception import HTTPBadGateway, HTTPInternalServerError
from pytz import utc

from django.test import override_settings
from django.utils.timezone import now
from esi.models import Token
from eveuniverse.models import EvePlanet

from app_utils.esi_testing import EsiClientStub, EsiEndpoint
from app_utils.testing import BravadoResponseStub, NoSocketsTestCase, queryset_pks

from structures.core.notification_types import NotificationType
from structures.models import Notification, Structure, StructureItem
from structures.tests.testdata.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveEntityCorporationFactory,
    JumpFuelAlertConfigFactory,
    OwnerFactory,
    SkyhookFactory,
    StarbaseFactory,
    StructureFactory,
    StructureItemFactory,
    UserMainDefaultOwnerFactory,
    WebhookFactory,
    datetime_to_esi,
)
from structures.tests.testdata.helpers import (
    NearestCelestial,
    load_eve_entities,
    load_notification_entities,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

OWNERS_PATH = "structures.models.owners"
NOTIFICATIONS_PATH = "structures.models.notifications"


@patch(OWNERS_PATH + ".esi")
class TestFetchNotificationsEsi(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.sender_corporation = EveEntityCorporationFactory()
        cls.character = EveCharacterFactory()
        cls.user = UserMainDefaultOwnerFactory(main_character__character=cls.character)
        endpoints = [
            EsiEndpoint(
                "Character",
                "get_characters_character_id_notifications",
                "character_id",
                needs_token=True,
                data={
                    f"{cls.character.character_id}": [
                        {
                            "notification_id": 1000000505,
                            "type": "StructureLostShields",
                            "sender_id": cls.sender_corporation.id,
                            "sender_type": "corporation",
                            "timestamp": "2019-10-04 14:52:00",
                            "text": "solarsystemID: 30002537\nstructureID: &id001 1000000000001\nstructureShowInfoData:\n- showinfo\n- 35832\n- *id001\nstructureTypeID: 35832\ntimeLeft: 1727805401093\ntimestamp: 132148470780000000\nvulnerableTime: 9000000000\n",
                        },
                    ]
                },
            )
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(endpoints)

    @patch(OWNERS_PATH + ".notify", spec=True)
    @patch(OWNERS_PATH + ".now", spec=True)
    def test_should_inform_user_about_successful_update(
        self, mock_now, mock_notify, mock_esi
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_now.return_value = dt.datetime(2019, 8, 16, 14, 15, tzinfo=utc)
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        StructureFactory(owner=owner, id=1000000000001)
        # when
        owner.fetch_notifications_esi(self.user)
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_notification_sync_fresh)
        self.assertTrue(mock_notify.called)

    def test_should_create_notifications(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        StructureFactory(owner=owner, id=1000000000001)
        # when
        owner.fetch_notifications_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_notification_sync_fresh)
        # should only contain the right notifications
        notif_ids_current = set(
            Notification.objects.values_list("notification_id", flat=True)
        )
        self.assertSetEqual(notif_ids_current, {1000000505})

    @patch(OWNERS_PATH + ".now")
    def test_should_set_moon_for_structure_if_missing(self, mock_now, mock_esi_client):
        # given
        character = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        endpoints = [
            EsiEndpoint(
                "Character",
                "get_characters_character_id_notifications",
                "character_id",
                needs_token=True,
                data={
                    f"{character.character_id}": [
                        {
                            "notification_id": 1000000404,
                            "type": "MoonminingExtractionStarted",
                            "sender_id": self.sender_corporation.id,
                            "sender_type": "corporation",
                            "timestamp": "2019-11-13 23:33:00",
                            "text": 'autoTime: 132186924601059151\nmoonID: 40161465\noreVolumeByType:\n  46300: 1288475.124715103\n  46301: 544691.7637724016\n  46302: 526825.4047522942\n  46303: 528996.6386983792\nreadyTime: 132186816601059151\nsolarSystemID: 30002537\nstartedBy: 1001\nstartedByLink: <a href="showinfo:1383//1001">Bruce Wayne</a>\nstructureID: 1000000000002\nstructureLink: <a href="showinfo:35835//1000000000002">Dummy</a>\nstructureName: Dummy\nstructureTypeID: 35835\n',
                            "is_read": False,
                        },
                    ]
                },
            )
        ]
        mock_esi_client.client = EsiClientStub.create_from_endpoints(endpoints)
        mock_now.return_value = dt.datetime(2019, 11, 13, 23, 50, 0, tzinfo=utc)
        owner = OwnerFactory(
            user=user, notifications_last_update_at=None, characters=[character]
        )
        structure = StructureFactory(owner=owner, id=1000000000002, eve_type_id=35835)
        # when
        owner.fetch_notifications_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_notification_sync_fresh)
        structure.refresh_from_db()
        self.assertEqual(structure.eve_moon_id, 40161465)

    def test_report_error_when_esi_returns_error_during_sync(self, mock_esi):
        def my_callback(*args, **kwargs):
            raise HTTPBadGateway(
                BravadoResponseStub(status_code=502, reason="Test Exception")
            )

        # given
        endpoints = [
            EsiEndpoint(
                "Character",
                "get_characters_character_id_notifications",
                "character_id",
                needs_token=True,
                data=[],
                side_effect=my_callback,
            )
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        owner = OwnerFactory(
            user=self.user,
            notifications_last_update_at=None,
            characters=[self.character],
        )
        StructureFactory(owner=owner, id=1000000000001)
        # when
        with self.assertRaises(HTTPBadGateway):
            owner.fetch_notifications_esi()
        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_notification_sync_fresh)

    def test_should_create_notifications_from_scratch(self, mock_esi):
        # given
        owner = OwnerFactory(notifications_last_update_at=None)
        sender = EveEntityCorporationFactory()
        eve_character = owner.characters.first().character_ownership.character
        endpoints = [
            EsiEndpoint(
                "Character",
                "get_characters_character_id_notifications",
                "character_id",
                needs_token=True,
                data={
                    str(eve_character.character_id): [
                        {
                            "notification_id": 42,
                            "is_read": False,
                            "sender_id": sender.id,
                            "sender_type": "corporation",
                            "text": "{}\n",
                            "timestamp": datetime_to_esi(now()),
                            "type": "CorpBecameWarEligible",
                        }
                    ]
                },
            )
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        # when
        owner.fetch_notifications_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_notification_sync_fresh)
        self.assertEqual(owner.notification_set.count(), 1)
        obj = owner.notification_set.first()
        self.assertEqual(
            obj.notif_type, NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE
        )

    def test_should_handle_other_sender_correctly(self, mock_esi):
        # given
        owner = OwnerFactory(notifications_last_update_at=None)
        eve_character = owner.characters.first().character_ownership.character
        endpoints = [
            EsiEndpoint(
                "Character",
                "get_characters_character_id_notifications",
                "character_id",
                needs_token=True,
                data={
                    str(eve_character.character_id): [
                        {
                            "notification_id": 42,
                            "is_read": False,
                            "sender_id": 1,
                            "sender_type": "other",
                            "text": "{}\n",
                            "timestamp": datetime_to_esi(now()),
                            "type": "CorpBecameWarEligible",
                        }
                    ]
                },
            )
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        # when
        owner.fetch_notifications_esi()
        # then
        obj = owner.notification_set.get(notification_id=42)
        self.assertIsNone(obj.sender)


@override_settings(DEBUG=True)
@patch(NOTIFICATIONS_PATH + ".STRUCTURES_REPORT_NPC_ATTACKS", True)
@patch(NOTIFICATIONS_PATH + ".Webhook.send_message", spec=True)
class TestSendNewNotifications(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        cls.owner = OwnerFactory(
            is_alliance_main=True, webhooks=False, forwarding_last_update_at=None
        )
        load_notification_entities(cls.owner)

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


@patch(OWNERS_PATH + ".esi")
class TestOwnerUpdateAssetEsi(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.corporation = EveCharacterFactory()
        character = EveCharacterFactory(corporation=cls.corporation)
        cls.user = UserMainDefaultOwnerFactory(main_character__character=character)

        endpoints = [
            EsiEndpoint(
                "Assets",
                "get_corporations_corporation_id_assets",
                "corporation_id",
                needs_token=True,
                data={
                    f"{cls.corporation.corporation_id}": [
                        {
                            "is_singleton": False,
                            "item_id": 1300000001001,
                            "location_flag": "QuantumCoreRoom",
                            "location_id": 1000000000001,
                            "location_type": "item",
                            "quantity": 1,
                            "type_id": 56201,
                        },
                        {
                            "is_singleton": True,
                            "item_id": 1300000001002,
                            "location_flag": "ServiceSlot0",
                            "location_id": 1000000000001,
                            "location_type": "item",
                            "quantity": 1,
                            "type_id": 35894,
                        },
                        {
                            "is_singleton": True,
                            "item_id": 1300000002001,
                            "location_flag": "ServiceSlot0",
                            "location_id": 1000000000002,
                            "location_type": "item",
                            "quantity": 1,
                            "type_id": 35894,
                        },
                        {
                            "is_singleton": True,
                            "item_id": 1500000000001,
                            "location_flag": "AutoFit",
                            "location_id": 30002537,  # Amamake,
                            "location_type": "solar_system",
                            "quantity": 1,
                            "type_id": 16213,  # control tower
                        },
                        {
                            "is_singleton": True,
                            "item_id": 1500000000002,
                            "location_flag": "AutoFit",
                            "location_id": 30002537,  # Amamake,
                            "location_type": "solar_system",
                            "quantity": 1,
                            "type_id": 32226,
                        },
                    ],
                },
            ),
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_locations",
                "corporation_id",
                needs_token=True,
                data={
                    f"{cls.corporation.corporation_id}": [
                        {"item_id": 1500000000002, "position": {"x": 1, "y": 2, "z": 3}}
                    ]
                },
            ),
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(endpoints)

    def test_should_update_upwell_items_for_owner(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000001)
        StructureFactory(owner=owner, id=1000000000002)
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_assets_sync_fresh)
        self.assertSetEqual(
            queryset_pks(StructureItem.objects.all()),
            {1300000001001, 1300000001002, 1300000002001},
        )
        obj = owner.structures.get(pk=1000000000001).items.get(pk=1300000001001)
        self.assertEqual(obj.eve_type_id, 56201)
        self.assertEqual(
            obj.location_flag, StructureItem.LocationFlag.QUANTUM_CORE_ROOM
        )
        self.assertEqual(obj.quantity, 1)
        self.assertFalse(obj.is_singleton)

        obj = owner.structures.get(pk=1000000000001).items.get(pk=1300000001002)
        self.assertEqual(obj.eve_type_id, 35894)
        self.assertEqual(obj.location_flag, "ServiceSlot0")
        self.assertEqual(obj.quantity, 1)
        self.assertTrue(obj.is_singleton)

        structure = owner.structures.get(id=1000000000001)
        self.assertTrue(structure.has_fitting)
        self.assertTrue(structure.has_core)

        structure = owner.structures.get(id=1000000000002)
        self.assertTrue(structure.has_fitting)
        self.assertFalse(structure.has_core)

    @patch(OWNERS_PATH + ".notify", spec=True)
    def test_should_inform_user_about_successful_update(self, mock_notify, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000001)
        # when
        owner.update_asset_esi(user=self.user)
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_assets_sync_fresh)
        self.assertTrue(mock_notify.called)

    def test_should_raise_exception_if_esi_has_error(self, mock_esi):
        def my_callback(**kwargs):
            raise HTTPInternalServerError(
                BravadoResponseStub(status_code=500, reason="Test")
            )

        # given
        endpoints = [
            EsiEndpoint(
                "Assets",
                "get_corporations_corporation_id_assets",
                "corporation_id",
                needs_token=True,
                side_effect=my_callback,
            )
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000001)
        # when
        with self.assertRaises(HTTPInternalServerError):
            owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_assets_sync_fresh)

    def test_should_remove_assets_that_no_longer_exist_for_existing_structure(
        self, mock_esi
    ):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        structure = StructureFactory(owner=owner, id=1000000000001)
        item = StructureItemFactory(structure=structure)
        # when
        owner.update_asset_esi()
        # then
        self.assertFalse(structure.items.filter(pk=item.pk).exists())

    def test_should_remove_assets_that_no_longer_exist_for_removed_structure(
        self, mock_esi
    ):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000001)
        structure = StructureFactory(owner=owner, id=1000000000666)
        item = StructureItemFactory(structure=structure)
        # when
        owner.update_asset_esi()
        # then
        self.assertFalse(structure.items.filter(pk=item.pk).exists())

    def test_should_handle_asset_moved_to_another_structure(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        structure_1 = StructureFactory(owner=owner, id=1000000000001)
        structure_2 = StructureFactory(owner=owner, id=1000000000002)
        StructureItemFactory(
            structure=structure_2,
            id=1300000001002,
            eve_type_id=35894,
            location_flag="ServiceSlot0",
            is_singleton=True,
            quantity=1,
        )
        # when
        owner.update_asset_esi()
        # then
        self.assertSetEqual(queryset_pks(structure_2.items.all()), {1300000002001})
        self.assertSetEqual(
            queryset_pks(structure_1.items.all()), {1300000001001, 1300000001002}
        )

    def test_should_not_delete_assets_from_other_owners(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        user_2 = UserMainDefaultOwnerFactory()
        owner_2 = OwnerFactory(user=user_2)
        structure_2 = StructureFactory(
            owner=owner_2, id=1000000000004, quantum_core=False
        )
        StructureItemFactory(structure=structure_2, id=1300000003001)

        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000001, quantum_core=False)
        StructureFactory(owner=owner, id=1000000000002, quantum_core=False)

        # when
        owner.update_asset_esi()

        # then
        self.assertSetEqual(
            queryset_pks(StructureItem.objects.all()),
            {1300000001001, 1300000001002, 1300000002001, 1300000003001},
        )

    def test_should_remove_outdated_jump_fuel_alerts(self, mock_esi):
        # given
        user = UserMainDefaultOwnerFactory()
        owner = OwnerFactory(user=user)
        structure = StructureFactory(owner=owner, id=1000000000004)
        config = JumpFuelAlertConfigFactory(threshold=100)
        structure.jump_fuel_alerts.create(structure=structure, config=config)

        endpoints = [
            EsiEndpoint(
                "Assets",
                "get_corporations_corporation_id_assets",
                "corporation_id",
                needs_token=True,
                data={
                    f"{owner.corporation.corporation_id}": [
                        {
                            "is_singleton": False,
                            "item_id": 1300000003001,
                            "location_flag": "StructureFuel",
                            "location_id": 1000000000004,
                            "location_type": "item",
                            "quantity": 5000,
                            "type_id": 16273,
                        }
                    ]
                },
            ),
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_locations",
                "corporation_id",
                needs_token=True,
                data={f"{owner.corporation.corporation_id}": []},
            ),
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        # when
        owner.update_asset_esi()
        # then
        self.assertEqual(structure.jump_fuel_alerts.count(), 0)

    # TODO: Add tests for error cases

    def test_should_update_starbase_items_for_owner(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        StarbaseFactory(
            owner=owner, id=1500000000001, position_x=1, position_y=2, position_z=3
        )  # position needed to match assets
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_assets_sync_fresh)
        self.assertSetEqual(queryset_pks(StructureItem.objects.all()), {1500000000002})

    def test_should_update_upwell_items_for_owner_with_invalid_locations(
        self, mock_esi
    ):
        # given
        user = UserMainDefaultOwnerFactory()
        owner = OwnerFactory(user=user)
        structure = StructureFactory(owner=owner, id=1000000000004)

        endpoints = [
            EsiEndpoint(
                "Assets",
                "get_corporations_corporation_id_assets",
                "corporation_id",
                needs_token=True,
                data={
                    f"{owner.corporation.corporation_id}": [
                        {
                            "is_singleton": False,
                            "item_id": 1300000003001,
                            "location_flag": "StructureFuel",
                            "location_id": 1000000000004,
                            "location_type": "item",
                            "quantity": 5000,
                            "type_id": 16273,
                        }
                    ]
                },
            ),
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_locations",
                "corporation_id",
                needs_token=True,
                http_error_code=404,
            ),
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        # when
        owner.update_asset_esi()
        # then
        self.assertTrue(structure.items.filter(id=1300000003001).exists())


@patch(OWNERS_PATH + ".STRUCTURES_FEATURE_SKYHOOKS", True)
@patch(OWNERS_PATH + ".EveSolarSystem.nearest_celestial")
@patch(OWNERS_PATH + ".esi")
class TestOwnerUpdateSkyhooks(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.corporation = EveCharacterFactory()
        character = EveCharacterFactory(corporation=cls.corporation)
        cls.user = UserMainDefaultOwnerFactory(main_character__character=character)
        cls.planet = EvePlanet.objects.get(id=40161469)
        endpoints = [
            EsiEndpoint(
                "Assets",
                "get_corporations_corporation_id_assets",
                "corporation_id",
                needs_token=True,
                data={
                    f"{cls.corporation.corporation_id}": [
                        {
                            "is_singleton": True,
                            "item_id": 1000000010001,
                            "location_flag": "AutoFit",
                            "location_id": 30002537,
                            "location_type": "solar_system",
                            "quantity": 1,
                            "type_id": 81080,
                        },
                    ],
                },
            ),
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_locations",
                "corporation_id",
                needs_token=True,
                data={
                    f"{cls.corporation.corporation_id}": [
                        {"item_id": 1000000010001, "position": {"x": 1, "y": 2, "z": 3}}
                    ]
                },
            ),
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(endpoints)

    def test_should_create_new_skyhooks_from_scratch(
        self, mock_esi, mock_nearest_celestial
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_nearest_celestial.return_value = NearestCelestial(
            eve_object=self.planet, distance=35_000_000, eve_type=self.planet.eve_type
        )
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertEqual(owner.structures.count(), 1)
        obj: Structure = owner.structures.get(pk=1000000010001)
        self.assertTrue(obj.is_skyhook)
        self.assertEqual(obj.eve_planet, self.planet)

    def test_should_remove_obsolete_skyhooks(self, mock_esi, mock_nearest_celestial):
        # given
        mock_esi.client = self.esi_client_stub
        mock_nearest_celestial.return_value = NearestCelestial(
            eve_object=self.planet, distance=35_000_000, eve_type=self.planet.eve_type
        )
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        SkyhookFactory.create(owner=owner)
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertEqual(owner.structures.count(), 1)
        obj: Structure = owner.structures.get(pk=1000000010001)
        self.assertTrue(obj.is_skyhook)
        self.assertEqual(obj.eve_planet, self.planet)

    def test_should_update_existing_skyhook(self, mock_esi, mock_nearest_celestial):
        # given
        mock_esi.client = self.esi_client_stub
        mock_nearest_celestial.return_value = NearestCelestial(
            eve_object=self.planet, distance=35_000_000, eve_type=self.planet.eve_type
        )
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        SkyhookFactory.create(owner=owner, id=1000000010001, eve_planet_name="Thera I")
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertEqual(owner.structures.count(), 1)
        obj: Structure = owner.structures.get(pk=1000000010001)
        self.assertTrue(obj.is_skyhook)
        self.assertEqual(obj.eve_planet, self.planet)

    def test_should_ignore_os_error_when_resolving_planet(
        self, mock_esi, mock_nearest_celestial
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_nearest_celestial.side_effect = OSError
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertEqual(owner.structures.count(), 1)
        obj: Structure = owner.structures.get(pk=1000000010001)
        self.assertTrue(obj.is_skyhook)
        self.assertIsNone(obj.eve_planet)

    def test_should_ignore_no_reply_when_resolving_planet(
        self, mock_esi, mock_nearest_celestial
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_nearest_celestial.return_value = None
        owner = OwnerFactory(user=self.user, assets_last_update_at=None)
        # when
        owner.update_asset_esi()
        # then
        owner.refresh_from_db()
        self.assertEqual(owner.structures.count(), 1)
        obj: Structure = owner.structures.get(pk=1000000010001)
        self.assertTrue(obj.is_skyhook)
        self.assertIsNone(obj.eve_planet)


class TestOwnerToken(NoSocketsTestCase):
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
class TestOwnerUpdateIsUp(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
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
