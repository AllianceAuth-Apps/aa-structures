from unittest.mock import Mock, patch

from app_utils.django import app_labels
from app_utils.testing import NoSocketsTestCase

from structures.core import notification_timers
from structures.core.notification_types import NotificationType
from structures.models import Notification
from structures.tests.testdata.factories import (
    EveAllianceInfoFactory,
    EveCorporationInfoFactory,
    GeneratedNotificationFactory,
    OwnerFactory,
)
from structures.tests.testdata.helpers import (
    load_notification_entities,
    load_notification_objects,
)

MODULE_PATH = "structures.core.notification_timers"

if "timerboard" in app_labels():
    from allianceauth.timerboard.models import Timer as AuthTimer

    @patch(MODULE_PATH + ".STRUCTURES_MOON_EXTRACTION_TIMERS_ENABLED", False)
    @patch("allianceauth.timerboard.models.Timer", spec=True)
    def test_moon_timers_disabled(self, mock_Timer):
        # given
        notif = Notification.objects.get(notification_id=1000000404)
        # when
        result = notification_timers.add_or_remove_timer(notif)
        # then
        self.assertFalse(result)
        self.assertFalse(mock_Timer.objects.create.called)
        notif.refresh_from_db()
        self.assertFalse(notif.add_or_remove_timer())
        self.assertFalse(mock_Timer.delete.called)


if "structuretimers" in app_labels():

    @patch(
        "structuretimers.models._task_calc_timer_distances_for_all_staging_systems",
        Mock(),
    )
    @patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
    class TestNotificationAddToTimerboard(NoSocketsTestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            alliance = EveAllianceInfoFactory(alliance_id=3001)
            corporation = EveCorporationInfoFactory(
                corporation_id=2001, alliance=alliance
            )
            cls.owner = OwnerFactory(corporation=corporation, is_alliance_main=True)

            load_notification_entities(cls.owner)
            load_notification_objects(cls.owner)


if "timerboard" in app_labels() or "structuretimers" in app_labels():

    @patch(MODULE_PATH + ".STRUCTURES_MOON_EXTRACTION_TIMERS_ENABLED", True)
    def test_normal(self):
        notification_without_timer_query = Notification.objects.filter(
            notification_id__in=[
                1000000401,
                1000000403,
                1000000405,
                1000000502,
                1000000503,
                1000000506,
                1000000507,
                1000000508,
                1000000509,
                1000000510,
                1000000511,
                1000000512,
                1000000513,
                1000000601,
                1000010509,
                1000010601,
            ]
        )
        for obj in notification_without_timer_query:
            self.assertFalse(obj.add_or_remove_timer())

        self.assertEqual(AuthTimer.objects.count(), 0)

        obj = Notification.objects.get(notification_id=1000000501)
        self.assertFalse(obj.add_or_remove_timer())

        obj = Notification.objects.get(notification_id=1000000504)
        self.assertTrue(obj.add_or_remove_timer())

        obj = Notification.objects.get(notification_id=1000000505)
        self.assertTrue(obj.add_or_remove_timer())

        obj = Notification.objects.get(notification_id=1000000602)
        self.assertTrue(obj.add_or_remove_timer())

        ids_set_1 = {x.id for x in AuthTimer.objects.all()}
        obj = Notification.objects.get(notification_id=1000000404)
        self.assertTrue(obj.add_or_remove_timer())

        self.assertEqual(AuthTimer.objects.count(), 4)

        # this should remove the right timer only
        obj = Notification.objects.get(notification_id=1000000402)
        obj.add_or_remove_timer()
        self.assertEqual(AuthTimer.objects.count(), 3)
        ids_set_2 = {x.id for x in AuthTimer.objects.all()}
        self.assertSetEqual(ids_set_1, ids_set_2)

    @patch(MODULE_PATH + ".STRUCTURES_MOON_EXTRACTION_TIMERS_ENABLED", True)
    def test_run_all(self):
        for obj in Notification.objects.all():
            timer_types = NotificationType.relevant_for_timerboard()
            with self.subTest(notif_type=obj.notif_type):
                is_timer = obj.notif_type in timer_types
                is_added = obj.add_or_remove_timer()
                self.assertEqual(is_timer, is_added)

    @patch(MODULE_PATH + ".STRUCTURES_TIMERS_ARE_CORP_RESTRICTED", False)
    def test_corp_restriction_1(self):
        # given
        notif = Notification.objects.get(notification_id=1000000504)
        # when
        result = notif.add_or_remove_timer()
        # then
        self.assertTrue(result)
        timer = AuthTimer.objects.first()
        self.assertFalse(timer.corp_timer)

    @patch(MODULE_PATH + ".STRUCTURES_TIMERS_ARE_CORP_RESTRICTED", True)
    def test_corp_restriction_2(self):
        obj = Notification.objects.get(notification_id=1000000504)
        self.assertTrue(obj.add_or_remove_timer())
        timer = AuthTimer.objects.first()
        self.assertTrue(timer.corp_timer)

    def test_timer_starbase_reinforcement(self):
        # given
        notif = GeneratedNotificationFactory()
        structure = notif.structures.first()
        # when
        result = notif.add_or_remove_timer()
        # then
        self.assertTrue(result)
        obj = AuthTimer.objects.first()
        self.assertEqual(obj.system, structure.eve_solar_system.name)
        self.assertEqual(obj.planet_moon, structure.eve_moon.name)
        self.assertEqual(obj.eve_time, structure.state_timer_end)
        self.assertEqual(obj.system, structure.eve_solar_system.name)
        self.assertEqual(obj.planet_moon, structure.eve_moon.name)
        self.assertEqual(obj.eve_time, structure.state_timer_end)
        self.assertEqual(obj.system, structure.eve_solar_system.name)
        self.assertEqual(obj.planet_moon, structure.eve_moon.name)
        self.assertEqual(obj.eve_time, structure.state_timer_end)
