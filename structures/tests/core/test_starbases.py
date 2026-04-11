from typing import NamedTuple, Optional

from eveuniverse.models import EveType

from app_utils.testing import NoSocketsTestCase

from structures.core import starbases
from structures.tests.testdata.factories import (
    CitadelTypeFactory,
    CustomsOfficeTypeFactory,
    StarbaseTypeFactory,
)


class TestStarbases(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.type_citadel = CitadelTypeFactory()
        cls.type_poco = CustomsOfficeTypeFactory()
        cls.type_starbase = StarbaseTypeFactory()

    def test_is_starbase(self):
        self.assertFalse(starbases.is_starbase(self.type_citadel))
        self.assertFalse(starbases.is_starbase(self.type_poco))
        self.assertTrue(starbases.is_starbase(self.type_starbase))

    def test_starbase_fuel_consumption_per_hour(self):
        class Case(NamedTuple):
            eve_type: EveType
            want: Optional[int]

        cases = [
            Case(
                StarbaseTypeFactory(id=16213, name="Caldari Control Tower"),
                40,
            ),
            Case(
                StarbaseTypeFactory(id=20061, name="Caldari Control Tower Medium"),
                20,
            ),
            Case(
                StarbaseTypeFactory(id=20062, name="Caldari Control Tower Small"),
                10,
            ),
            Case(CitadelTypeFactory(), None),
        ]

        for tc in cases:
            with self.subTest(name=tc.eve_type.name):
                self.assertEqual(starbases.fuel_per_hour(tc.eve_type), tc.want)

    def test_starbase_size(self):
        class Case(NamedTuple):
            eve_type: EveType
            want: Optional[starbases.StarbaseSize]

        cases = [
            Case(
                StarbaseTypeFactory(id=16213, name="Caldari Control Tower"),
                starbases.StarbaseSize.LARGE,
            ),
            Case(
                StarbaseTypeFactory(id=20061, name="Caldari Control Tower Medium"),
                starbases.StarbaseSize.MEDIUM,
            ),
            Case(
                StarbaseTypeFactory(id=20062, name="Caldari Control Tower Small"),
                starbases.StarbaseSize.SMALL,
            ),
            Case(CitadelTypeFactory(), None),
        ]

        for tc in cases:
            with self.subTest(name=tc.eve_type.name):
                self.assertEqual(starbases.starbase_size(tc.eve_type), tc.want)


class TestStarbasesFuelDuration(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_can_calculate_for_large_tower(self):
        # given
        large_tower_type = StarbaseTypeFactory(name="Caldari Control Tower")
        # when
        result = starbases.fuel_duration(
            starbase_type=large_tower_type, fuel_quantity=80
        )
        # then
        self.assertEqual(result, 7200)

    def test_can_calculate_for_large_tower_with_sov(self):
        # given
        large_tower_type = StarbaseTypeFactory(name="Caldari Control Tower")
        # when
        result = starbases.fuel_duration(
            starbase_type=large_tower_type, fuel_quantity=80, has_sov=True
        )
        # then
        self.assertEqual(result, 9600)

    def test_can_raise_error_when_not_starbase_type(self):
        # given
        astrahus_type = CitadelTypeFactory()
        # when
        with self.assertRaises(ValueError):
            starbases.fuel_duration(starbase_type=astrahus_type, fuel_quantity=80)
        # given
        astrahus_type = CitadelTypeFactory()
        # when
        with self.assertRaises(ValueError):
            starbases.fuel_duration(starbase_type=astrahus_type, fuel_quantity=80)
        # given
        astrahus_type = CitadelTypeFactory()
        # when
        with self.assertRaises(ValueError):
            starbases.fuel_duration(starbase_type=astrahus_type, fuel_quantity=80)
        with self.assertRaises(ValueError):
            starbases.fuel_duration(starbase_type=astrahus_type, fuel_quantity=80)
        with self.assertRaises(ValueError):
            starbases.fuel_duration(starbase_type=astrahus_type, fuel_quantity=80)
