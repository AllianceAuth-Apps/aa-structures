import datetime as dt
from unittest.mock import patch

from django.utils.timezone import now
from eveuniverse.models import EveSolarSystem

from app_utils.esi_testing import EsiClientStub, EsiEndpoint
from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import NoSocketsTestCase

from structures.core.notification_types import NotificationType
from structures.models import (
    EveSovereigntyMap,
    EveSpaceType,
    Structure,
    StructureService,
    StructureTag,
    Webhook,
)

from .testdata.factories import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveSovereigntyMapFactory,
    OwnerFactory,
    PocoFactory,
    SkyhookFactory,
    StarbaseFactory,
    StructureFactory,
    StructureTagFactory,
    WebhookFactory,
)
from .testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.managers"
MODULE_PATH_ESI_FETCH = "structures.helpers.esi_fetch"


class TestEveSovereigntyMapManagerUpdateFromEsi(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        endpoints = [
            EsiEndpoint(
                "Sovereignty",
                "get_sovereignty_map",
                data=[
                    {
                        "alliance_id": 3011,
                        "corporation_id": 2011,
                        "system_id": 30000726,
                    },
                    {
                        "alliance_id": 3001,
                        "corporation_id": 2001,
                        "system_id": 30000474,
                        "faction_id": None,
                    },
                    {
                        "alliance_id": 3001,
                        "corporation_id": 2001,
                        "system_id": 30000728,
                        "faction_id": None,
                    },
                    {
                        "alliance_id": None,
                        "corporation_id": None,
                        "system_id": 30000142,
                        "faction_id": None,
                    },
                ],
            )
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(endpoints)

    @patch(MODULE_PATH + ".esi")
    def test_should_create_sov_map_from_scratch(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        # when
        EveSovereigntyMap.objects.update_or_create_all_from_esi()
        # then
        solar_system_ids = EveSovereigntyMap.objects.values_list(
            "solar_system_id", flat=True
        )
        self.assertSetEqual(set(solar_system_ids), {30000726, 30000474, 30000728})

    @patch(MODULE_PATH + ".esi")
    def test_should_update_existing_map(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        EveSovereigntyMapFactory(solar_system_id=30000726, alliance_id=3001)
        # when
        EveSovereigntyMap.objects.update_or_create_all_from_esi()
        # then
        solar_system_ids = EveSovereigntyMap.objects.values_list(
            "solar_system_id", flat=True
        )
        self.assertSetEqual(set(solar_system_ids), {30000726, 30000474, 30000728})
        structure = EveSovereigntyMap.objects.get(solar_system_id=30000726)
        self.assertEqual(structure.corporation_id, 2011)
        self.assertEqual(structure.alliance_id, 3011)
        structure = EveSovereigntyMap.objects.get(solar_system_id=30000474)
        self.assertEqual(structure.corporation_id, 2001)
        self.assertEqual(structure.alliance_id, 3001)
        structure = EveSovereigntyMap.objects.get(solar_system_id=30000728)
        self.assertEqual(structure.corporation_id, 2001)
        self.assertEqual(structure.alliance_id, 3001)


class TestEveSovereigntyMapManagerOther(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.corporation = EveCorporationInfoFactory()
        solar_system = EveSolarSystem.objects.get(name="1-PGSG")
        EveSovereigntyMapFactory(
            corporation=cls.corporation, solar_system_id=solar_system.id
        )

    def test_should_return_alliance_id_for_sov_system_in_null(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="1-PGSG")
        # when/then
        self.assertEqual(
            EveSovereigntyMap.objects.solar_system_sov_alliance_id(solar_system),
            self.corporation.alliance.alliance_id,
        )

    def test_should_return_none_when_no_sov_info_for_null_sec_system(self):
        solar_system = EveSolarSystem.objects.get(name="A-C5TC")
        self.assertIsNone(
            EveSovereigntyMap.objects.solar_system_sov_alliance_id(solar_system)
        )

    def test_should_return_none_when_system_not_in_null(self):
        solar_system = EveSolarSystem.objects.get(name="Amamake")
        self.assertIsNone(
            EveSovereigntyMap.objects.solar_system_sov_alliance_id(solar_system)
        )

    def test_should_return_true_when_corporation_has_sov_in_null_system(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="1-PGSG")
        # when/then
        self.assertTrue(
            EveSovereigntyMap.objects.corporation_has_sov(
                solar_system, self.corporation
            )
        )

    def test_should_return_false_when_corporation_has_no_sov_in_null_system(self):
        solar_system = EveSolarSystem.objects.get(name="A-C5TC")
        self.assertFalse(
            EveSovereigntyMap.objects.corporation_has_sov(
                solar_system, self.corporation
            )
        )

    def test_should_return_false_when_system_is_not_in_null(self):
        solar_system = EveSolarSystem.objects.get(name="Amamake")
        self.assertFalse(
            EveSovereigntyMap.objects.corporation_has_sov(
                solar_system, self.corporation
            )
        )


@patch(MODULE_PATH + ".esi")
class TestStructureManagerEsi(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        cls.token = cls.owner.fetch_token()
        endpoints = [
            EsiEndpoint(
                "Universe",
                "get_universe_structures_structure_id",
                "structure_id",
                needs_token=True,
                data={
                    "1000000000001": {
                        "corporation_id": cls.owner.corporation.corporation_id,
                        "name": "Amamake - Test Structure Alpha",
                        "position": {
                            "x": 55028384780.0,
                            "y": 7310316270.0,
                            "z": -163686684205.0,
                        },
                        "solar_system_id": 30002537,
                        "type_id": 35832,
                    },
                    "1000000000002": {
                        "corporation_id": 2001,
                        "name": "Amamake - Test Structure Bravo",
                        "position": {
                            "x": -2518743930339.066,
                            "y": -130157937025.56424,
                            "z": -442026427345.6355,
                        },
                        "solar_system_id": 30002537,
                        "type_id": 35835,
                    },
                    "1000000000003": {
                        "corporation_id": 2001,
                        "name": "Amamake - Test Structure Charlie",
                        "position": {
                            "x": -2518743930339.066,
                            "y": -130157937025.56424,
                            "z": -442026427345.6355,
                        },
                        "solar_system_id": 30000476,
                        "type_id": 35832,
                    },
                },
            )
        ]
        cls.esi_client_stub = EsiClientStub.create_from_endpoints(endpoints)

    def test_should_return_object_from_db_if_found(self, mock_esi):
        # given
        endpoints = [
            EsiEndpoint(
                "Universe",
                "get_universe_structures_structure_id",
                "structure_id",
                needs_token=True,
                side_effect=RuntimeError,
            )
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        structure = StructureFactory(owner=self.owner, id=1000000000001, name="Batcave")
        # when
        structure, created = Structure.objects.get_or_create_esi(
            id=1000000000001, token=self.token
        )
        # then
        self.assertFalse(created)
        self.assertEqual(structure.id, 1000000000001)

    def test_can_create_object_from_esi_if_not_found(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        # when
        structure, created = Structure.objects.get_or_create_esi(
            id=1000000000001, token=self.token
        )
        # then
        self.assertTrue(created)
        self.assertEqual(structure.id, 1000000000001)
        self.assertEqual(structure.name, "Test Structure Alpha")
        self.assertEqual(structure.eve_type_id, 35832)
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(structure.position_x, 55028384780.0)
        self.assertEqual(structure.position_y, 7310316270.0)
        self.assertEqual(structure.position_z, -163686684205.0)

    def test_can_update_object_from_esi(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        structure = StructureFactory(owner=self.owner, id=1000000000001, name="Batcave")
        # when
        structure, created = Structure.objects.update_or_create_esi(
            id=1000000000001, token=self.token
        )
        # then
        self.assertFalse(created)
        self.assertEqual(structure.id, 1000000000001)
        self.assertEqual(structure.name, "Test Structure Alpha")

    def test_raises_exception_when_create_fails(self, mock_esi):
        # given
        endpoints = [
            EsiEndpoint(
                "Universe",
                "get_universe_structures_structure_id",
                "structure_id",
                needs_token=True,
                side_effect=RuntimeError,
            )
        ]
        mock_esi.client = EsiClientStub.create_from_endpoints(endpoints)
        # when/then
        with self.assertRaises(RuntimeError):
            Structure.objects.update_or_create_esi(id=1000000000001, token=self.token)

    def test_raises_exception_when_create_without_token(self, mock_esi):
        # given
        mock_esi.client = self.esi_client_stub
        # when
        with self.assertRaises(ValueError):
            Structure.objects.update_or_create_esi(id=987, token=None)


class TestStructureQuerySet(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        cls.structure = StructureFactory(owner=cls.owner)
        cls.poco = PocoFactory(owner=cls.owner)
        cls.starbase = StarbaseFactory(owner=cls.owner)
        cls.skyhook = SkyhookFactory(owner=cls.owner)

    def test_should_return_ids_as_set(self):
        # when
        ids = Structure.objects.ids()
        # then
        self.assertSetEqual(
            ids, {self.structure.id, self.poco.id, self.starbase.id, self.skyhook.id}
        )

    def test_should_filter_upwell_structures(self):
        # when
        result_qs = Structure.objects.filter_upwell_structures()
        # then
        self.assertSetEqual(result_qs.ids(), {self.structure.id})

    def test_should_filter_customs_offices(self):
        # when
        result_qs = Structure.objects.filter_customs_offices()
        # then
        self.assertSetEqual(result_qs.ids(), {self.poco.id})

    def test_should_filter_starbases(self):
        # when
        result_qs = Structure.objects.filter_starbases()
        # then
        self.assertSetEqual(result_qs.ids(), {self.starbase.id})

    def test_should_filter_skyhooks(self):
        # when
        result_qs = Structure.objects.filter_skyhooks()
        # then
        self.assertSetEqual(result_qs.ids(), {self.skyhook.id})


class TestStructureQuerySetVisibleForUser(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        # same alliance
        alliance = EveAllianceInfoFactory()
        cls.corporation_1a = EveCorporationInfoFactory(alliance=alliance)
        owner_1a = OwnerFactory(corporation=cls.corporation_1a)
        cls.structure_1a = StructureFactory(owner=owner_1a, id=1000000000011)
        cls.corporation_1b = EveCorporationInfoFactory(alliance=alliance)
        owner_1b = OwnerFactory(corporation=cls.corporation_1b)
        cls.structure_1b = StructureFactory(owner=owner_1b, id=1000000000012)
        # corp without alliance
        cls.corporation_2 = EveCorporationInfoFactory(alliance=None)
        owner_2 = OwnerFactory(corporation=cls.corporation_2)
        cls.structure_2 = StructureFactory(owner=owner_2, id=1000000000020)

    def test_should_show_structures_from_own_corporation_only_w_alliance(self):
        # given
        character = EveCharacterFactory(corporation=self.corporation_1a)
        user = UserMainFactory(
            main_character__character=character,
            permissions__=[
                "structures.basic_access",
                "structures.view_corporation_structures",
            ],
        )
        # when
        structure_ids = Structure.objects.visible_for_user(user).ids()
        # then
        self.assertSetEqual(structure_ids, {self.structure_1a.id})

    def test_should_show_structures_from_own_corporation_only_wo_alliance(self):
        # given
        character = EveCharacterFactory(corporation=self.corporation_2)
        user = UserMainFactory(
            main_character__character=character,
            permissions__=[
                "structures.basic_access",
                "structures.view_corporation_structures",
            ],
        )
        # when
        structure_ids = Structure.objects.visible_for_user(user).ids()
        # then
        self.assertSetEqual(structure_ids, {self.structure_2.id})

    def test_should_show_structures_from_own_alliance_only_with_corp_in_alliance(self):
        # given
        character = EveCharacterFactory(corporation=self.corporation_1a)
        user = UserMainFactory(
            main_character__character=character,
            permissions__=[
                "structures.basic_access",
                "structures.view_alliance_structures",
            ],
        )
        # when
        structure_ids = Structure.objects.visible_for_user(user).ids()
        # then
        self.assertSetEqual(structure_ids, {self.structure_1a.id, self.structure_1b.id})

    def test_should_show_structures_from_own_alliance_only_with_corp_not_in_alliance(
        self,
    ):
        # given
        character = EveCharacterFactory(corporation=self.corporation_2)
        user = UserMainFactory(
            main_character__character=character,
            permissions__=[
                "structures.basic_access",
                "structures.view_alliance_structures",
            ],
        )
        # when
        structure_ids = Structure.objects.visible_for_user(user).ids()
        # then
        self.assertSetEqual(structure_ids, {self.structure_2.id})

    def test_should_show_all_structures(self):
        # given
        character = EveCharacterFactory(corporation=self.corporation_1a)
        user = UserMainFactory(
            main_character__character=character,
            permissions__=[
                "structures.basic_access",
                "structures.view_all_structures",
            ],
        )
        # when
        structure_ids = Structure.objects.visible_for_user(user).ids()
        # then
        self.assertSetEqual(
            structure_ids,
            {self.structure_1a.id, self.structure_1b.id, self.structure_2.id},
        )

    def test_should_show_no_structures(self):
        # given
        character = EveCharacterFactory(corporation=self.corporation_1a)
        user = UserMainFactory(
            main_character__character=character,
            permissions__=["structures.basic_access"],
        )
        # when
        structure_ids = Structure.objects.visible_for_user(user).ids()
        # then
        self.assertSetEqual(structure_ids, set())


class TestStructureQuerySetFilterTags(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        owner = OwnerFactory()
        tag_a = StructureTagFactory(name="tag_a")
        tag_b = StructureTagFactory(name="tag_b")
        cls.structure_1 = StructureFactory(owner=owner, tags=[tag_a], id=1000000000001)
        cls.structure_2 = StructureFactory(owner=owner, tags=[tag_b], id=1000000000002)
        cls.structure_3 = StructureFactory(
            owner=owner, tags=[tag_a, tag_b], id=1000000000003
        )
        cls.structure_4 = StructureFactory(owner=owner, id=1000000000004)

    def test_should_filter_nothing_when_no_tags_provided(self):
        # when
        result = Structure.objects.filter_tags(tag_names=[]).ids()
        # then
        self.assertSetEqual(
            result,
            {
                self.structure_1.id,
                self.structure_2.id,
                self.structure_3.id,
                self.structure_4.id,
            },
        )

    def test_should_return_structures_which_have_one_tag_only(self):
        # when
        result = Structure.objects.filter_tags(tag_names=["tag_a"]).ids()
        # then
        self.assertSetEqual(result, {self.structure_1.id, self.structure_3.id})

    def test_should_return_structures_which_have_one_of_two_tags_only(self):
        # when
        result = Structure.objects.filter_tags(tag_names=["tag_a", "tag_b"]).ids()
        # then
        self.assertSetEqual(
            result,
            {self.structure_1.id, self.structure_2.id, self.structure_3.id},
        )

    def test_should_return_no_structures_when_tag_not_matches(self):
        # when
        result = Structure.objects.filter_tags(tag_names=["invalid"]).ids()
        # then
        self.assertSetEqual(result, set())


class TestStructureManagerCreateFromDict(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()

    def test_can_create_full(self):
        # given
        structure_data = {
            "fuel_expires": None,
            "name": "Test Structure Alpha",
            "next_reinforce_apply": None,
            "next_reinforce_hour": None,
            "position": {"x": 55028384780.0, "y": 7310316270.0, "z": -163686684205.0},
            "profile_id": 101853,
            "reinforce_hour": 18,
            "services": [
                {
                    "name": "Clone Bay",
                    "state": "online",
                },
                {
                    "name": "Market Hub",
                    "state": "offline",
                },
            ],
            "state": "shield_vulnerable",
            "state_timer_end": None,
            "state_timer_start": None,
            "structure_id": 1000000000001,
            "system_id": 30002537,
            "type_id": 35832,
            "unanchors_at": None,
        }
        # when
        structure, created = Structure.objects.update_or_create_from_dict(
            structure_data, self.owner
        )

        # then
        self.assertTrue(created)
        self.assertEqual(structure.id, 1000000000001)
        self.assertEqual(structure.name, "Test Structure Alpha")
        self.assertEqual(structure.eve_type_id, 35832)
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(structure.owner, self.owner)
        self.assertEqual(structure.position_x, 55028384780.0)
        self.assertEqual(structure.position_y, 7310316270.0)
        self.assertEqual(structure.position_z, -163686684205.0)
        self.assertEqual(structure.reinforce_hour, 18)
        self.assertEqual(structure.state, Structure.State.SHIELD_VULNERABLE)
        self.assertAlmostEqual(
            (now() - structure.created_at).total_seconds(), 0, delta=2
        )
        self.assertAlmostEqual(
            (now() - structure.last_updated_at).total_seconds(), 0, delta=2
        )
        self.assertAlmostEqual(
            (now() - structure.last_online_at).total_seconds(), 0, delta=2
        )
        self.assertEqual(structure.services.count(), 2)
        service_1 = structure.services.get(name="Clone Bay")
        self.assertEqual(service_1.state, StructureService.State.ONLINE)
        service_1 = structure.services.get(name="Market Hub")
        self.assertEqual(service_1.state, StructureService.State.OFFLINE)
        # todo: add more content tests

    def test_can_update_full(self):
        # given
        structure = StructureFactory(
            id=1000000000001,
            owner=self.owner,
            last_updated_at=now() - dt.timedelta(hours=2),
        )
        structure_data = {
            "corporation_id": self.owner.corporation.corporation_id,
            "fuel_expires": None,
            "name": "Test Structure Alpha Updated",
            "next_reinforce_apply": None,
            "next_reinforce_hour": None,
            "position": {"x": 55028384780.0, "y": 7310316270.0, "z": -163686684205.0},
            "profile_id": 101853,
            "reinforce_hour": 18,
            "services": [
                {
                    "name": "Clone Bay",
                    "state": "online",
                },
                {
                    "name": "Market Hub",
                    "state": "offline",
                },
            ],
            "state": "shield_vulnerable",
            "state_timer_end": None,
            "state_timer_start": None,
            "structure_id": 1000000000001,
            "system_id": 30002537,
            "type_id": 35832,
            "unanchors_at": None,
        }

        # when
        structure, created = Structure.objects.update_or_create_from_dict(
            structure_data, self.owner
        )

        # then
        self.assertFalse(created)
        self.assertEqual(structure.id, 1000000000001)
        self.assertEqual(structure.name, "Test Structure Alpha Updated")
        self.assertEqual(structure.eve_type_id, 35832)
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(structure.owner, self.owner)
        self.assertEqual(structure.position_x, 55028384780.0)
        self.assertEqual(structure.position_y, 7310316270.0)
        self.assertEqual(structure.position_z, -163686684205.0)
        self.assertEqual(structure.reinforce_hour, 18)
        self.assertEqual(structure.state, Structure.State.SHIELD_VULNERABLE)
        self.assertAlmostEqual(
            (now() - structure.last_updated_at).total_seconds(), 0, delta=2
        )
        self.assertAlmostEqual(
            (now() - structure.last_online_at).total_seconds(), 0, delta=2
        )

    def test_does_not_update_last_online_when_services_are_offline(self):
        # given
        structure = StructureFactory(
            owner=self.owner, id=1000000000001, last_online_at=None
        )
        structure_data = {
            "fuel_expires": None,
            "name": "Test Structure Alpha Updated",
            "next_reinforce_apply": None,
            "next_reinforce_hour": None,
            "position": {"x": 55028384780.0, "y": 7310316270.0, "z": -163686684205.0},
            "profile_id": 101853,
            "reinforce_hour": 18,
            "services": [
                {
                    "name": "Clone Bay",
                    "state": "offline",
                },
                {
                    "name": "Market Hub",
                    "state": "offline",
                },
            ],
            "state": "shield_vulnerable",
            "state_timer_end": None,
            "state_timer_start": None,
            "structure_id": 1000000000001,
            "system_id": 30002537,
            "type_id": 35832,
            "unanchors_at": None,
        }
        structure, created = Structure.objects.update_or_create_from_dict(
            structure_data, self.owner
        )

        # check structure
        self.assertFalse(created)
        self.assertIsNone(structure.last_online_at)

    def test_can_create_starbase_without_moon(self):
        # given
        structure_data = {
            "structure_id": 1300000000099,
            "name": "Hidden place",
            "system_id": 30002537,
            "type_id": 16213,
            "moon_id": None,
            "position": {"x": 55028384780.0, "y": 7310316270.0, "z": -163686684205.0},
        }

        # when
        structure, created = Structure.objects.update_or_create_from_dict(
            structure_data, self.owner
        )

        # then
        structure: Structure
        self.assertTrue(created)
        self.assertEqual(structure.id, 1300000000099)
        self.assertEqual(structure.eve_type_id, 16213)
        self.assertEqual(structure.eve_solar_system_id, 30002537)
        self.assertEqual(structure.owner, self.owner)
        self.assertEqual(structure.position_x, 55028384780.0)
        self.assertEqual(structure.position_y, 7310316270.0)
        self.assertEqual(structure.position_z, -163686684205.0)
        self.assertEqual(structure.state, Structure.State.UNKNOWN)


class TestStructureTagManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.corporation = EveCorporationInfoFactory()
        solar_system = EveSolarSystem.objects.get(name="1-PGSG")
        EveSovereigntyMapFactory(
            corporation=cls.corporation, solar_system_id=solar_system.id
        )

    def test_can_get_space_type_tag_that_exists(self):
        solar_system = EveSolarSystem.objects.get(name="Amamake")
        tag = StructureTagFactory(name=StructureTag.NAME_LOWSEC_TAG)
        structure, created = StructureTag.objects.get_or_create_for_space_type(
            solar_system
        )
        self.assertFalse(created)
        self.assertEqual(structure, tag)

    def test_raise_error_for_unknown_space_type_when_trying_to_get(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="Amamake")

        with patch(
            "structures.models.eveuniverse.EveSpaceType.from_solar_system"
        ) as mock:
            mock.return_value = EveSpaceType.UNKNOWN
            with self.assertRaises(ValueError):
                StructureTag.objects.get_or_create_for_space_type(solar_system)

    def test_can_get_space_type_tag_that_does_not_exist(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="Amamake")
        # when
        structure, created = StructureTag.objects.get_or_create_for_space_type(
            solar_system
        )
        # then
        self.assertTrue(created)
        self.assertEqual(structure.name, StructureTag.NAME_LOWSEC_TAG)
        self.assertEqual(structure.style, StructureTag.Style.ORANGE)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 50)

    def test_can_update_space_type_tag(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="Amamake")
        StructureTagFactory(
            name=StructureTag.NAME_LOWSEC_TAG,
            style=StructureTag.Style.GREEN,
            is_user_managed=True,
            is_default=True,
            order=100,
        )
        # when
        structure, created = StructureTag.objects.update_or_create_for_space_type(
            solar_system
        )
        # then
        self.assertFalse(created)
        self.assertEqual(structure.name, StructureTag.NAME_LOWSEC_TAG)
        self.assertEqual(structure.style, StructureTag.Style.ORANGE)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 50)

    def test_can_create_for_space_type_highsec(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="Osoggur")
        # when
        structure, created = StructureTag.objects.update_or_create_for_space_type(
            solar_system
        )
        # then
        self.assertTrue(created)
        self.assertEqual(structure.name, StructureTag.NAME_HIGHSEC_TAG)
        self.assertEqual(structure.style, StructureTag.Style.GREEN)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 50)

    def test_can_create_for_space_type_nullsec(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="1-PGSG")
        # when
        structure, created = StructureTag.objects.update_or_create_for_space_type(
            solar_system
        )
        # then
        self.assertTrue(created)
        self.assertEqual(structure.name, StructureTag.NAME_NULLSEC_TAG)
        self.assertEqual(structure.style, StructureTag.Style.RED)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 50)

    def test_can_create_for_space_type_w_space(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="Thera")
        # when
        structure, created = StructureTag.objects.update_or_create_for_space_type(
            solar_system
        )
        # then
        self.assertTrue(created)
        self.assertEqual(structure.name, StructureTag.NAME_W_SPACE_TAG)
        self.assertEqual(structure.style, StructureTag.Style.LIGHT_BLUE)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 50)

    def test_can_get_existing_sov_tag(self):
        # given
        tag = StructureTagFactory(name="sov")
        # when
        structure, created = StructureTag.objects.update_or_create_for_sov()
        # then
        self.assertFalse(created)
        self.assertEqual(structure, tag)

    def test_can_get_non_existing_sov_tag(self):
        # when
        structure, created = StructureTag.objects.update_or_create_for_sov()
        # then
        self.assertTrue(created)
        self.assertEqual(structure.name, "sov")
        self.assertEqual(structure.style, StructureTag.Style.DARK_BLUE)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 20)

    def test_can_update_sov_tag(self):
        # given
        StructureTagFactory(
            name="sov",
            style=StructureTag.Style.GREEN,
            is_user_managed=True,
            is_default=True,
            order=100,
        )
        # when
        structure, created = StructureTag.objects.update_or_create_for_sov()
        # then
        self.assertFalse(created)
        self.assertEqual(structure.name, "sov")
        self.assertEqual(structure.style, StructureTag.Style.DARK_BLUE)
        self.assertEqual(structure.is_user_managed, False)
        self.assertEqual(structure.is_default, False)
        self.assertEqual(structure.order, 20)

    def test_should_raise_error_for_unknown_space_type_when_trying_to_update(self):
        # given
        solar_system = EveSolarSystem.objects.get(name="Amamake")
        StructureTagFactory(
            name=StructureTag.NAME_LOWSEC_TAG,
            style=StructureTag.Style.GREEN,
            is_default=True,
        )
        # when
        with patch(
            "structures.models.eveuniverse.EveSpaceType.from_solar_system"
        ) as mock:
            mock.return_value = EveSpaceType.UNKNOWN
            with self.assertRaises(ValueError):
                StructureTag.objects.update_or_create_for_space_type(solar_system)

    # FIXME
    # def test_update_nullsec_tag(self):
    #     solar_system = EveSolarSystem.objects.get(id=30000474)
    #     structure, created = \
    #         StructureTag.objects.get_or_create_for_space_type(solar_system)
    #     self.assertEqual(structure.name, StructureTag.NAME_NULLSEC_TAG)
    #     self.assertEqual(structure.style, StructureTag.Style.RED)
    #     self.assertEqual(structure.is_user_managed, False)
    #     self.assertEqual(structure.is_default, False)
    #     self.assertEqual(structure.order, 50)

    #     structure.style = StructureTag.Style.GREEN
    #     structure.is_user_managed = True
    #     structure.order = 100
    #     structure.save()

    #     structure, created = \
    #         StructureTag.objects.get_or_create_for_space_type(solar_system)

    #     self.assertFalse(created)
    #     self.assertEqual(structure.name, StructureTag.NAME_NULLSEC_TAG)
    #     self.assertEqual(structure.style, StructureTag.Style.RED)
    #     self.assertEqual(structure.is_user_managed, False)
    #     self.assertEqual(structure.is_default, False)
    #     self.assertEqual(structure.order, 50)


class TestWebhookManager(NoSocketsTestCase):
    def test_should_return_enabled_notification_types(self):
        # given
        WebhookFactory(
            is_active=True,
            notification_types=[
                NotificationType.STRUCTURE_ANCHORING,
                NotificationType.STRUCTURE_REFUELED_EXTRA,
            ],
        )
        WebhookFactory(
            is_active=True,
            notification_types=[
                NotificationType.STRUCTURE_LOST_ARMOR,
                NotificationType.STRUCTURE_LOST_SHIELD,
            ],
        )
        WebhookFactory(
            is_active=False,
            notification_types=[NotificationType.TOWER_ALERT_MSG],
        )
        # when
        result = Webhook.objects.enabled_notification_types()
        # then
        self.assertSetEqual(
            result,
            {
                NotificationType.STRUCTURE_LOST_ARMOR,
                NotificationType.STRUCTURE_LOST_SHIELD,
                NotificationType.STRUCTURE_ANCHORING,
                NotificationType.STRUCTURE_REFUELED_EXTRA,
            },
        )

    def test_should_return_empty_set(self):
        # when
        result = Webhook.objects.enabled_notification_types()
        # then
        self.assertSetEqual(result, set())
