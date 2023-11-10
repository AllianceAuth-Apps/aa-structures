from django.test import TestCase
from django.urls import reverse

from app_utils.testing import add_character_to_user

from ..testdata.factories import (
    EveCharacterFactory,
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
        character = EveCharacterFactory(character_name="Bruce Wayne")
        cls.user = UserMainBasicFactory(main_character__character=character)
        cls.owner = OwnerFactory(are_pocos_public=True)
        cls.alt_character = EveCharacterFactory(character_name="Peter Parker")
        add_character_to_user(cls.user, cls.alt_character)

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
        characters = {obj["character_name"] for obj in response.context["characters"]}
        self.assertEqual(characters, {"Bruce Wayne", "Peter Parker"})
