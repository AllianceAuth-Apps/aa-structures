import datetime as dt
from unittest.mock import patch

import pook

from django.test import TestCase
from django.utils.timezone import utc
from eveuniverse.tests.testdata.factories_2 import (
    EveMoonFactory,
    EveSolarSystemFactory,
    EveTypeFactory,
)

from structures.constants import EveCorporationId
from structures.models import OwnerCharacter, StarbaseDetail, Structure
from structures.tests.testdata.factories import (
    EveEntityCorporationFactory,
    OwnerFactory,
    StarbaseFactory,
    StarbaseTypeFactory,
    UserMainDefaultOwnerFactory,
)

MODULE_PATH = "structures.models.owners"


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
class TestUpdateStarbasesEsi(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, structures_last_update_at=None)
        cls.corporation_id = cls.owner.corporation.corporation_id
        EveEntityCorporationFactory(
            id=EveCorporationId.DED, name="DED"
        )  # for notifications

    @pook.on
    def test_can_sync_starbases(self):
        # given
        fuel_1_type = EveTypeFactory(id=4051)  # Nitrogen Fuel Block
        fuel_2_type = EveTypeFactory(id=16275)  # Strontium Clathrates
        moon_1 = EveMoonFactory(id=40161465)
        solar_system = EveSolarSystemFactory(id=30002537)
        starbase_type = StarbaseTypeFactory(id=16213)  # Caldari Control Tower
        STARBASE_ID = 1300000000001
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": STARBASE_ID,
                    "position": {"x": 40.2, "y": 27.3, "z": -19.4},
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/names",
            reply=200,
            response_json=[
                {"item_id": STARBASE_ID, "name": "Home Sweat Home"},
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases",
            reply=200,
            response_json=[
                {
                    "moon_id": moon_1.id,
                    "starbase_id": STARBASE_ID,
                    "state": "online",
                    "system_id": solar_system.id,
                    "type_id": starbase_type.id,
                    "reinforced_until": dt.datetime(
                        2020, 4, 5, 7, tzinfo=utc
                    ).isoformat(),
                }
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases/{STARBASE_ID}",
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
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StarbaseFactory(owner=owner, id=1300000000099, name="delete-me")
        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)

        # must contain all expected structures
        expected = {STARBASE_ID}
        self.assertSetEqual(owner.structures.ids(), expected)

        # verify attributes for POS
        structure = Structure.objects.get(id=STARBASE_ID)
        self.assertEqual(structure.name, "Home Sweat Home")
        self.assertEqual(structure.eve_solar_system_id, solar_system.id)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.eve_type_id, starbase_type.id)
        self.assertEqual(structure.state, Structure.State.POS_ONLINE)
        self.assertEqual(structure.eve_moon_id, moon_1.id)
        self.assertEqual(
            structure.state_timer_end, dt.datetime(2020, 4, 5, 7, 0, 0, tzinfo=utc)
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
        self.assertEqual(detail.fuels.get(eve_type_id=fuel_1_type.id).quantity, 960)
        self.assertEqual(detail.fuels.get(eve_type_id=fuel_2_type.id).quantity, 11678)

        # structure = Structure.objects.get(id=1300000000002)
        # self.assertEqual(structure.name, "Bat cave")
        # self.assertEqual(structure.eve_solar_system_id, 30002537)
        # self.assertEqual(
        #     int(structure.owner.corporation.corporation_id), self.corporation_id
        # )
        # self.assertEqual(structure.eve_type_id, 20061)
        # self.assertEqual(structure.state, Structure.State.POS_OFFLINE)
        # self.assertEqual(structure.eve_moon_id, 40161466)
        # self.assertEqual(
        #     structure.unanchors_at, dt.datetime(2020, 5, 5, 7, 0, 0, tzinfo=utc)
        # )
        # self.assertIsNone(structure.fuel_expires_at)
        # self.assertFalse(structure.generatednotification_set.exists())

        # structure = Structure.objects.get(id=1300000000003)
        # self.assertEqual(structure.name, "Panic Room")
        # self.assertEqual(structure.eve_solar_system_id, 30000474)
        # self.assertEqual(
        #     int(structure.owner.corporation.corporation_id), self.corporation_id
        # )
        # self.assertEqual(structure.eve_type_id, 20062)
        # self.assertEqual(structure.state, Structure.State.POS_REINFORCED)
        # self.assertEqual(structure.eve_moon_id, 40029527)
        # self.assertAlmostEqual(
        #     structure.fuel_expires_at,
        #     now() + dt.timedelta(seconds=360_000),
        #     delta=dt.timedelta(seconds=30),
        # )
        # self.assertEqual(
        #     structure.state_timer_end, dt.datetime(2020, 1, 2, 3, tzinfo=utc)
        # )
        # self.assertTrue(structure.generatednotification_set.exists())

    @patch(MODULE_PATH + ".STRUCTURES_ESI_DIRECTOR_ERROR_MAX_RETRIES", 3)
    @patch(MODULE_PATH + ".notify", spec=True)
    @pook.on
    def test_should_mark_error_when_character_not_director_while_updating_starbases(
        self, mock_notify
    ):
        # given
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases",
            reply=403,
            response_json={"error": "forbidden"},
        )
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
    @pook.on
    def test_should_disable_character_when_not_director_while_updating_starbases(
        self, mock_notify
    ):
        # given
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases",
            reply=403,
            response_json={"error": "forbidden"},
        )
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

    @pook.on
    def test_should_reset_error_count_for_character_when_successful(self):
        # given
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases",
            reply=200,
            response_json=[],
        )
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

    @pook.on
    def test_should_not_delete_existing_starbases_when_update_failed(self):
        # given
        STARBASE_ID = 1300000000001
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases",
            reply=500,
            response_json={"error": "server error"},
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StarbaseFactory(owner=owner, id=STARBASE_ID)
        # when
        owner.update_structures_esi()
        # then
        # self.assertFalse(owner.is_structure_sync_fresh)
        expected = {STARBASE_ID}
        self.assertSetEqual(owner.structures.ids(), expected)

    @pook.on
    def test_should_not_break_when_starbase_names_not_found(self):
        # given
        moon_1 = EveMoonFactory(id=40161465)
        solar_system = EveSolarSystemFactory(id=30002537)
        starbase_type = StarbaseTypeFactory(id=16213)  # Caldari Control Tower
        STARBASE_ID = 1300000000001
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": STARBASE_ID,
                    "position": {"x": 40.2, "y": 27.3, "z": -19.4},
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/names",
            reply=404,
            response_json={"error": "not found"},
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases",
            reply=200,
            response_json=[
                {
                    "moon_id": moon_1.id,
                    "starbase_id": STARBASE_ID,
                    "state": "online",
                    "system_id": solar_system.id,
                    "type_id": starbase_type.id,
                    "reinforced_until": dt.datetime(
                        2020, 4, 5, 7, tzinfo=utc
                    ).isoformat(),
                }
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/starbases/{STARBASE_ID}",
            reply=200,
            response_json={
                "allow_alliance_members": True,
                "allow_corporation_members": True,
                "anchor": "config_starbase_equipment_role",
                "attack_if_at_war": False,
                "attack_if_other_security_status_dropping": False,
                "fuel_bay_take": "config_starbase_equipment_role",
                "fuel_bay_view": "starbase_fuel_technician_role",
                "fuels": [],
                "offline": "config_starbase_equipment_role",
                "online": "config_starbase_equipment_role",
                "unanchor": "config_starbase_equipment_role",
                "use_alliance_standings": True,
            },
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        owner.refresh_from_db()
        expected = {STARBASE_ID}
        self.assertSetEqual(owner.structures.ids(), expected)

    # Older below

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
    #     owner.refresh_from_db()
    #     self.assertTrue(owner.is_structure_sync_fresh)
    #     self.assertTrue(owner.is_structure_sync_fresh)
    #     self.assertTrue(owner.is_structure_sync_fresh)
    #     owner.refresh_from_db()
    #     self.assertTrue(owner.is_structure_sync_fresh)
    #     self.assertTrue(owner.is_structure_sync_fresh)


class TestPlayground(TestCase):
    def test_playground(self):
        x = StarbaseFactory()
        print(x.eve_type.eve_group.eve_category.id)
        print(x.eve_type.eve_group.eve_category.name)
        print(x.eve_type.eve_group.id)
        print(x.eve_type.eve_group.name)
        print(x.eve_type.id)
        print(x.eve_type.name)
