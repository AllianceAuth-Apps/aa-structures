import datetime as dt
from unittest.mock import Mock, patch

import pytz

from django.utils.timezone import now
from eveuniverse.models import EveType

from app_utils.django import app_labels
from app_utils.testing import NoSocketsTestCase

from structures.constants import EveTypeId
from structures.core import notification_timers
from structures.core.notification_types import NotificationType
from structures.models import Structure
from structures.tests.testdata.factories import (
    EveEntityAllianceFactory,
    EveEntityCharacterFactory,
    GeneratedNotificationFactory,
    NotificationFactory,
    NotificationMoonMiningExtractionCanceledFactory,
    NotificationMoonMiningExtractionStartedFactory,
    NotificationOrbitalReinforcedFactory,
    NotificationSovStructureReinforcedFactory,
    NotificationStructureLostShieldFactory,
    OwnerFactory,
    PocoFactory,
    RefineryFactory,
    StructureFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

if "structuretimers" in app_labels():
    from structuretimers.models import Timer

    MODULE_PATH = "structures.core.notification_timers"

    @patch(
        "structuretimers.models._task_calc_timer_distances_for_all_staging_systems",
        Mock(),
    )
    @patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
    @patch(MODULE_PATH + ".STRUCTURES_MOON_EXTRACTION_TIMERS_ENABLED", True)
    class TestTimersForStructureTimers(NoSocketsTestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            load_eveuniverse()

        def test_should_create_timer_for_reinforced_structure(self):
            # given
            owner = OwnerFactory()
            structure = StructureFactory(owner=owner)
            notif = NotificationStructureLostShieldFactory(
                owner=owner, structure=structure
            )
            # when
            result = notification_timers.add_or_remove_timer(notif)
            # then
            self.assertTrue(result)
            timer = Timer.objects.first()
            self.assertIsInstance(timer, Timer)
            self.assertEqual(timer.eve_solar_system, structure.eve_solar_system)
            self.assertEqual(timer.structure_type, structure.eve_type)
            self.assertEqual(timer.timer_type, Timer.Type.ARMOR)
            self.assertEqual(timer.objective, Timer.Objective.FRIENDLY)
            self.assertAlmostEqual(
                timer.date, now() + dt.timedelta(hours=47), delta=dt.timedelta(hours=1)
            )
            self.assertEqual(timer.eve_corporation, owner.corporation)
            self.assertEqual(timer.eve_alliance, owner.corporation.alliance)

            self.assertEqual(timer.visibility, Timer.Visibility.UNRESTRICTED)
            self.assertEqual(timer.structure_name, structure.name)
            self.assertEqual(timer.owner_name, owner.corporation.corporation_name)
            self.assertTrue(timer.details_notes)
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

        def test_should_create_timer_for_sov_reinforcement(self):
            # given
            owner = OwnerFactory(is_alliance_main=True)
            alliance = owner.corporation.alliance
            sender = EveEntityAllianceFactory(
                id=alliance.alliance_id, name=alliance.alliance_name
            )
            notif = NotificationSovStructureReinforcedFactory(
                owner=owner, sender=sender, eve_solar_system_name="1-PGSG"
            )
            # when
            result = notification_timers.add_or_remove_timer(notif)
            # then
            self.assertTrue(result)
            timer = Timer.objects.first()
            self.assertIsInstance(timer, Timer)
            self.assertEqual(timer.timer_type, Timer.Type.FINAL)
            self.assertEqual(timer.eve_solar_system.id, 30000474)
            self.assertEqual(timer.structure_type.id, EveTypeId.TCU)
            self.assertAlmostEqual(
                timer.date,
                pytz.utc.localize(dt.datetime(2018, 12, 20, 17, 3, 22)),
                delta=dt.timedelta(seconds=120),
            )
            self.assertEqual(timer.eve_corporation, owner.corporation)
            self.assertEqual(timer.eve_alliance, owner.corporation.alliance)
            self.assertEqual(timer.visibility, Timer.Visibility.UNRESTRICTED)
            self.assertEqual(timer.owner_name, alliance.alliance_name)
            self.assertTrue(timer.details_notes)
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

        def test_should_create_timer_for_sov_reinforcement_2(self):
            # given
            owner = OwnerFactory(is_alliance_main=False)
            alliance = owner.corporation.alliance
            sender = EveEntityAllianceFactory(
                id=alliance.alliance_id, name=alliance.alliance_name
            )
            notif = NotificationSovStructureReinforcedFactory(
                owner=owner, sender=sender, eve_solar_system_name="1-PGSG"
            )
            # when
            result = notification_timers.add_or_remove_timer(notif)
            # then
            self.assertFalse(result)
            self.assertFalse(Timer.objects.exists())
            notif.refresh_from_db()
            self.assertFalse(notif.is_timer_added)

        def test_should_create_timer_for_orbital_reinforcements(self):
            # given
            owner = OwnerFactory()
            structure = PocoFactory(owner=owner)
            notif = NotificationOrbitalReinforcedFactory(
                owner=owner, structure=structure
            )
            # when
            result = notification_timers.add_or_remove_timer(notif)
            # then
            self.assertTrue(result)
            timer = Timer.objects.first()
            self.assertIsInstance(timer, Timer)
            self.assertEqual(timer.timer_type, Timer.Type.FINAL)
            self.assertEqual(timer.eve_solar_system.id, structure.eve_solar_system.id)
            self.assertEqual(
                timer.structure_type, EveType.objects.get(id=EveTypeId.CUSTOMS_OFFICE)
            )
            self.assertEqual(timer.location_details, structure.eve_planet.name)
            self.assertAlmostEqual(
                timer.date,
                pytz.utc.localize(dt.datetime(2019, 10, 13, 20, 32, 27)),
                delta=dt.timedelta(seconds=120),
            )
            self.assertEqual(timer.eve_corporation, owner.corporation)
            self.assertEqual(timer.eve_alliance, owner.corporation.alliance)
            self.assertEqual(timer.visibility, Timer.Visibility.UNRESTRICTED)
            self.assertEqual(timer.owner_name, owner.corporation.corporation_name)
            self.assertTrue(timer.details_notes)
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

        def test_should_create_timer_for_moon_extraction(self):
            # given
            owner = OwnerFactory()
            structure = RefineryFactory(owner=owner)
            started_by = EveEntityCharacterFactory()
            notif = NotificationMoonMiningExtractionStartedFactory(
                owner=owner, structure=structure, started_by=started_by
            )
            # when
            result = notification_timers.add_or_remove_timer(notif)
            # then
            self.assertTrue(result)
            timer = Timer.objects.first()
            self.assertIsInstance(timer, Timer)
            self.assertEqual(timer.timer_type, Timer.Type.MOONMINING)
            self.assertEqual(timer.eve_solar_system, structure.eve_solar_system)
            self.assertEqual(timer.structure_type, structure.eve_type)
            self.assertEqual(timer.eve_corporation, owner.corporation)
            self.assertEqual(timer.eve_alliance, owner.corporation.alliance)
            self.assertEqual(timer.visibility, Timer.Visibility.UNRESTRICTED)
            self.assertEqual(timer.location_details, structure.eve_moon.name)
            self.assertEqual(timer.owner_name, owner.corporation.corporation_name)
            self.assertEqual(timer.structure_name, structure.name)
            self.assertTrue(timer.details_notes)
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

        def test_can_delete_extraction_timer(self):
            # create timer
            owner = OwnerFactory()
            structure = RefineryFactory(owner=owner)
            notif = NotificationMoonMiningExtractionStartedFactory(
                owner=owner, structure=structure
            )
            self.assertTrue(notification_timers.add_or_remove_timer(notif))
            timer = Timer.objects.first()
            self.assertIsInstance(timer, Timer)
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

            # delete timer
            notif = NotificationMoonMiningExtractionCanceledFactory(
                owner=owner, structure=structure
            )
            self.assertTrue(notification_timers.add_or_remove_timer(notif))
            self.assertFalse(Timer.objects.filter(pk=timer.pk).exists())
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

        def test_should_create_timer_for_starbase_reinforcement(self):
            # given
            notif = GeneratedNotificationFactory()
            structure: Structure = notif.structures.first()
            # when
            result = notification_timers.add_or_remove_timer(notif)
            # then
            self.assertTrue(result)
            obj = Timer.objects.first()
            self.assertEqual(obj.eve_solar_system, structure.eve_solar_system)
            self.assertEqual(obj.structure_type, structure.eve_type)
            self.assertEqual(obj.timer_type, Timer.Type.FINAL)
            self.assertEqual(obj.objective, Timer.Objective.FRIENDLY)
            self.assertAlmostEqual(obj.date, structure.state_timer_end)
            self.assertEqual(obj.eve_corporation, structure.owner.corporation)
            self.assertEqual(obj.visibility, Timer.Visibility.UNRESTRICTED)
            self.assertEqual(obj.structure_name, structure.name)
            self.assertEqual(
                obj.owner_name, structure.owner.corporation.corporation_name
            )
            self.assertTrue(obj.details_notes)
            notif.refresh_from_db()
            self.assertTrue(notif.is_timer_added)

        def test_raise_error_for_unsupported_types(self):
            owner = OwnerFactory()
            notif = NotificationFactory(
                owner=owner, notif_type=NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE
            )
            # when
            with self.assertRaises(NotImplementedError):
                notification_timers.add_or_remove_timer(notif)
