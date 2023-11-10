from typing import List

from django.test import RequestFactory

from app_utils.testing import NoSocketsTestCase

from structures.core.serializers import PocoListSerializer, StructureListSerializer
from structures.models import Structure
from structures.tests.testdata.factories_2 import (
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
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        load_eveuniverse()
        user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=user)
        cls.request = cls.factory.get("/")
        cls.request.user = user

    def test_should_show_not_reinforced_for_structure(self):
        # given
        structure = StructureFactory(owner=self.owner)
        # when
        data = StructureListSerializer(
            queryset=Structure.objects.all(), request=self.request
        ).to_list()
        # then
        obj = to_dict(data)[structure.id]
        self.assertFalse(obj["is_reinforced"])

    def test_should_show_reinforced_for_structure(self):
        # given
        structure = StructureFactory(
            owner=self.owner, state=Structure.State.ARMOR_REINFORCE
        )
        # when
        data = StructureListSerializer(
            queryset=Structure.objects.all(), request=self.request
        ).to_list()
        # then
        obj = to_dict(data)[structure.id]
        self.assertTrue(obj["is_reinforced"])

    def test_should_show_not_reinforced_for_starbase(self):
        # given
        structure = StarbaseFactory(owner=self.owner)
        # when
        data = StructureListSerializer(
            queryset=Structure.objects.all(), request=self.request
        ).to_list()
        # then
        obj = to_dict(data)[structure.id]
        self.assertFalse(obj["is_reinforced"])

    def test_should_show_reinforced_for_starbase(self):
        # given
        structure = StarbaseFactory(
            owner=self.owner, state=Structure.State.POS_REINFORCED
        )
        # when
        data = StructureListSerializer(
            queryset=Structure.objects.all(), request=self.request
        ).to_list()
        # then
        obj = to_dict(data)[structure.id]
        self.assertTrue(obj["is_reinforced"])


class TestPocoListSerializer(NoSocketsTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        load_eveuniverse()
        user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=user)
        cls.request = cls.factory.get("/")
        cls.request.user = user

    def test_should_extract_planet_type(self):
        # given
        structure = PocoFactory(owner=self.owner)
        # when
        data = PocoListSerializer(
            queryset=Structure.objects.all(), request=self.request
        ).to_list()
        # then
        obj = to_dict(data)[structure.id]
        self.assertEqual(obj["planet_type_name"], "Barren")
