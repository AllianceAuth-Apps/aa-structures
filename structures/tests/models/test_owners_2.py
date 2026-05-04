import datetime as dt
from unittest.mock import patch

import pook

from django.utils.timezone import now
from eveuniverse.tests.testdata.factories_2 import EveMoonFactory, EveSolarSystemFactory

from structures.constants import EveCorporationId
from structures.core.notification_types import NotificationType
from structures.models import Structure, StructureService
from structures.tests.helpers import TestCaseWithClearCache
from structures.tests.testdata.factories import (
    CitadelTypeFactory,
    EveEntityCorporationFactory,
    FuelAlertConfigFactory,
    MoonDrillTypeFactory,
    OwnerFactory,
    StructureFactory,
    StructureTagFactory,
    UserMainDefaultOwnerFactory,
    WebhookFactory,
)
from structures.tests.testdata.helpers import NearestCelestial

MODULE_PATH = "structures.models.owners"


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
class TestUpdateStructuresEsi(TestCaseWithClearCache):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, structures_last_update_at=None)
        cls.corporation_id = cls.owner.corporation.corporation_id

    @pook.on
    def test_can_create_new_structures_and_delete_old(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        StructureFactory(owner=owner, id=1000000000004, name="delete-me")

        structure_id = 1000000000001
        reinforce_hour = 18
        next_reinforce_hour = 12
        state_timer_start = now() + dt.timedelta(hours=3)
        state_timer_end = state_timer_start + dt.timedelta(days=2, hours=1)
        unanchors_at = now() + dt.timedelta(hours=12)
        fuel_expires_at = now() + dt.timedelta(days=3)
        solar_system = EveSolarSystemFactory(name="Amamake")
        structure_type = CitadelTypeFactory()
        next_reinforce_apply = now() + dt.timedelta(days=5)
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "fuel_expires": fuel_expires_at.isoformat(),
                    "next_reinforce_apply": next_reinforce_apply.isoformat(),
                    "next_reinforce_hour": next_reinforce_hour,
                    "profile_id": 101853,
                    "reinforce_hour": reinforce_hour,
                    "services": [
                        {"name": "Clone Bay", "state": "online"},
                        {"name": "Market Hub", "state": "offline"},
                    ],
                    "state": "shield_vulnerable",
                    "state_timer_end": state_timer_end.isoformat(),
                    "state_timer_start": state_timer_start.isoformat(),
                    "structure_id": structure_id,
                    "system_id": solar_system.id,
                    "type_id": structure_type.id,
                    "unanchors_at": unanchors_at.isoformat(),
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure_id}",
            reply=200,
            response_json={
                "owner_id": self.corporation_id,
                "name": f"{solar_system.name} - Test Structure Alpha",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": solar_system.id,
                "type_id": structure_type.id,
            },
        )

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)
        self.assertAlmostEqual(
            owner.structures_last_update_at, now(), delta=dt.timedelta(seconds=30)
        )
        self.assertSetEqual(owner.structures.ids(), {1000000000001})

        # verify attributes for structure
        structure = Structure.objects.get(id=1000000000001)
        self.assertEqual(structure.name, "Test Structure Alpha")
        self.assertEqual(structure.position_x, 55028384780.0)
        self.assertEqual(structure.position_y, 7310316270.0)
        self.assertEqual(structure.position_z, -163686684205.0)
        self.assertEqual(structure.eve_solar_system_id, solar_system.id)
        self.assertEqual(structure.eve_type_id, structure_type.id)
        self.assertEqual(
            int(structure.owner.corporation.corporation_id), self.corporation_id
        )
        self.assertEqual(structure.state, Structure.State.SHIELD_VULNERABLE)
        self.assertEqual(structure.reinforce_hour, reinforce_hour)
        self.assertEqual(structure.fuel_expires_at, fuel_expires_at)
        self.assertEqual(structure.state_timer_start, state_timer_start)
        self.assertEqual(structure.state_timer_end, state_timer_end)
        self.assertEqual(structure.unanchors_at, unanchors_at)
        self.assertEqual(structure.next_reinforce_apply, next_reinforce_apply)
        self.assertEqual(structure.next_reinforce_hour, next_reinforce_hour)
        want = {
            "Clone Bay": StructureService.State.ONLINE,
            "Market Hub": StructureService.State.OFFLINE,
        }
        got = {x.name: x.state for x in structure.services.all()}
        self.assertDictEqual(got, want)

    @pook.on
    def test_can_update_existing_structure(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure = StructureFactory(
            owner=owner,
            state=Structure.State.ANCHOR_VULNERABLE,
        )
        reinforce_hour = 18
        next_reinforce_hour = 12
        state_timer_start = now() + dt.timedelta(hours=3)
        state_timer_end = state_timer_start + dt.timedelta(days=2, hours=1)
        unanchors_at = now() + dt.timedelta(hours=12)
        fuel_expires_at = now() + dt.timedelta(days=3)
        next_reinforce_apply = now() + dt.timedelta(days=5)

        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "fuel_expires": fuel_expires_at.isoformat(),
                    "next_reinforce_apply": next_reinforce_apply.isoformat(),
                    "next_reinforce_hour": next_reinforce_hour,
                    "profile_id": 101853,
                    "reinforce_hour": reinforce_hour,
                    "services": [
                        {"name": "Clone Bay", "state": "online"},
                        {"name": "Market Hub", "state": "offline"},
                    ],
                    "state": "shield_vulnerable",
                    "state_timer_end": state_timer_end.isoformat(),
                    "state_timer_start": state_timer_start.isoformat(),
                    "structure_id": structure.id,
                    "system_id": structure.eve_solar_system.id,
                    "type_id": structure.eve_type.id,
                    "unanchors_at": unanchors_at.isoformat(),
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure.id}",
            reply=200,
            response_json={
                "owner_id": self.corporation_id,
                "name": f"{structure.eve_solar_system.name} - {structure.name}",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": structure.eve_solar_system.id,
                "type_id": structure.eve_type.id,
            },
        )

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)
        self.assertAlmostEqual(
            owner.structures_last_update_at, now(), delta=dt.timedelta(seconds=30)
        )
        self.assertSetEqual(owner.structures.ids(), {structure.id})

        # verify attributes for structure
        structure.refresh_from_db()
        self.assertEqual(structure.state, Structure.State.SHIELD_VULNERABLE)
        self.assertEqual(structure.reinforce_hour, reinforce_hour)
        self.assertEqual(structure.fuel_expires_at, fuel_expires_at)
        self.assertEqual(structure.state_timer_start, state_timer_start)
        self.assertEqual(structure.state_timer_end, state_timer_end)
        self.assertEqual(structure.unanchors_at, unanchors_at)
        self.assertEqual(structure.next_reinforce_apply, next_reinforce_apply)
        self.assertEqual(structure.next_reinforce_hour, next_reinforce_hour)
        want = {
            "Clone Bay": StructureService.State.ONLINE,
            "Market Hub": StructureService.State.OFFLINE,
        }
        got = {x.name: x.state for x in structure.services.all()}
        self.assertDictEqual(got, want)

    @pook.on
    def test_can_handle_owner_without_structures(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[],
        )

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)
        self.assertSetEqual(owner.structures.ids(), set())

    @pook.on
    def test_should_not_break_when_structures_endpoint_returns_error(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=500,
            response_json={"error": "internal error"},
        )

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        self.assertSetEqual(owner.structures.ids(), set())

    @pook.on
    def test_should_not_delete_existing_upwell_structures_when_update_failed(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure = StructureFactory(owner=owner)
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=500,
            response_json={"error": "internal error"},
        )
        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        self.assertSetEqual(owner.structures.ids(), {structure.id})

    @pook.on
    def test_should_not_break_when_universe_endpoint_returns_error(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure_id = 1000000000001
        solar_system = EveSolarSystemFactory()
        structure_type = CitadelTypeFactory()
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure_id,
                    "system_id": solar_system.id,
                    "type_id": structure_type.id,
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure_id}",
            reply=500,
            response_json={"error": "internal_error"},
        )

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        structure = Structure.objects.get(id=structure_id)
        self.assertEqual(structure.name, "(no data)")

    @pook.on
    def test_update_will_not_break_on_403_error_from_structure_info(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure_id = 1000000000001
        solar_system = EveSolarSystemFactory()
        structure_type = CitadelTypeFactory()
        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure_id,
                    "system_id": solar_system.id,
                    "type_id": structure_type.id,
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure_id}",
            reply=403,
            response_json={"error": "forbidden"},
        )

        # when
        owner.update_structures_esi()

        # then
        owner.refresh_from_db()
        self.assertFalse(owner.is_structure_sync_fresh)
        structure = Structure.objects.get(id=structure_id)
        self.assertEqual(structure.name, "(no data)")

    @pook.on
    def test_tags_are_not_modified_by_update(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure = StructureFactory(owner=owner)

        tag_a = StructureTagFactory(name="tag_a")
        structure.tags.add(tag_a)
        structure.save()

        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure.id,
                    "system_id": structure.eve_solar_system.id,
                    "type_id": structure.eve_type.id,
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure.id}",
            reply=200,
            response_json={
                "owner_id": self.corporation_id,
                "name": f"{structure.eve_solar_system.name} - Test Structure Alpha",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": structure.eve_solar_system.id,
                "type_id": structure.eve_type.id,
            },
        )

        # when
        owner.update_structures_esi()

        # then
        self.assertSetEqual(owner.structures.ids(), {structure.id})

        # should still contain the tag
        self.assertTrue(structure.tags.filter(name="tag_a").exists())


@patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
@patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
class TestUpdateStructuresEsi_FuelAlerts(TestCaseWithClearCache):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, structures_last_update_at=None)
        cls.corporation_id = cls.owner.corporation.corporation_id
        EveEntityCorporationFactory(
            id=EveCorporationId.DED, name="DED"
        )  # for notifications

    @patch(
        "structures.models.structures_1.STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS", True
    )
    @patch("structures.models.notifications.Webhook.send_message")
    @pook.on
    def test_should_send_refueled_notification_when_fuel_level_increased(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA],
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        owner.webhooks.add(webhook)

        fuel_expires_at_1 = now() + dt.timedelta(hours=3)
        fuel_expires_at_2 = fuel_expires_at_1 + dt.timedelta(days=3)
        structure = StructureFactory(owner=owner, fuel_expires_at=fuel_expires_at_1)
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure.structure_fuel_alerts.create(config=config, hours=12)
        structure.save()

        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "fuel_expires": fuel_expires_at_2.isoformat(),
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure.id,
                    "system_id": structure.eve_solar_system.id,
                    "type_id": structure.eve_type.id,
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure.id}",
            reply=200,
            response_json={
                "owner_id": self.corporation_id,
                "name": f"{structure.eve_solar_system.name} - Test Structure Alpha",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": structure.eve_solar_system.id,
                "type_id": structure.eve_type.id,
            },
        )

        # when
        owner.update_structures_esi()

        # then
        self.assertTrue(mock_send_message.called)
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    @patch(
        "structures.models.structures_1.STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS", True
    )
    @patch("structures.models.notifications.Webhook.send_message")
    @pook.on
    def test_should_not_send_refueled_notification_when_fuel_level_unchanged(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        structure_id = 1000000000001
        fuel_expires_at_1 = now() + dt.timedelta(hours=3)
        fuel_expires_at_2 = fuel_expires_at_1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA],
        )
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        owner.webhooks.add(webhook)
        structure = StructureFactory(
            owner=owner, id=structure_id, fuel_expires_at=fuel_expires_at_1
        )

        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "fuel_expires": fuel_expires_at_2.isoformat(),
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure_id,
                    "system_id": structure.eve_solar_system.id,
                    "type_id": structure.eve_type.id,
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure_id}",
            reply=200,
            response_json={
                "owner_id": self.corporation_id,
                "name": f"{structure.eve_solar_system.name} - Test Structure Alpha",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": structure.eve_solar_system.id,
                "type_id": structure.eve_type.id,
            },
        )

        # when
        owner.update_structures_esi()

        # then
        self.assertFalse(mock_send_message.called)

    @pook.on
    def test_can_update_metenox(self):
        # given
        owner = OwnerFactory(user=self.user, structures_last_update_at=None)
        structure_id = 1000000000111
        structure_name = "Test Moon Drill"
        solar_system = EveSolarSystemFactory(name="Amamake")
        structure_type = MoonDrillTypeFactory(id=81826, name="Metenox Moon Drill")

        pook.get(
            f"https://esi.evetech.net/corporations/{self.corporation_id}/structures",
            reply=200,
            response_json=[
                {
                    "corporation_id": self.corporation_id,
                    "profile_id": 101853,
                    "reinforce_hour": 18,
                    "state": "shield_vulnerable",
                    "structure_id": structure_id,
                    "system_id": solar_system.id,
                    "type_id": structure_type.id,
                    "services": [
                        {"name": "Moon Drill", "state": "online"},
                    ],
                },
            ],
        )
        pook.get(
            f"https://esi.evetech.net/universe/structures/{structure_id}",
            reply=200,
            response_json={
                "owner_id": self.corporation_id,
                "name": f"{solar_system.name} - {structure_name}",
                "position": {
                    "x": 55028384780.0,
                    "y": 7310316270.0,
                    "z": -163686684205.0,
                },
                "solar_system_id": solar_system.id,
                "type_id": structure_type.id,
            },
        )

        moon = EveMoonFactory(eve_planet__eve_solar_system=solar_system)

        # when
        with patch(MODULE_PATH + ".EveSolarSystem.nearest_celestial") as m:
            m.return_value = NearestCelestial(None, moon, 100)
            owner.update_structures_esi()

        owner.refresh_from_db()
        self.assertTrue(owner.is_structure_sync_fresh)

        structure = Structure.objects.get(id=structure_id)
        self.assertEqual(structure.name, structure_name)
        self.assertEqual(structure.eve_solar_system.id, solar_system.id)
        services = set(structure.services.values_list("name", flat=True))
        self.assertSetEqual({"Moon Drill"}, services)
        self.assertEqual(structure.eve_moon, moon)
