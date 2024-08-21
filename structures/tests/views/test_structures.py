import datetime as dt
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from allianceauth.eveonline.models import EveCharacter
from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import json_response_to_python

import structures.views.status
from structures.models import Owner, Structure
from structures.tests.testdata.factories import (
    EveCharacterFactory,
    JumpGateFactory,
    OwnerFactory,
    PocoFactory,
    SkyhookFactory,
    StarbaseFactory,
    StructureFactory,
    StructureTagFactory,
    UserMainDefaultFactory,
    UserMainDefaultOwnerFactory,
    WebhookFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse
from structures.views import structures

from .utils import json_response_to_dict

VIEWS_PATH = "structures.views.structures"
OWNERS_PATH = "structures.models.owners"


@patch(VIEWS_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", False)
class TestIndexRedirect(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    def test_should_redirect_to_public_view(self):
        # given
        user = UserMainFactory(
            permissions__=[
                "structures.basic_access",
            ],
        )
        request = self.factory.get("/")
        request.user = user

        # when
        response = structures.index(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:public"))

    def test_should_redirect_to_structure_list_view_1(self):
        # given
        user = UserMainFactory(
            permissions__=[
                "structures.basic_access",
                "structures.view_corporation_structures",
            ],
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.index(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:structure_list"))

    def test_should_redirect_to_structure_list_view_2(self):
        # given
        user = UserMainFactory(
            permissions__=[
                "structures.basic_access",
                "structures.view_alliance_structures",
            ],
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.index(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:structure_list"))

    def test_should_redirect_to_structure_list_view_3(self):
        # given
        user = UserMainFactory(
            permissions__=[
                "structures.basic_access",
                "structures.view_all_structures",
            ],
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.index(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:structure_list"))


class TestIndexTagFilter(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        StructureTagFactory(name="tag_a", is_default=True)
        cls.user = UserMainDefaultFactory()

    @patch(VIEWS_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", True)
    def test_default_filter_enabled(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.index(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/structures/list?tags=tag_a")

    @patch(VIEWS_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", False)
    def test_default_filter_disabled(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.index(request)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/structures/list")


class TestStructureListDataFilterVariant(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainDefaultFactory()
        owner = OwnerFactory(user=cls.user)
        cls.structure = StructureFactory(owner=owner)
        cls.poco = PocoFactory(owner=owner)
        cls.skyhook = SkyhookFactory(owner=owner)
        cls.starbase = StarbaseFactory(owner=owner)
        cls.jump_gate = JumpGateFactory(owner=owner)

    def test_should_return_upwell_structures_only(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "structures")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.structure.id, self.jump_gate.id})

    def test_should_return_orbitals_only(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "orbitals")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.poco.id, self.skyhook.id})

    def test_should_return_starbases_only(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "starbases")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.starbase.id})

    def test_should_return_jump_gates(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "jump_gates")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.jump_gate.id})

    def test_should_return_all_structures(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(
            structure_ids,
            {
                self.structure.id,
                self.poco.id,
                self.starbase.id,
                self.jump_gate.id,
                self.skyhook.id,
            },
        )

    def test_should_raise_error_when_invalid_variant_requested(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when/then
        with self.assertRaises(ValueError):
            structures.structure_list_data(request, "invalid")

    def test_should_not_return_structure_from_different_corporations(self):
        # given
        other_structure = StructureFactory()
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "structures")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertNotIn(other_structure.id, structure_ids)


class TestStructureListDataPermissions(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()

    def test_should_show_structures_from_own_corporation_only(self):
        # given
        user = UserMainFactory(
            permissions__=[
                "structures.basic_access",
                "structures.view_corporation_structures",
            ],
        )
        owner = OwnerFactory(user=user)
        structure_own_corp = StructureFactory(owner=owner)
        StructureFactory()  # structure with a different corporation
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {structure_own_corp.id})

    def test_should_show_unanchoring_status(self):
        # given
        user = UserMainFactory(
            permissions__=[
                "structures.basic_access",
                "structures.view_all_structures",
                "structures.view_all_unanchoring_status",
            ],
        )
        owner = OwnerFactory(user=user)
        structure = StructureFactory(
            owner=owner, unanchors_at=now() + dt.timedelta(days=3)
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure = data[structure.id]
        self.assertIn("Unanchoring until", structure["state_details"])

    def test_should_not_show_unanchoring_status(self):
        # given
        user = UserMainFactory(
            permissions__=["structures.basic_access", "structures.view_all_structures"],
        )
        owner = OwnerFactory(user=user)
        structure = StructureFactory(
            owner=owner, unanchors_at=now() + dt.timedelta(days=3)
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure = data[structure.id]
        self.assertNotIn("Unanchoring until", structure["state_details"])


class TestStructureListTagFilters(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.factory = RequestFactory()
        cls.user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=cls.user)
        tag_b = StructureTagFactory(name="tag_b")
        tag_c = StructureTagFactory(name="tag_c")
        cls.structure_1 = StructureFactory(
            owner=cls.owner, tags=[tag_b], id=1000000000001
        )
        cls.structure_2 = StructureFactory(
            owner=cls.owner, tags=[tag_c], id=1000000000002
        )
        cls.structure_3 = StructureFactory(
            owner=cls.owner, tags=[tag_b, tag_c], id=1000000000003
        )
        cls.structure_4 = StructureFactory(owner=cls.owner, id=1000000000004)

    def test_list_filter_by_tag_with_no_filter(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        self.assertSetEqual(
            set(data.keys()),
            {
                self.structure_1.id,
                self.structure_2.id,
                self.structure_3.id,
                self.structure_4.id,
            },
        )

    def test_list_filter_by_one_tag(self):
        # given
        request = self.factory.get("/?tags=tag_b")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        self.assertSetEqual(
            set(data.keys()), {self.structure_1.id, self.structure_3.id}
        )

    def test_list_filter_by_two_tags(self):
        # given
        request = self.factory.get("/?tags=tag_b,tag_c")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "all")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        self.assertSetEqual(
            set(data.keys()),
            {self.structure_1.id, self.structure_2.id, self.structure_3.id},
        )

    def test_call_with_raw_tags(self):
        # given
        request = self.factory.get("/?tags=tag_c,tag_b")
        request.user = self.user
        # when
        response = structures.structure_list(request)
        # then
        self.assertEqual(response.status_code, 200)

    def test_set_tags_filter(self):
        # given
        request = self.factory.post("/", data={"tag_b": True, "tag_c": True})
        request.user = self.user
        # when
        response = structures.structure_list(request)
        # then
        self.assertEqual(response.status_code, 302)
        parts = urlparse(response.url)
        path = parts[2]
        query_dict = parse_qs(parts[4])
        self.assertEqual(path, reverse("structures:structure_list"))
        self.assertIn("tags", query_dict)
        params = query_dict["tags"][0].split(",")
        self.assertSetEqual(set(params), {"tag_c", "tag_b"})

    def test_handle_post_with_no_tags(self):
        # given
        request = self.factory.post("/")
        request.user = self.user
        # when
        response = structures.structure_list(request)
        # then
        self.assertEqual(response.status_code, 302)
        parts = urlparse(response.url)
        path = parts[2]
        query_dict = parse_qs(parts[4])
        self.assertEqual(path, reverse("structures:structure_list"))
        self.assertNotIn("tags", query_dict)


class TestStructurePowerModes(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user)

    def display_data_for_structure(self, structure_id: int):
        request = self.factory.get("/")
        request.user = self.user
        response = structures.structure_list_data(request, "all")
        self.assertEqual(response.status_code, 200)

        data = json_response_to_python(response)["data"]
        for row in data:
            if row["id"] == structure_id:
                return row

        return None

    def test_full_power(self):
        # given
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=1)
        )
        # when
        obj = self.display_data_for_structure(structure.id)
        # then
        self.assertEqual(obj["power_mode_str"], "Full Power")
        self.assertEqual(
            parse_datetime(obj["fuel_and_power"]["fuel_expires_at"]),
            structure.fuel_expires_at,
        )
        self.assertIn("Full Power", obj["fuel_and_power"]["display"])

    def test_low_power(self):
        # given
        structure = StructureFactory(
            owner=self.owner,
            fuel_expires_at=None,
            last_online_at=now() - dt.timedelta(days=3),
        )
        # when
        obj = self.display_data_for_structure(structure.id)
        # then
        self.assertEqual(obj["power_mode_str"], "Low Power")
        self.assertIn("Low Power", obj["fuel_and_power"]["display"])

    def test_abandoned(self):
        # given
        structure = StructureFactory(
            owner=self.owner,
            fuel_expires_at=None,
            last_online_at=now() - dt.timedelta(days=7, seconds=1),
        )
        # when
        obj = self.display_data_for_structure(structure.id)
        # then
        self.assertEqual(obj["power_mode_str"], "Abandoned")
        self.assertIn("Abandoned", obj["fuel_and_power"]["display"])

    def test_maybe_abandoned(self):
        # given
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=None, last_online_at=None
        )
        # when
        obj = self.display_data_for_structure(structure.id)
        # then
        self.assertEqual(obj["power_mode_str"], "Abandoned?")
        self.assertIn("Abandoned?", obj["fuel_and_power"]["display"])

    def test_poco(self):
        # given
        structure = PocoFactory(owner=self.owner)
        # when
        obj = self.display_data_for_structure(structure.id)
        self.assertEqual(obj["power_mode_str"], "")
        self.assertEqual(obj["fuel_and_power"]["display"], "")

    def test_starbase_online(self):
        # given
        structure = StarbaseFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=1)
        )
        # when
        obj = self.display_data_for_structure(structure.id)
        self.assertEqual(obj["power_mode_str"], "")
        self.assertEqual(
            parse_datetime(obj["fuel_and_power"]["fuel_expires_at"]),
            structure.fuel_expires_at,
        )

    def test_starbase_offline(self):
        # given
        structure = StarbaseFactory(
            owner=self.owner, fuel_expires_at=None, state=Structure.State.POS_OFFLINE
        )
        # when
        obj = self.display_data_for_structure(structure.id)
        # then
        self.assertEqual(obj["power_mode_str"], "")
        self.assertIn("-", obj["fuel_and_power"]["display"])


class TestAddStructureOwner(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainDefaultOwnerFactory()
        cls.character: EveCharacter = cls.user.profile.main_character
        cls.character_ownership = cls.character.character_ownership

    def _add_structure_owner_view(self, token=None, user=None):
        # given
        request = self.factory.get(reverse("structures:add_structure_owner"))
        if not user:
            user = self.user
        if not token:
            token = user.token_set.first()
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = structures.add_structure_owner.__wrapped__.__wrapped__.__wrapped__
        # when
        return orig_view(request, token)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", True)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_should_add_new_owner_and_notify_admins(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        webhook = WebhookFactory(is_default=True)
        # when
        response = self._add_structure_owner_view()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(mock_notify_admins.called)
        new_owner = Owner.objects.first()
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(new_owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertIn(webhook, new_owner.webhooks.all())
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_should_add_new_owner_and_not_notify_admins(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # when
        response = self._add_structure_owner_view()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        owner = Owner.objects.first()
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_notify_admins.called)
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_should_add_structure_owner_with_no_default_webhook(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        WebhookFactory(is_default=False)
        # when
        response = self._add_structure_owner_view()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_notify_admins.called)
        new_owner = Owner.objects.get(
            characters__character_ownership=self.character_ownership
        )
        self.assertFalse(new_owner.webhooks.exists())
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(VIEWS_PATH + ".messages")
    def test_should_report_error_when_token_does_not_belong_to_user(
        self, mock_messages
    ):
        # given
        other_user = UserMainDefaultOwnerFactory()
        # when
        my_token = other_user.token_set.first()
        response = self._add_structure_owner_view(token=my_token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.error.called)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_should_add_another_character_to_existing_owner_and_reactivate(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        owner = OwnerFactory(
            user=self.user, characters=[self.character], is_active=False
        )
        character_2 = EveCharacterFactory(corporation=owner.corporation)
        user_2 = UserMainDefaultOwnerFactory(main_character__character=character_2)
        # when
        response = self._add_structure_owner_view(user=user_2)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_update_all_for_owner.delay.called)
        owner.refresh_from_db()
        character_ownerships = set(
            owner.characters.values_list("character_ownership", flat=True)
        )
        self.assertSetEqual(
            {self.character_ownership.pk, character_2.character_ownership.pk},
            character_ownerships,
        )
        self.assertTrue(owner.is_active)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_can_readd_same_character(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        owner = OwnerFactory(characters=[self.character])
        owner_character = owner.characters.first()
        # when
        response = self._add_structure_owner_view(user=self.user)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        owner.refresh_from_db()
        character_ownerships = set(
            owner.characters.values_list("character_ownership", flat=True)
        )
        self.assertSetEqual(
            {self.character_ownership.pk, owner_character.character_ownership.pk},
            character_ownerships,
        )

    # @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    # @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    # @patch(VIEWS_PATH + ".notify_admins")
    # @patch(VIEWS_PATH + ".messages")
    # def test_should_reenable_character_when_re_adding(
    #     self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    # ):
    #     # given
    #     owner = OwnerFactory(characters=[self.character])
    #     owner_character: OwnerCharacter = owner.characters.first()
    #     owner_character.is_enabled = False
    #     owner_character.save()
    #     # when
    #     response = self._add_structure_owner_view(user=self.user)
    #     # then
    #     self.assertEqual(response.status_code, 302)
    #     self.assertEqual(response.url, reverse("structures:index"))
    #     owner.refresh_from_db()
    #     character_ownerships = set(
    #         owner.characters.values_list("character_ownership", flat=True)
    #     )
    #     self.assertSetEqual(
    #         {self.character_ownership.pk, owner_character.character_ownership.pk},
    #         character_ownerships,
    #     )
    #     owner_character.refresh_from_db()
    #     self.assertTrue(owner_character.is_enabled)


class TestStructureFittingModal(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.character = EveCharacterFactory()
        owner = OwnerFactory(corporation=cls.character.corporation)
        cls.structure = StructureFactory(owner=owner)

    def test_should_have_access_to_fitting(self):
        # given
        user = UserMainFactory(
            main_character__character=self.character,
            permissions__=[
                "structures.basic_access",
                "structures.view_corporation_structures",
                "structures.view_structure_fit",
            ],
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.structure_details(request, self.structure.id)
        # then
        self.assertEqual(response.status_code, 200)

    def test_should_not_have_access_to_fitting(self):
        # given
        user = UserMainFactory(
            main_character__character=self.character,
            permissions__=[
                "structures.basic_access",
                "structures.view_corporation_structures",
            ],
        )
        request = self.factory.get("/")
        request.user = user
        # when
        response = structures.structure_details(request, self.structure.id)
        # then
        self.assertEqual(response.status_code, 302)


class TestDetailsModal(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainDefaultFactory()
        cls.owner = OwnerFactory(user=cls.user)

    def test_should_load_poco_detail(self):
        # given
        structure = PocoFactory(owner=self.owner)
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.poco_details(request, structure.id)
        # then
        self.assertEqual(response.status_code, 200)

    def test_should_load_starbase_detail(self):
        # given
        structure = StarbaseFactory(owner=self.owner)
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.starbase_detail(request, structure.id)
        # then
        self.assertEqual(response.status_code, 200)
