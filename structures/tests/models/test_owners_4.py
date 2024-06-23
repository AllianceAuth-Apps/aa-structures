import datetime as dt
from unittest.mock import patch

from django.utils.timezone import now, utc

from app_utils.esi_testing import EsiClientStub, EsiEndpoint
from app_utils.testing import NoSocketsTestCase

from structures.constants import EveCorporationId
from structures.models import OwnerCharacter, StarbaseDetail, Structure
from structures.tests.testdata.factories import (
    EveEntityCorporationFactory,
    OwnerFactory,
    StarbaseFactory,
    UserMainDefaultOwnerFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.models.owners"


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
@patch(MODULE_PATH + ".esi")
class TestUpdateStarbasesEsi(NoSocketsTestCase):
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
                "post_corporations_corporation_id_assets_locations",
                "corporation_id",
                needs_token=True,
                data={
                    str(cls.corporation_id): [
                        {
                            "item_id": 1300000000001,
                            "position": {"x": 40.2, "y": 27.3, "z": -19.4},
                        },
                    ]
                },
            ),
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_names",
                "corporation_id",
                needs_token=True,
                data={
                    str(cls.corporation_id): [
                        {"item_id": 1300000000001, "name": "Home Sweat Home"},
                        {"item_id": 1300000000002, "name": "Bat cave"},
                        {"item_id": 1300000000003, "name": "Panic Room"},
                    ]
                },
            ),
            EsiEndpoint(
                "Corporation",
                "get_corporations_corporation_id_starbases",
                "corporation_id",
                needs_token=True,
                data={
                    str(cls.corporation_id): [
                        {
                            "moon_id": 40161465,
                            "starbase_id": 1300000000001,
                            "state": "online",
                            "system_id": 30002537,
                            "type_id": 16213,  # Caldari Control Tower
                            "reinforced_until": dt.datetime(2020, 4, 5, 7, tzinfo=utc),
                        },
                        {
                            "moon_id": 40161466,
                            "starbase_id": 1300000000002,
                            "state": "offline",
                            "system_id": 30002537,
                            "type_id": 20061,  # Caldari Control Tower Medium
                            "unanchors_at": dt.datetime(2020, 5, 5, 7, tzinfo=utc),
                        },
                        {
                            "moon_id": 40029527,
                            "reinforced_until": dt.datetime(2020, 1, 2, 3, tzinfo=utc),
                            "starbase_id": 1300000000003,
                            "state": "reinforced",
                            "system_id": 30000474,
                            "type_id": 20062,  # Caldari Control Tower Small
                        },
                    ]
                },
            ),
            EsiEndpoint(
                "Corporation",
                "get_corporations_corporation_id_starbases_starbase_id",
                ("corporation_id", "starbase_id"),
                needs_token=True,
                data={
                    str(cls.corporation_id): {
                        "1300000000001": {
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
                                    "type_id": 4051,  # Nitrogen Fuel Block
                                },
                                {
                                    "quantity": 11678,
                                    "type_id": 16275,  # Strontium Clathrates
                                },
                            ],
                            "offline": "config_starbase_equipment_role",
                            "online": "config_starbase_equipment_role",
                            "unanchor": "config_starbase_equipment_role",
                            "use_alliance_standings": True,
                        },
                        "1300000000002": {
                            "allow_alliance_members": True,
                            "allow_corporation_members": True,
                            "anchor": "config_starbase_equipment_role",
                            "attack_if_at_war": False,
                            "attack_if_other_security_status_dropping": False,
                            "fuel_bay_take": "config_starbase_equipment_role",
                            "fuels": [
                                {"quantity": 5, "type_id": 4051},
                                {"quantity": 11678, "type_id": 16275},
                            ],
                            "fuel_bay_view": "starbase_fuel_technician_role",
                            "offline": "config_starbase_equipment_role",
                            "online": "config_starbase_equipment_role",
                            "unanchor": "config_starbase_equipment_role",
                            "use_alliance_standings": True,
                        },
                        "1300000000003": {
                            "allow_alliance_members": True,
                            "allow_corporation_members": True,
                            "anchor": "config_starbase_equipment_role",
                            "attack_if_at_war": False,
                            "attack_if_other_security_status_dropping": False,
                            "fuel_bay_take": "config_starbase_equipment_role",
                            "fuel_bay_view": "starbase_fuel_technician_role",
                            "fuels": [
                                {
                                    "quantity": 1000,
                                    "type_id": 4051,  # Nitrogen Fuel Block
                                },
                                {
                                    "quantity": 11678,
                                    "type_id": 16275,  # Strontium Clathrates
                                },
                            ],
                            "offline": "config_starbase_equipment_role",
                            "online": "config_starbase_equipment_role",
                            "unanchor": "config_starbase_equipment_role",
                            "use_alliance_standings": True,
                        },
                    }
                },
            ),
            EsiEndpoint(
                "Corporation",
                "get_corporations_corporation_id_structures",
                "corporation_id",
                needs_token=True,
                data={str(cls.corporation_id): [], "2005": []},
            ),  # TODO: Remove once possible
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(cls.endpoints)

    def test_can_sync_starbases(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)

        # must contain all expected structures
        expected = {1300000000001, 1300000000002, 1300000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

        # verify attributes for POS
        structure = Structure.objects.get(id=1300000000001)
        self.assertEqual(structure.name, "Home Sweat Home")
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.eve_type_id, 16213)
        self.assertEqual(structure.state, Structure.State.POS_ONLINE)
        self.assertEqual(structure.eve_moon_id, 40161465)
        self.assertEqual(
            structure.state_timer_end, dt.datetime(2020, 4, 5, 7, 0, 0, tzinfo=utc)
        )
        self.assertAlmostEqual(
            structure.fuel_expires_at,
            now() + dt.timedelta(hours=24),
            delta=dt.timedelta(seconds=30),
        )
        self.assertEqual(structure.position_x, 40.2)
        self.assertEqual(structure.position_y, 27.3)
        self.assertEqual(structure.position_z, -19.4)
        # verify details
        detail = structure.starbase_detail
        self.assertTrue(detail.allow_alliance_members)
        self.assertTrue(detail.allow_corporation_members)
        self.assertEqual(
            detail.anchor_role, StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
        )
        self.assertFalse(detail.attack_if_at_war)
        self.assertFalse(detail.attack_if_other_security_status_dropping)
        self.assertEqual(
            detail.anchor_role, StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
        )
        self.assertEqual(
            detail.fuel_bay_take_role,
            StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE,
        )
        self.assertEqual(
            detail.fuel_bay_view_role,
            StarbaseDetail.Role.STARBASE_FUEL_TECHNICIAN_ROLE,
        )
        self.assertEqual(
            detail.offline_role,
            StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE,
        )
        self.assertEqual(
            detail.online_role,
            StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE,
        )
        self.assertEqual(
            detail.unanchor_role,
            StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE,
        )
        self.assertTrue(detail.use_alliance_standings)
        # fuels
        self.assertEqual(detail.fuels.count(), 2)
        self.assertEqual(detail.fuels.get(eve_type_id=4051).quantity, 960)
        self.assertEqual(detail.fuels.get(eve_type_id=16275).quantity, 11678)

        structure = Structure.objects.get(id=1300000000002)
        self.assertEqual(structure.name, "Bat cave")
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.eve_type_id, 20061)
        self.assertEqual(structure.state, Structure.State.POS_OFFLINE)
        self.assertEqual(structure.eve_moon_id, 40161466)
        self.assertEqual(
            structure.unanchors_at, dt.datetime(2020, 5, 5, 7, 0, 0, tzinfo=utc)
        )
        self.assertIsNone(structure.fuel_expires_at)
        self.assertFalse(structure.generatednotification_set.exists())

        structure = Structure.objects.get(id=1300000000003)
        self.assertEqual(structure.name, "Panic Room")
        self.assertEqual(structure.eve_solar_system_id, 30000474)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.eve_type_id, 20062)
        self.assertEqual(structure.state, Structure.State.POS_REINFORCED)
        self.assertEqual(structure.eve_moon_id, 40029527)
        self.assertAlmostEqual(
            structure.fuel_expires_at,
            now() + dt.timedelta(seconds=360_000),
            delta=dt.timedelta(seconds=30),
        )
        self.assertEqual(
            structure.state_timer_end, dt.datetime(2020, 1, 2, 3, tzinfo=utc)
        )
        self.assertTrue(structure.generatednotification_set.exists())

    # @patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
    # @patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", True)
    # @patch(MODULE_PATH + ".notify", spec=True)
    # def test_can_sync_all_structures_and_notify_user(self, mock_notify, mock_esi):
    #     # given
    #     mock_esi.client = self.esi_client_stub
    #     owner = OwnerFactory(user=self.user, structures_last_update_at=None)

    #     # when
    #     owner.update_structures_esi(user=self.user)

    #     # then
    #     owner.refresh_from_db()
    #     self.assertTrue(owner.is_structure_sync_fresh)

    #     # must contain all expected structures
    #     expected = {
    #         1200000000003,
    #         1200000000004,
    #         1200000000005,
    #         1200000000006,
    #         1200000000099,
    #         1300000000001,
    #         1300000000002,
    #         1300000000003,
    #     }
    #     self.assertSetEqual(owner.structures.ids(), expected)

    #     # user report has been sent
    #     self.assertTrue(mock_notify.called)

    def test_should_not_break_on_http_error_when_fetching_starbases(self, mock_esi):
        # given
        new_endpoint = EsiEndpoint(
            "Corporation",
            "get_corporations_corporation_id_starbases",
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

    @patch(MODULE_PATH + ".STRUCTURES_ESI_DIRECTOR_ERROR_MAX_RETRIES", 3)
    @patch(MODULE_PATH + ".notify", spec=True)
    def test_should_mark_error_when_character_not_director_while_updating_starbases(
        self, mock_notify, mock_esi
    ):
        # given
        new_endpoint = EsiEndpoint(
            "Corporation",
            "get_corporations_corporation_id_starbases",
            http_error_code=403,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        self.assertTrue(mock_notify)
        character: OwnerCharacter = owner.characters.first()
        self.assertEqual(character.error_count, 1)
        self.assertTrue(character.is_enabled)

    @patch(MODULE_PATH + ".STRUCTURES_ESI_DIRECTOR_ERROR_MAX_RETRIES", 3)
    @patch(MODULE_PATH + ".notify", spec=True)
    def test_should_disable_character_when_not_director_while_updating_starbases(
        self, mock_notify, mock_esi
    ):
        # given
        new_endpoint = EsiEndpoint(
            "Corporation",
            "get_corporations_corporation_id_starbases",
            http_error_code=403,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        character: OwnerCharacter = owner.characters.first()
        character.error_count = 3
        character.save()
        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        self.assertTrue(mock_notify)
        character.refresh_from_db()
        self.assertFalse(character.is_enabled)

    def test_should_reset_error_count_for_character_when_successful(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        character: OwnerCharacter = owner.characters.first()
        character.error_count = 3
        character.save()
        # when
        owner.update_structures_esi()
        # then
        character.refresh_from_db()
        self.assertTrue(character.is_enabled)
        self.assertEqual(character.error_count, 0)

    def test_should_remove_old_starbases(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StarbaseFactory(owner=owner, id=1300000000099, name="delete-me")
        # when
        owner.update_structures_esi()
        # then
        expected = {1300000000001, 1300000000002, 1300000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_should_not_delete_existing_starbases_when_update_failed(self, mock_esi):
        # given

        new_endpoint = EsiEndpoint(
            "Corporation",
            "get_corporations_corporation_id_starbases",
            http_error_code=500,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StarbaseFactory(owner=owner, id=1300000000001)
        StarbaseFactory(owner=owner, id=1300000000002)
        # when
        owner.update_structures_esi()
        # then
        # self.assertFalse(owner.is_structure_sync_fresh)
        expected = {1300000000001, 1300000000002}
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_should_not_break_when_starbase_names_not_found(self, mock_esi):
        # given
        new_endpoint = EsiEndpoint(
            "Assets",
            "post_corporations_corporation_id_assets_names",
            http_error_code=404,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        expected = {1300000000001, 1300000000002, 1300000000003}
        self.assertSetEqual(owner.structures.ids(), expected)

    # @patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
    # @patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
    # def test_should_notify_admins_when_service_is_restored(
    #     self, mock_esi_client
    # ):
    #     # given
    #     mock_esi_client.side_effect = esi_mock_client
    #     owner = OwnerFactory(user=self.user, structures_last_update_at=None)
    #     owner.is_structure_sync_fresh = False
    #     owner.save()
    #     # when
    #     owner.update_structures_esi()
    #     # then
    #     owner.refresh_from_db()
    #     self.assertTrue(owner.is_structure_sync_fresh)
