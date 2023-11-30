from typing import List

from django.test import RequestFactory

from app_utils.testdata_factories import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
)
from app_utils.testing import NoSocketsTestCase

from structures.core.serializers import PocoListSerializer, StructureListSerializer
from structures.models import Structure
from structures.tests.testdata.factories import (
    JumpGateFactory,
    OwnerFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    UserMainDefaultFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse


def to_dict(lst: List[dict], key="id"):
    return {obj[key]: obj for obj in lst}


class TestStructureListSerializer(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=cls.user)
        alliance = EveAllianceInfoFactory(
            alliance_name="Wayne Enterprises", alliance_ticker="WYE"
        )
        corporation = EveCorporationInfoFactory(
            corporation_name="Wayne Technologies", alliance=alliance
        )
        character = EveCharacterFactory(corporation=corporation)
        cls.user = UserMainDefaultFactory(main_character__character=character)
        cls.owner = OwnerFactory(corporation=corporation)

    def _render_structure(self, structure: Structure, queryset=None) -> dict:
        """Return rendered data row for a structure."""
        request = self.factory.get("/")
        request.user = self.user
        my_queryset = queryset or Structure.objects.all()
        data = StructureListSerializer(queryset=my_queryset, request=request).to_list()
        obj = to_dict(data)[structure.id]
        return obj

    def test_should_render_upwell_structure(self):
        # given
        structure = StructureFactory(
            owner=self.owner, eve_solar_system_name="Amamake", eve_type_name="Astrahus"
        )
        # when
        obj = self._render_structure(structure)
        # then
        self.assertEqual(obj["alliance_name"], "Wayne Enterprises [WYE]")
        self.assertEqual(obj["corporation_name"], "Wayne Technologies")
        self.assertEqual(obj["region_name"], "Heimatar")
        self.assertEqual(obj["solar_system_name"], "Amamake")
        self.assertEqual(obj["group_name"], "Citadel")
        self.assertEqual(obj["category_name"], "Structure")
        self.assertFalse(obj["is_starbase"])
        self.assertFalse(obj["is_poco"])
        self.assertEqual(obj["type_name"], "Astrahus")
        self.assertFalse(obj["is_reinforced"])
        self.assertEqual(obj["is_reinforced_str"], "no")
        self.assertEqual(
            obj["fuel_and_power"]["fuel_expires_at"],
            structure.fuel_expires_at.isoformat(),
        )
        self.assertEqual(obj["power_mode_str"], "Full Power")
        self.assertEqual(obj["state_str"], "Shield vulnerable")
        self.assertEqual(obj["core_status_str"], "yes")
        self.assertEqual(obj["details"], "")

    def test_should_show_reinforced_for_structure(self):
        # given
        structure = StructureFactory(
            owner=self.owner, state=Structure.State.ARMOR_REINFORCE
        )
        # when
        obj = self._render_structure(structure)
        # then
        self.assertTrue(obj["is_reinforced"])

    def test_should_show_not_reinforced_for_starbase(self):
        # given
        structure = StarbaseFactory(owner=self.owner)
        # when
        obj = self._render_structure(structure)
        # then
        self.assertFalse(obj["is_reinforced"])

    def test_should_show_reinforced_for_starbase(self):
        # given
        structure = StarbaseFactory(
            owner=self.owner, state=Structure.State.POS_REINFORCED
        )
        # when
        obj = self._render_structure(structure)
        # then
        self.assertTrue(obj["is_reinforced"])

    def test_should_handle_owner_without_alliance(self):
        # given
        corporation = EveCorporationInfoFactory(create_alliance=False)
        owner = OwnerFactory(corporation=corporation)
        structure = StarbaseFactory(owner=owner)
        # when
        obj = self._render_structure(structure)
        # then
        self.assertEqual(obj["alliance_name"], "")

    def test_should_return_jump_gates(self):
        # given
        structure = JumpGateFactory(
            owner=self.owner, jump_fuel_quantity=5000, eve_solar_system_name="1-PGSG"
        )
        # when
        obj = self._render_structure(
            structure, queryset=Structure.objects.annotate_jump_fuel_quantity()
        )
        # then
        self.assertEqual(obj["region_name"], "Detorid")
        self.assertEqual(obj["solar_system_name"], "1-PGSG")
        # self.assertEqual(
        #     obj["structure_name_and_tags"], "1-PGSG &gt;&gt; A-C5TC - Test Jump Gate"
        # )
        self.assertEqual(obj["jump_fuel_quantity"], 5000)


class TestPocoListSerializer(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        alliance = EveAllianceInfoFactory(
            alliance_name="Wayne Enterprises", alliance_ticker="WYE"
        )
        corporation = EveCorporationInfoFactory(
            corporation_name="Wayne Technologies", alliance=alliance
        )
        cls.character = EveCharacterFactory(corporation=corporation)
        cls.user = UserMainDefaultFactory(main_character__character=cls.character)
        cls.owner = OwnerFactory(user=cls.user, are_pocos_public=True)

    def _render_structure(self, structure: Structure, queryset=None) -> dict:
        """Return rendered data row for a structure."""
        request = self.factory.get("/")
        request.user = self.user
        my_queryset = queryset or Structure.objects.all()
        data = PocoListSerializer(
            queryset=my_queryset, request=request, character=self.character
        ).to_list()
        obj = to_dict(data)[structure.id]
        return obj

    def test_should_render_poco_correctly(self):
        # given
        structure = PocoFactory(
            owner=self.owner,
            eve_planet_name="Amamake V",
            poco_details__corporation_tax_rate=0.01,
        )
        # when
        obj = self._render_structure(structure)
        # then
        self.assertEqual(obj["alliance_name"], "Wayne Enterprises [WYE]")
        self.assertIn("Hed", obj["constellation"])
        self.assertEqual(obj["corporation_name"], "Wayne Technologies")
        self.assertEqual(obj["has_access_str"], "yes")
        self.assertEqual(obj["region"], "Heimatar")
        self.assertEqual(obj["planet_name"], "Amamake V")
        self.assertEqual(obj["planet_type_name"], "Barren")
        self.assertEqual(obj["solar_system"], "Amamake")
        self.assertEqual(obj["space_type"], "lowsec")
        self.assertEqual(obj["tax"]["sort"], 1.0)
