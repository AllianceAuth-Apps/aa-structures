from django.test import TestCase
from django.urls import reverse

from ..testdata.factories import (
    JumpGateFactory,
    OwnerFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    UserMainBasicFactory,
    UserMainDefaultFactory,
)
from ..testdata.load_eveuniverse import load_eveuniverse


class TestStructureListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_eveuniverse()
        cls.user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=cls.user)

    def test_should_be_able_to_open_page(self):
        # given
        StructureFactory(owner=self.owner)
        PocoFactory(owner=self.owner)
        StarbaseFactory(owner=self.owner)
        JumpGateFactory(owner=self.owner)
        StructureFactory()  # this one will be hidden
        self.client.force_login(self.user)
        # when
        response = self.client.get(reverse("structures:structure_list"))
        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["structures_count"], 2)
        self.assertEqual(response.context["pocos_count"], 1)
        self.assertEqual(response.context["starbases_count"], 1)
        self.assertEqual(response.context["jump_gates_count"], 1)


class TestStatisticsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_eveuniverse()
        cls.user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=cls.user)

    def test_should_be_able_to_open_page(self):
        # given
        StructureFactory(owner=self.owner)
        self.client.force_login(self.user)
        # when
        response = self.client.get(reverse("structures:statistics"))
        # then
        self.assertEqual(response.status_code, 200)
        self.assertIn("last_updated", response.context)


class TestPocoView(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_eveuniverse()
        cls.user = UserMainBasicFactory()
        cls.owner = OwnerFactory(are_pocos_public=True)

    def test_should_be_able_to_open_page(self):
        # given
        PocoFactory(owner=self.owner)
        PocoFactory(owner=self.owner)
        PocoFactory()  # this one will be hidden
        self.client.force_login(self.user)
        # when
        response = self.client.get(reverse("structures:public"))
        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pocos_count"], 2)
