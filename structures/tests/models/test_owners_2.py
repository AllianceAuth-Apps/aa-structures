import datetime as dt
from unittest.mock import patch

from django.utils.timezone import now, utc

from app_utils.esi_testing import EsiClientStub, EsiEndpoint
from app_utils.testing import NoSocketsTestCase

from structures.constants import EveCorporationId
from structures.core.notification_types import NotificationType
from structures.models import Structure, StructureService
from structures.tests import to_json
from structures.tests.testdata.factories import (
    EveEntityCorporationFactory,
    FuelAlertConfigFactory,
    OwnerFactory,
    StructureFactory,
    StructureServiceFactory,
    StructureTagFactory,
    UserMainDefaultOwnerFactory,
    WebhookFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.models.owners"


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
@patch(MODULE_PATH + ".esi")
class TestUpdateStructuresEsi(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, structures_last_update_at=None)
        cls.corporation_id = cls.owner.corporation.corporation_id
        EveEntityCorporationFactory(
            id=EveCorporationId.DED, name="DED"
        )  # for notifications
        cls.endpoints = [
            EsiEndpoint(
                "Assets",
                "get_corporations_corporation_id_assets",
                "corporation_id",
                needs_token=True,
                data={
                    str(cls.corporation_id): [
                        {
                            "is_singleton": False,
                            "item_id": 1300000001001,
                            "location_flag": "QuantumCoreRoom",
                            "location_id": 1000000000001,
                            "location_type": "item",
                            "quantity": 1,
                            "type_id": 56201,  # Astrahus Upwell Quantum Core
                        },
                        {
                            "is_singleton": True,
                            "item_id": 1300000001002,
                            "location_flag": "ServiceSlot0",
                            "location_id": 1000000000001,
                            "location_type": "item",
                            "quantity": 1,
                            "type_id": 35894,  # Standup Cloning Center I
                        },
                        {
                            "is_singleton": True,
                            "item_id": 1300000002001,
                            "location_flag": "ServiceSlot0",
                            "location_id": 1000000000002,
                            "location_type": "item",
                            "quantity": 1,
                            "type_id": 35894,  # Standup Cloning Center I
                        },
                    ],
                    "2102": [
                        {
                            "is_singleton": False,
                            "item_id": 1300000003001,
                            "location_flag": "StructureFuel",
                            "location_id": 1000000000004,
                            "location_type": "item",
                            "quantity": 5000,
                            "type_id": 16273,  # Liquid Ozone
                        }
                    ],
                },
            ),
            EsiEndpoint(
                "Corporation",
                "get_corporations_corporation_id_structures",
                "corporation_id",
                needs_token=True,
                data={
                    str(cls.corporation_id): [
                        {
                            "corporation_id": cls.corporation_id,
                            "fuel_expires": dt.datetime(2020, 3, 5, 5, tzinfo=utc),
                            "next_reinforce_apply": None,
                            "next_reinforce_hour": None,
                            "profile_id": 52436,
                            "reinforce_hour": 19,
                            "services": [
                                {"name": "Reprocessing", "state": "online"},
                                {"name": "Moon Drilling", "state": "online"},
                            ],
                            "state": "shield_vulnerable",
                            "state_timer_end": None,
                            "state_timer_start": None,
                            "structure_id": 1000000000002,
                            "system_id": 30002537,
                            "type_id": 35835,  # Athanor
                            "unanchors_at": None,
                        },
                        {
                            "corporation_id": cls.corporation_id,
                            "fuel_expires": dt.datetime(2020, 3, 5, 5, tzinfo=utc),
                            "next_reinforce_apply": None,
                            "next_reinforce_hour": None,
                            "profile_id": 101853,
                            "reinforce_hour": 18,
                            "services": [
                                {"name": "Clone Bay", "state": "online"},
                                {"name": "Market Hub", "state": "offline"},
                            ],
                            "state": "shield_vulnerable",
                            "state_timer_end": dt.datetime(2020, 4, 5, 7, tzinfo=utc),
                            "state_timer_start": dt.datetime(
                                2020, 4, 5, 6, 30, tzinfo=utc
                            ),
                            "structure_id": 1000000000001,
                            "system_id": 30002537,
                            "type_id": 35832,  # Astrahus
                            "unanchors_at": dt.datetime(2020, 5, 5, 6, 30, tzinfo=utc),
                        },
                        {
                            "corporation_id": cls.corporation_id,
                            "fuel_expires": None,
                            "next_reinforce_apply": None,
                            "next_reinforce_hour": None,
                            "profile_id": 101853,
                            "reinforce_hour": 18,
                            "services": None,
                            "state": "shield_vulnerable",
                            "state_timer_end": None,
                            "state_timer_start": None,
                            "structure_id": 1000000000003,
                            "system_id": 30000476,
                            "type_id": 35832,  # Astrahus
                            "unanchors_at": None,
                        },
                    ],
                },
            ),
            EsiEndpoint(
                "Universe",
                "get_universe_structures_structure_id",
                "structure_id",
                needs_token=True,
                data={
                    "1000000000001": {
                        "corporation_id": cls.corporation_id,
                        "name": "Amamake - Test Structure Alpha",
                        "position": {
                            "x": 55028384780.0,
                            "y": 7310316270.0,
                            "z": -163686684205.0,
                        },
                        "solar_system_id": 30002537,
                        "type_id": 35832,  # Astrahus
                    },
                    "1000000000002": {
                        "corporation_id": cls.corporation_id,
                        "name": "Amamake - Test Structure Bravo",
                        "position": {
                            "x": -2518743930339.066,
                            "y": -130157937025.56424,
                            "z": -442026427345.6355,
                        },
                        "solar_system_id": 30002537,
                        "type_id": 35835,  # Athanor
                    },
                    "1000000000003": {
                        "corporation_id": cls.corporation_id,
                        "name": "Amamake - Test Structure Charlie",
                        "position": {
                            "x": -2518743930339.066,
                            "y": -130157937025.56424,
                            "z": -442026427345.6355,
                        },
                        "solar_system_id": 30000476,
                        "type_id": 35832,  # Astrahus
                    },
                },
            ),
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(cls.endpoints)

    def test_can_sync_upwell_structures(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)
        self.assertAlmostEqual(
            owner.structures_last_update_at, now(), delta=dt.timedelta(seconds=30)
        )

        # must contain all expected structures
        expected = {1000000000001, 1000000000002, 1000000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

        # verify attributes for structure
        structure = Structure.objects.get(id=1000000000001)
        self.assertEqual(structure.name, "Test Structure Alpha")
        self.assertEqual(structure.position_x, 55028384780.0)
        self.assertEqual(structure.position_y, 7310316270.0)
        self.assertEqual(structure.position_z, -163686684205.0)
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(structure.eve_type_id, 35832)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.state, Structure.State.SHIELD_VULNERABLE)
        self.assertEqual(structure.reinforce_hour, 18)
        self.assertEqual(
            structure.fuel_expires_at, dt.datetime(2020, 3, 5, 5, 0, 0, tzinfo=utc)
        )
        self.assertEqual(
            structure.state_timer_start, dt.datetime(2020, 4, 5, 6, 30, 0, tzinfo=utc)
        )
        self.assertEqual(
            structure.state_timer_end, dt.datetime(2020, 4, 5, 7, 0, 0, tzinfo=utc)
        )
        self.assertEqual(
            structure.unanchors_at, dt.datetime(2020, 5, 5, 6, 30, 0, tzinfo=utc)
        )

        # must have created services with localizations
        # structure 1000000000001
        expected = {
            to_json(
                {
                    "name": "Clone Bay",
                    "name_de": "",
                    "name_ko": "",
                    "name_ru": "",
                    # "name_zh": "Clone Bay_zh",
                    "state": StructureService.State.ONLINE,
                }
            ),
            to_json(
                {
                    "name": "Market Hub",
                    "name_de": "",
                    "name_ko": "",
                    "name_ru": "",
                    # "name_zh": "Market Hub_zh",
                    "state": StructureService.State.OFFLINE,
                }
            ),
        }
        structure = Structure.objects.get(id=1000000000001)
        services = {
            to_json(
                {
                    "name": x.name,
                    "name_de": "",
                    "name_ko": "",
                    "name_ru": "",
                    # "name_zh": x.name_zh,
                    "state": x.state,
                }
            )
            for x in structure.services.all()
        }
        self.assertEqual(services, expected)

        # must have created services with localizations
        # structure 1000000000002
        expected = {
            to_json(
                {
                    "name": "Reprocessing",
                    "name_de": "",
                    "name_ko": "",
                    "name_ru": "",
                    # "name_zh": "Reprocessing_zh",
                    "state": StructureService.State.ONLINE,
                }
            ),
            to_json(
                {
                    "name": "Moon Drilling",
                    "name_de": "",
                    "name_ko": "",
                    "name_ru": "",
                    # "name_zh": "Moon Drilling_zh",
                    "state": StructureService.State.ONLINE,
                }
            ),
        }
        structure = Structure.objects.get(id=1000000000002)
        services = {
            to_json(
                {
                    "name": x.name,
                    "name_de": "",
                    "name_ko": "",
                    "name_ru": "",
                    # "name_zh": x.name_zh,
                    "state": x.state,
                }
            )
            for x in structure.services.all()
        }
        self.assertEqual(services, expected)

    def test_can_handle_owner_without_structures(self, mock_esi):
        # given
        owner = OwnerFactory(structures_last_update_at=None)
        corporation_id = owner.corporation.corporation_id
        endpoints = [
            EsiEndpoint(
                "Corporation",
                "get_corporations_corporation_id_structures",
                "corporation_id",
                needs_token=True,
                data={f"{corporation_id}": []},
            ),
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)

        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)
        self.assertSetEqual(owner.structures.ids(), set())

    def test_should_not_break_when_endpoint_for_fetching_upwell_structures_is_down(
        self, mock_esi
    ):
        # given
        new_endpoint = EsiEndpoint(
            "Corporation",
            "get_corporations_corporation_id_structures",
            http_error_code=500,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        expected = set()
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_update_will_not_break_on_http_error_from_structure_info(self, mock_esi):
        # given
        new_endpoint = EsiEndpoint(
            "Universe", "get_universe_structures_structure_id", http_error_code=500
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        self.assertFalse(owner.is_structure_sync_fresh)
        structure = Structure.objects.get(id=1000000000002)
        self.assertEqual(structure.name, "(no data)")

    def test_update_will_not_break_on_403_error_from_structure_info(self, mock_esi):
        # given
        new_endpoint = EsiEndpoint(
            "Universe", "get_universe_structures_structure_id", http_error_code=403
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        self.assertFalse(owner.is_structure_sync_fresh)
        structure = Structure.objects.get(id=1000000000002)
        self.assertEqual(structure.name, "(no data)")

    @patch(MODULE_PATH + ".Structure.objects.update_or_create_from_dict")
    def test_update_will_not_break_on_http_error_when_creating_structures(
        self, mock_create_structure, mock_esi
    ):
        mock_create_structure.side_effect = OSError
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        self.assertFalse(owner.is_structure_sync_fresh)

    def test_should_remove_old_upwell_structures(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000004, name="delete-me")
        # when
        owner.update_structures_esi()
        # then
        expected = {1000000000001, 1000000000002, 1000000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_tags_are_not_modified_by_update(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then

        # should contain the right structures
        expected = {1000000000001, 1000000000002, 1000000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

        # adding tags
        tag_a = StructureTagFactory(name="tag_a")
        s = Structure.objects.get(id=1000000000001)
        s.tags.add(tag_a)
        s.save()

        # run update task 2nd time
        owner.update_structures_esi()

        # should still contain alls structures
        expected = {1000000000001, 1000000000002, 1000000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

        # should still contain the tag
        s_new = Structure.objects.get(id=1000000000001)
        self.assertEqual(s_new.tags.get(name="tag_a"), tag_a)

    def test_should_not_delete_existing_upwell_structures_when_update_failed(
        self, mock_esi
    ):
        # given
        new_endpoint = EsiEndpoint(
            "Corporation",
            "get_corporations_corporation_id_structures",
            http_error_code=500,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000001)
        StructureFactory(owner=owner, id=1000000000002)
        # when
        owner.update_structures_esi()
        # then
        self.assertFalse(owner.is_structure_sync_fresh)
        expected = {1000000000001, 1000000000002}
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_should_remove_outdated_services(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure = StructureFactory(owner=owner, id=1000000000002)
        StructureServiceFactory(structure=structure, name="Clone Bay")
        # when
        owner.update_structures_esi()
        # then
        structure.refresh_from_db()
        services = {
            obj.name for obj in StructureService.objects.filter(structure=structure)
        }
        self.assertEqual(services, {"Moon Drilling", "Reprocessing"})

    @patch(
        "structures.models.structures_1.STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS", True
    )
    @patch("structures.models.notifications.Webhook.send_message")
    def test_should_send_refueled_notification_when_fuel_level_increased(
        self, mock_send_message, mock_esi
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA],
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        owner.webhooks.add(webhook)
        owner.update_structures_esi()
        structure = Structure.objects.get(id=1000000000001)
        structure.fuel_expires_at = dt.datetime(2020, 3, 3, 0, 0, tzinfo=utc)
        structure.save()
        # when
        with patch("structures.models.structures_1.now") as now:
            now.return_value = dt.datetime(2020, 3, 2, 0, 0, tzinfo=utc)
            owner.update_structures_esi()
        # then
        self.assertTrue(mock_send_message.called)

    @patch(
        "structures.models.structures_1.STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS", True
    )
    @patch("structures.models.notifications.Webhook.send_message")
    def test_should_not_send_refueled_notification_when_fuel_level_unchanged(
        self, mock_send_message, mock_esi
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA],
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        owner.webhooks.add(webhook)
        with patch("structures.models.structures_1.now") as now:
            now.return_value = dt.datetime(2020, 3, 2, 0, 0, tzinfo=utc)
            owner.update_structures_esi()
            # when
            owner.update_structures_esi()
        # then
        self.assertFalse(mock_send_message.called)

    @patch("structures.models.notifications.Webhook.send_message")
    def test_should_remove_outdated_fuel_alerts_when_fuel_level_changed(
        self, mock_send_message, mock_esi
    ):
        # given
        mock_esi.client = self.esi_client_stub
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA],
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        owner.webhooks.add(webhook)
        owner.update_structures_esi()
        structure = Structure.objects.get(id=1000000000001)
        structure.fuel_expires_at = dt.datetime(2020, 3, 3, 0, 0, tzinfo=utc)
        structure.save()
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure.structure_fuel_alerts.create(config=config, hours=12)
        # when
        with patch("structures.models.structures_1.now") as now:
            now.return_value = dt.datetime(2020, 3, 2, 0, 0, tzinfo=utc)
            owner.update_structures_esi()
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)
