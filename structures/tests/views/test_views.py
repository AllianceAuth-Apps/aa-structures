import datetime as dt
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from eveuniverse.models import EveSolarSystem

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import create_user_from_evecharacter, json_response_to_python

from structures.models import Owner, Structure, Webhook
from structures.views import structures

from ..testdata.factories_2 import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    JumpGateFactory,
    OwnerFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    UserMainBasicFactory,
    UserMainDefaultFactory,
)
from ..testdata.helpers import create_structures, load_entities, set_owner_character
from ..testdata.load_eveuniverse import load_eveuniverse
from .utils import json_response_to_dict

VIEWS_PATH = "structures.views.structures"
OWNERS_PATH = "structures.models.owners"


class TestStructureListDataSerialization(TestCase):
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
        character = EveCharacterFactory(corporation=corporation)
        cls.user = UserMainDefaultFactory(main_character__character=character)
        cls.owner = OwnerFactory(corporation=corporation)

    def test_should_serialize_data_correctly(self):
        # given
        eve_solar_system = EveSolarSystem.objects.get(name="Amamake")
        structure = StructureFactory(
            owner=self.owner,
            eve_solar_system=eve_solar_system,
            eve_type_name="Astrahus",
        )
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "structures")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        obj = data[structure.id]
        self.assertEqual(obj["alliance_name"], "Wayne Enterprises [WYE]")
        self.assertEqual(obj["corporation_name"], "Wayne Technologies")
        self.assertEqual(obj["region_name"], "Heimatar")
        self.assertEqual(obj["solar_system_name"], "Amamake")
        self.assertEqual(obj["group_name"], "Citadel")
        self.assertEqual(obj["category_name"], "Structure")
        self.assertFalse(obj["is_starbase"])
        self.assertFalse(obj["is_poco"])
        self.assertEqual(obj["type_name"], "Astrahus")
        self.assertEqual(obj["is_reinforced_str"], "no")
        self.assertEqual(
            obj["fuel_and_power"]["fuel_expires_at"],
            structure.fuel_expires_at.isoformat(),
        )
        self.assertEqual(obj["power_mode_str"], "Full Power")
        self.assertEqual(obj["state_str"], "Shield vulnerable")
        self.assertEqual(obj["core_status_str"], "no")
        self.assertEqual(obj["details"], "")

    def test_should_return_jump_gates(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        structure = JumpGateFactory(
            owner=self.owner, jump_fuel_quantity=5000, eve_solar_system_name="1-PGSG"
        )
        # when
        response = structures.structure_list_data(request, "jump_gates")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        obj = data[structure.id]
        self.assertEqual(obj["region_name"], "Detorid")
        self.assertEqual(obj["solar_system_name"], "1-PGSG")
        # self.assertEqual(
        #     obj["structure_name_and_tags"], "1-PGSG &gt;&gt; A-C5TC - Test Jump Gate"
        # )
        self.assertEqual(obj["jump_fuel_quantity"], 5000)


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

    def test_should_return_pocos_only(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.structure_list_data(request, "pocos")
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.poco.id})

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
            {self.structure.id, self.poco.id, self.starbase.id, self.jump_gate.id},
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
        create_structures()

    def _structure_list_data_view(self, user) -> dict:
        """helper method:  makes the request to the view
        and returns response as dict for the given user
        """
        request = self.factory.get("/")
        request.user = user
        response = structures.structure_list_data(request, "all")
        self.assertEqual(response.status_code, 200)
        return json_response_to_dict(response)

    def test_should_show_no_structures(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(set(structure_ids), set())

    def test_should_show_own_corporation_only_1(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(
            set(structure_ids),
            {
                1000000000001,
                1000000000002,
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

    def test_should_show_own_corporation_only_2(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(set(structure_ids), {1000000000003, 1000000000004})

    def test_should_show_own_alliance_only_1(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_alliance_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(
            set(structure_ids),
            {
                1000000000001,
                1000000000002,  # only for alliance
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

    def test_should_show_own_alliance_only_2(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_alliance_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(set(structure_ids), {1000000000003, 1000000000004})

    def test_should_show_all_structures(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(
            set(structure_ids),
            {
                1000000000001,
                1000000000002,
                1000000000003,  # only for all
                1000000000004,
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

    def test_should_show_unanchoring_status(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_unanchoring_status", user
        )
        # when
        data = self._structure_list_data_view(user)
        # then
        structure = data[1000000000003]
        self.assertIn("Unanchoring until", structure["state_details"])

    def test_should_not_show_unanchoring_status(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        # when
        data = self._structure_list_data_view(user)
        # then
        structure = data[1000000000003]
        self.assertNotIn("Unanchoring until", structure["state_details"])


class TestStructureListFilters(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        create_structures()
        cls.user, cls.owner = set_owner_character(character_id=1001)
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.basic_access", cls.user
        )
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", cls.user
        )
        cls.factory = RequestFactory()

    @patch(VIEWS_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", True)
    def test_default_filter_enabled(self):
        request = self.factory.get(reverse("structures:index"))
        request.user = self.user
        response = structures.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/structures/list?tags=tag_a")

    @patch(VIEWS_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", False)
    def test_default_filter_disabled(self):
        request = self.factory.get(reverse("structures:index"))
        request.user = self.user
        response = structures.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/structures/list")

    def test_list_filter_by_tag_1(self):
        # no filter
        request = self.factory.get("/")
        request.user = self.user
        response = structures.structure_list_data(request, "all")
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response)
        self.assertSetEqual(
            set(data.keys()),
            {
                1000000000001,
                1000000000002,
                1000000000003,
                1000000000004,
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

        # filter for tag_c
        request = self.factory.get("/?tags=tag_c")
        request.user = self.user
        response = structures.structure_list_data(request, "all")
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response)
        self.assertSetEqual(set(data.keys()), {1000000000002, 1000000000003})

        # filter for tag_b
        request = self.factory.get("/?tags=tag_b")
        request.user = self.user
        response = structures.structure_list_data(request, "all")
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response)
        self.assertSetEqual(set(data.keys()), {1000000000003})

        # filter for tag_c, tag_b
        request = self.factory.get("/?tags=tag_c,tag_b")
        request.user = self.user
        response = structures.structure_list_data(request, "all")
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response)
        self.assertSetEqual(set(data.keys()), {1000000000002, 1000000000003})

    def test_call_with_raw_tags(self):
        request = self.factory.get("/?tags=tag_c,tag_b")
        request.user = self.user
        response = structures.structure_list(request)
        self.assertEqual(response.status_code, 200)

    def test_set_tags_filter(self):
        request = self.factory.post("/", data={"tag_b": True, "tag_c": True})
        request.user = self.user
        response = structures.structure_list(request)
        self.assertEqual(response.status_code, 302)
        parts = urlparse(response.url)
        path = parts[2]
        query_dict = parse_qs(parts[4])
        self.assertEqual(path, reverse("structures:structure_list"))
        self.assertIn("tags", query_dict)
        params = query_dict["tags"][0].split(",")
        self.assertSetEqual(set(params), {"tag_c", "tag_b"})


class TestStructurePowerModes(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_entities()
        load_eveuniverse()

    def setUp(self):
        create_structures(dont_load_entities=True)
        self.user, self.owner = set_owner_character(character_id=1001)
        AuthUtils.add_permission_to_user_by_name("structures.basic_access", self.user)
        AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", self.user
        )

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
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = now() + dt.timedelta(hours=1)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Full Power")
        self.assertEqual(
            parse_datetime(my_structure["fuel_and_power"]["fuel_expires_at"]),
            structure.fuel_expires_at,
        )
        self.assertIn("Full Power", my_structure["fuel_and_power"]["display"])

    def test_low_power(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.last_online_at = now() - dt.timedelta(days=3)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Low Power")
        self.assertIn("Low Power", my_structure["fuel_and_power"]["display"])

    def test_abandoned(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.last_online_at = now() - dt.timedelta(days=7, seconds=1)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Abandoned")
        self.assertIn("Abandoned", my_structure["fuel_and_power"]["display"])

    def test_maybe_abandoned(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.last_online_at = None
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Abandoned?")
        self.assertIn("Abandoned?", my_structure["fuel_and_power"]["display"])

    def test_poco(self):
        structure_id = 1200000000003
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "")
        self.assertEqual(my_structure["fuel_and_power"]["display"], "")

    def test_starbase_online(self):
        structure_id = 1300000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = now() + dt.timedelta(hours=1)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "")
        self.assertEqual(
            parse_datetime(my_structure["fuel_and_power"]["fuel_expires_at"]),
            structure.fuel_expires_at,
        )

    def test_starbase_offline(self):
        structure_id = 1300000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "")
        self.assertIn("-", my_structure["fuel_and_power"]["display"])


class TestAddStructureOwner(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        load_entities([EveCorporationInfo, EveAllianceInfo, EveCharacter, Webhook])
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=["structures.basic_access", "structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        cls.character = cls.character_ownership.character
        cls.factory = RequestFactory()

    def _add_structure_owner(self, token=None, user=None):
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
    def test_should_add_new_structure_owner_and_notify_admins(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # when
        response = self._add_structure_owner()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(mock_notify_admins.called)
        owner = Owner.objects.first()
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertEqual(owner.webhooks.first().name, "Test Webhook 1")
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_should_add_character_to_existing_structure_owner_and_reactive(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        owner = Owner.objects.create(
            corporation=EveCorporationInfo.objects.get(corporation_id=2102),
            is_active=False,
        )
        _, character_ownership_1011 = create_user_from_evecharacter(
            1011,
            permissions=["structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        owner.add_character(character_ownership_1011)
        user_1102, character_ownership_1102 = create_user_from_evecharacter(
            1102,
            permissions=["structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        # when
        response = self._add_structure_owner(user=user_1102)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_update_all_for_owner.delay.called)
        owner.refresh_from_db()
        self.assertSetEqual(
            {character_ownership_1011.pk, character_ownership_1102.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertTrue(owner.is_active)

    @patch(VIEWS_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(VIEWS_PATH + ".tasks.update_all_for_owner")
    @patch(VIEWS_PATH + ".notify_admins")
    @patch(VIEWS_PATH + ".messages")
    def test_should_add_new_structure_owner_and_not_notify_admins(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # when
        response = self._add_structure_owner()
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
        Webhook.objects.filter(name="Test Webhook 1").update(is_default=False)
        # when
        response = self._add_structure_owner()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_notify_admins.called)
        my_owner = Owner.objects.get(
            characters__character_ownership=self.character_ownership
        )
        self.assertIsNone(my_owner.webhooks.first())
        self.assertTrue(mock_update_all_for_owner.delay.called)

        # webhook.is_default = True
        # webhook.save()

    @patch(VIEWS_PATH + ".messages")
    def test_should_report_error_when_token_does_not_belong_to_user(
        self, mock_messages
    ):
        # given
        other_user, _ = create_user_from_evecharacter(
            1011,
            permissions=["structures.basic_access", "structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        # when
        my_token = other_user.token_set.first()
        response = self._add_structure_owner(token=my_token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.error.called)


class TestStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        create_structures()
        my_user, _ = set_owner_character(character_id=1001)
        AuthUtils.add_permission_to_user_by_name("structures.basic_access", my_user)
        cls.factory = RequestFactory()

    def test_view_service_status_ok(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.notifications_last_update_at = now()
            owner.forwarding_last_update_at = now()
            owner.assets_last_update_at = now()
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = structures.service_status(request)
        self.assertEqual(response.status_code, 200)

    @patch(OWNERS_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_structures(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now() - dt.timedelta(minutes=31)
            owner.notifications_last_update_at = now()
            owner.forwarding_last_update_at = now()
            owner.assets_last_update_at = now()
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = structures.service_status(request)
        self.assertEqual(response.status_code, 500)

    @patch(OWNERS_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_notifications(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.notifications_last_update_at = now() - dt.timedelta(minutes=31)
            owner.forwarding_last_update_at = now()
            owner.assets_last_update_at = now()
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = structures.service_status(request)
        self.assertEqual(response.status_code, 500)

    @patch(OWNERS_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_forwarding(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.notifications_last_update_at = now()
            owner.forwarding_last_update_at = now() - dt.timedelta(minutes=31)
            owner.assets_last_update_at = now()
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = structures.service_status(request)
        self.assertEqual(response.status_code, 500)

    @patch(OWNERS_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_assets(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.notifications_last_update_at = now()
            owner.forwarding_last_update_at = now()
            owner.assets_last_update_at = now() - dt.timedelta(minutes=31)
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = structures.service_status(request)
        self.assertEqual(response.status_code, 500)


class TestPocoListData(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainBasicFactory()
        cls.main = cls.user.profile.main_character
        owner = OwnerFactory(are_pocos_public=True)
        cls.poco_public = PocoFactory(
            owner=owner,
            eve_planet_name="Amamake V",
            poco_details__allow_access_with_standings=True,
            poco_details__neutral_standing_tax_rate=0.01,
        )
        cls.poco_non_public = PocoFactory()

    def test_should_return_public_pocos_only(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.public_poco_list_data(request, self.main.character_id)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.poco_public.id})

    def test_should_return_correct_data_for_poco(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = structures.public_poco_list_data(request, self.main.character_id)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        obj = data[self.poco_public.id]
        self.assertEqual(obj["region"], "Heimatar")
        self.assertEqual(obj["solar_system"], "Amamake")
        self.assertEqual(obj["planet_name"], "Amamake V")
        self.assertEqual(obj["planet_type_name"], "Barren")
        self.assertEqual(obj["space_type"], "lowsec")
        self.assertEqual(obj["has_access_str"], "yes")
        self.assertEqual(obj["tax"]["sort"], 1.0)


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
