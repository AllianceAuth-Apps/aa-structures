from typing import NamedTuple
from unittest.mock import patch

import pook

from django.test import TestCase
from eveuniverse.tests.testdata.factories_2 import EvePlanetFactory

from structures.constants import EveCorporationId
from structures.models import PocoDetails, Structure, owners
from structures.tests.testdata.factories import (
    CustomsOfficeFactory,
    CustomsOfficeTypeFactory,
    EveEntityCorporationFactory,
    OwnerFactory,
    PositionFactory,
    UserMainDefaultOwnerFactory,
)

MODULE_PATH = "structures.models.owners"


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", True)
class TestUpdateCustomOfficesEsi(TestCase):
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
    def test_can_sync_pocos_and_remove_old(self):
        # given
        planet = EvePlanetFactory(
            name="Amamake V",
            eve_solar_system__enabled_sections=1,  # 1 = Planets
            eve_type__name="Planet (Barren)",
        )
        poco_type = CustomsOfficeTypeFactory()
        customs_office_id = 1200000000003
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": customs_office_id,
                    "position": PositionFactory(),
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/names",
            reply=200,
            response_json=[
                {
                    "item_id": customs_office_id,
                    "name": f"Customs Office ({planet.name})",
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/customs_offices",
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
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        CustomsOfficeFactory(owner=owner, id=1200000000010, name="delete-me")

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)

        # must contain all expected structures
        self.assertSetEqual(owner.structures.ids(), {customs_office_id})
        self.assertSetEqual(
            set(PocoDetails.objects.values_list("structure_id", flat=True)),
            {customs_office_id},
        )

        # verify attributes for POCO
        structure = Structure.objects.get(id=customs_office_id)
        self.assertEqual(structure.name, "Planet (Barren)")
        self.assertEqual(structure.eve_solar_system_id, planet.eve_solar_system.id)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.eve_type_id, poco_type.id)
        self.assertEqual(structure.reinforce_hour, 20)
        self.assertEqual(structure.state, Structure.State.UNKNOWN)
        self.assertEqual(structure.eve_planet_id, planet.id)

        # verify attributes for POCO details
        details: PocoDetails = structure.poco_details
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

    @pook.on
    def test_poco_has_no_name_when_no_asset_data(self):
        # given
        planet = EvePlanetFactory(
            name="Amamake V",
            eve_solar_system__name="Amamake",
            eve_solar_system__enabled_sections=1,  # 1 = Planets
            eve_type__name="Planet (Barren)",
        )
        CustomsOfficeTypeFactory()
        customs_office_id = 1200000000003
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": customs_office_id,
                    "position": {"x": 40.2, "y": 27.3, "z": -19.4},
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/names",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/customs_offices",
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
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        # when
        owner.update_structures_esi()

        # then
        self.assertSetEqual(owner.structures.ids(), {customs_office_id})
        structure = Structure.objects.get(id=customs_office_id)
        self.assertEqual(structure.name, "")
        self.assertEqual(structure.eve_solar_system_id, planet.eve_solar_system.id)

    @pook.on
    def test_should_not_break_or_delete_on_http_error_when_fetching_custom_offices(
        self,
    ):
        # given
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/customs_offices",
            reply=500,
            response_json={"error": "internal error"},
        )
        customs_office_id = 1200000000003
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        CustomsOfficeFactory(owner=owner, id=customs_office_id, name="keep-me")
        # when
        owner.update_structures_esi()
        # then
        self.assertSetEqual(owner.structures.ids(), {customs_office_id})

    @pook.on
    def test_should_not_break_when_name_not_found(self):
        # given
        planet = EvePlanetFactory(
            name="Amamake V",
            eve_solar_system__name="Amamake",
            eve_solar_system__enabled_sections=1,  # 1 = Planets
            eve_type__name="Planet (Barren)",
        )
        CustomsOfficeTypeFactory()
        customs_office_id = 1200000000003
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": customs_office_id,
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
            f"https://esi.evetech.net/corporations/{self.corporation_id}/customs_offices",
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
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)

        # when
        owner.update_structures_esi()

        # then
        self.assertSetEqual(owner.structures.ids(), {customs_office_id})
        structure = Structure.objects.get(id=customs_office_id)
        self.assertEqual(structure.name, "")
        self.assertEqual(structure.eve_solar_system_id, planet.eve_solar_system.id)

    @pook.on
    def test_should_have_empty_name_when_no_match_with_planet(self):
        # given
        planet = EvePlanetFactory(
            name="Amamake V",
            eve_solar_system__name="Amamake",
            eve_solar_system__enabled_sections=1,  # 1 = Planets
            eve_type__name="Planet (Barren)",
        )
        CustomsOfficeTypeFactory()
        customs_office_id = 1200000000003
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/locations",
            reply=200,
            response_json=[
                {
                    "item_id": customs_office_id,
                    "position": {"x": 40.2, "y": 27.3, "z": -19.4},
                },
            ],
        )
        pook.post(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/assets/names",
            reply=200,
            response_json=[
                {
                    "item_id": customs_office_id,
                    "name": "invalid name",
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/customs_offices",
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
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        CustomsOfficeFactory(owner=owner, id=1200000000010, name="delete-me")

        # when
        owner.update_structures_esi()

        # then
        self.assertSetEqual(owner.structures.ids(), {customs_office_id})
        structure = Structure.objects.get(id=customs_office_id)
        self.assertEqual(structure.name, "")


class TestExtractPlanetNameFromAsset(TestCase):
    def test_ok(self):
        class Case(NamedTuple):
            input: str
            want: str

        cases = [
            Case("Customs Office (Amamake V)", "Amamake V"),
            Case("Customs Office (1-PGSG VI)", "1-PGSG VI"),
            Case("Customs Office (1-PGSG VII)", "1-PGSG VII"),
            Case("invalid name", ""),
        ]
        for tc in cases:
            with self.subTest(input=tc.input):
                got = owners._extract_planet_name_from_asset(tc.input)
                self.assertEqual(got, tc.want)
