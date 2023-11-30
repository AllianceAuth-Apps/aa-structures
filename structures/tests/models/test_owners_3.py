from unittest.mock import patch

from app_utils.esi_testing import EsiClientStub, EsiEndpoint
from app_utils.testing import NoSocketsTestCase

from structures.constants import EveCorporationId
from structures.models import PocoDetails, Structure
from structures.tests.testdata.factories import (
    EveEntityCorporationFactory,
    OwnerFactory,
    PocoFactory,
    UserMainDefaultOwnerFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.models.owners"


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", True)
@patch(MODULE_PATH + ".esi")
class TestUpdatePocosEsi(NoSocketsTestCase):
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
                            "item_id": 1200000000003,
                            "position": {"x": 1.2, "y": 2.3, "z": -3.4},
                        },
                        {
                            "item_id": 1200000000004,
                            "position": {"x": 5.2, "y": 6.3, "z": -7.4},
                        },
                        {
                            "item_id": 1200000000005,
                            "position": {"x": 1.2, "y": 6.3, "z": -7.4},
                        },
                        {
                            "item_id": 1200000000006,
                            "position": {"x": 41.2, "y": 26.3, "z": -47.4},
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
                        {
                            "item_id": 1200000000003,
                            "name": "Customs Office (Amamake V)",
                        },
                        {
                            "item_id": 1200000000004,
                            "name": "Customs Office (1-PGSG VI)",
                        },
                        {
                            "item_id": 1200000000005,
                            "name": "Customs Office (1-PGSG VII)",
                        },
                        {
                            "item_id": 1200000000006,
                            "name": '<localized hint="Customs Office">Customs Office*</localized> (1-PGSG VIII)',
                        },
                    ]
                },
            ),
            EsiEndpoint(
                "Planetary_Interaction",
                "get_corporations_corporation_id_customs_offices",
                "corporation_id",
                needs_token=True,
                data={
                    str(cls.corporation_id): [
                        {
                            "alliance_tax_rate": 0.02,
                            "allow_access_with_standings": True,
                            "allow_alliance_access": True,
                            "bad_standing_tax_rate": 0.3,
                            "corporation_tax_rate": 0.02,
                            "excellent_standing_tax_rate": 0.02,
                            "good_standing_tax_rate": 0.02,
                            "neutral_standing_tax_rate": 0.02,
                            "office_id": 1200000000003,
                            "reinforce_exit_end": 21,
                            "reinforce_exit_start": 19,
                            "standing_level": "terrible",
                            "system_id": 30002537,
                            "terrible_standing_tax_rate": 0.5,
                        },
                        {
                            "alliance_tax_rate": 0.02,
                            "allow_access_with_standings": True,
                            "allow_alliance_access": True,
                            "bad_standing_tax_rate": 0.02,
                            "corporation_tax_rate": 0.02,
                            "excellent_standing_tax_rate": 0.02,
                            "good_standing_tax_rate": 0.02,
                            "neutral_standing_tax_rate": 0.02,
                            "office_id": 1200000000004,
                            "reinforce_exit_end": 21,
                            "reinforce_exit_start": 19,
                            "standing_level": "terrible",
                            "system_id": 30000474,
                            "terrible_standing_tax_rate": 0.02,
                        },
                        {
                            "alliance_tax_rate": 0.02,
                            "allow_access_with_standings": True,
                            "allow_alliance_access": True,
                            "bad_standing_tax_rate": 0.02,
                            "corporation_tax_rate": 0.02,
                            "excellent_standing_tax_rate": 0.02,
                            "good_standing_tax_rate": 0.02,
                            "neutral_standing_tax_rate": 0.02,
                            "office_id": 1200000000005,
                            "reinforce_exit_end": 21,
                            "reinforce_exit_start": 19,
                            "standing_level": "terrible",
                            "system_id": 30000474,
                            "terrible_standing_tax_rate": 0.02,
                        },
                        {
                            "alliance_tax_rate": 0.02,
                            "allow_access_with_standings": True,
                            "allow_alliance_access": True,
                            "bad_standing_tax_rate": 0.02,
                            "corporation_tax_rate": 0.02,
                            "excellent_standing_tax_rate": 0.02,
                            "good_standing_tax_rate": 0.02,
                            "neutral_standing_tax_rate": 0.02,
                            "office_id": 1200000000006,
                            "reinforce_exit_end": 21,
                            "reinforce_exit_start": 19,
                            "standing_level": "terrible",
                            "system_id": 30000474,
                            "terrible_standing_tax_rate": 0.02,
                        },
                        {
                            "alliance_tax_rate": 0.02,
                            "allow_access_with_standings": True,
                            "allow_alliance_access": True,
                            "bad_standing_tax_rate": 0.02,
                            "corporation_tax_rate": 0.02,
                            "excellent_standing_tax_rate": 0.02,
                            "good_standing_tax_rate": 0.02,
                            "neutral_standing_tax_rate": 0.02,
                            "office_id": 1200000000099,
                            "reinforce_exit_end": 21,
                            "reinforce_exit_start": 19,
                            "standing_level": "terrible",
                            "system_id": 30000474,
                            "terrible_standing_tax_rate": 0.02,
                        },
                    ]
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

    def test_can_sync_pocos(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)

        # must contain all expected structures
        expected = {
            1200000000003,
            1200000000004,
            1200000000005,
            1200000000006,
            1200000000099,
        }
        self.assertSetEqual(owner.structures.ids(), expected)
        self.assertSetEqual(
            set(PocoDetails.objects.values_list("structure_id", flat=True)),
            {1200000000003, 1200000000004, 1200000000005, 1200000000006, 1200000000099},
        )

        # verify attributes for POCO
        structure = Structure.objects.get(id=1200000000003)
        self.assertEqual(structure.name, "Planet (Barren)")
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.eve_type_id, 2233)
        self.assertEqual(structure.reinforce_hour, 20)
        self.assertEqual(structure.state, Structure.State.UNKNOWN)
        self.assertEqual(structure.eve_planet_id, 40161472)

        # verify attributes for POCO details
        details = structure.poco_details
        self.assertEqual(details.alliance_tax_rate, 0.02)
        self.assertTrue(details.allow_access_with_standings)
        self.assertTrue(details.allow_alliance_access)
        self.assertEqual(details.bad_standing_tax_rate, 0.3)
        self.assertEqual(details.corporation_tax_rate, 0.02)
        self.assertEqual(details.excellent_standing_tax_rate, 0.02)
        self.assertEqual(details.good_standing_tax_rate, 0.02)
        self.assertEqual(details.neutral_standing_tax_rate, 0.02)
        self.assertEqual(details.reinforce_exit_end, 21)
        self.assertEqual(details.reinforce_exit_start, 19)
        self.assertEqual(details.standing_level, PocoDetails.StandingLevel.TERRIBLE)
        self.assertEqual(details.terrible_standing_tax_rate, 0.5)

        # empty name for POCO with no asset data
        structure = Structure.objects.get(id=1200000000099)
        self.assertEqual(structure.name, "")

    def test_should_not_break_on_http_error_when_fetching_custom_offices(
        self, mock_esi
    ):
        # given
        new_endpoint = EsiEndpoint(
            "Planetary_Interaction",
            "get_corporations_corporation_id_customs_offices",
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

    def test_should_not_break_on_http_error_when_fetching_custom_office_names(
        self, mock_esi
    ):
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
        expected = {
            1200000000003,
            1200000000004,
            1200000000005,
            1200000000006,
            1200000000099,
        }
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_should_remove_old_pocos(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        PocoFactory(owner=owner, id=1200000000010, name="delete-me")
        # when
        owner.update_structures_esi()
        # then
        expected = {
            1200000000003,
            1200000000004,
            1200000000005,
            1200000000006,
            1200000000099,
        }
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_should_not_delete_existing_pocos_when_update_failed(self, mock_esi):
        # given
        new_endpoint = EsiEndpoint(
            "Planetary_Interaction",
            "get_corporations_corporation_id_customs_offices",
            http_error_code=500,
        )
        mock_esi.client = self.esi_client_stub.replace_endpoints([new_endpoint])
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        PocoFactory(owner=owner, id=1200000000003)
        PocoFactory(owner=owner, id=1200000000004)
        # when
        owner.update_structures_esi()
        # then
        self.assertFalse(owner.is_structure_sync_fresh)
        expected = {1200000000003, 1200000000004}
        self.assertSetEqual(owner.structures.ids(), expected)

    def test_should_have_empty_name_if_not_match_with_planets(self, mock_esi):
        # given
        owner = OwnerFactory(structures_last_update_at=None)
        corporation_id = owner.corporation.corporation_id
        endpoints = [
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_locations",
                "corporation_id",
                needs_token=True,
                data={
                    f"{corporation_id}": [
                        {
                            "item_id": 1200000000099,
                            "position": {"x": 1.2, "y": 2.3, "z": -3.4},
                        }
                    ]
                },
            ),
            EsiEndpoint(
                "Assets",
                "post_corporations_corporation_id_assets_names",
                "corporation_id",
                needs_token=True,
                data={
                    f"{corporation_id}": [
                        {
                            "item_id": 1200000000099,
                            "name": "Invalid name",
                        }
                    ]
                },
            ),
            EsiEndpoint(
                "Planetary_Interaction",
                "get_corporations_corporation_id_customs_offices",
                "corporation_id",
                needs_token=True,
                data={
                    f"{corporation_id}": [
                        {
                            "alliance_tax_rate": 0.02,
                            "allow_access_with_standings": True,
                            "allow_alliance_access": True,
                            "bad_standing_tax_rate": 0.3,
                            "corporation_tax_rate": 0.02,
                            "excellent_standing_tax_rate": 0.02,
                            "good_standing_tax_rate": 0.02,
                            "neutral_standing_tax_rate": 0.02,
                            "office_id": 1200000000099,
                            "reinforce_exit_end": 21,
                            "reinforce_exit_start": 19,
                            "standing_level": "terrible",
                            "system_id": 30002537,
                            "terrible_standing_tax_rate": 0.5,
                        }
                    ]
                },
            ),
            EsiEndpoint(
                "Corporation",
                "get_corporations_corporation_id_structures",
                "corporation_id",
                needs_token=True,
                data={f"{corporation_id}": []},
            ),  # TODO: Remove once possible
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        # when
        owner.update_structures_esi()
        # then
        self.assertTrue(owner.is_structure_sync_fresh)
        structure = Structure.objects.get(id=1200000000099)
        self.assertEqual(structure.name, "")

    def test_define_poco_name_from_planet_type_if_found(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()
        # then
        structure = Structure.objects.get(id=1200000000003)
        self.assertEqual(structure.eve_planet_id, 40161472)
        self.assertEqual(structure.name, "Planet (Barren)")
