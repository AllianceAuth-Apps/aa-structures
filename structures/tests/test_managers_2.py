import datetime as dt
from unittest.mock import patch

from django.utils.timezone import now

from app_utils.testing import NoSocketsTestCase

from structures.core.notification_types import NotificationType
from structures.models import GeneratedNotification, Notification, Owner

from .testdata.factories import (
    GeneratedNotificationFactory,
    NotificationFactory,
    OwnerCharacterFactory,
    OwnerFactory,
)
from .testdata.load_eveuniverse import load_eveuniverse

MANAGERS_PATH = "structures.managers"


@patch(
    "structures.models.notifications.NotificationBase.add_or_remove_timer",
    spec=True,
)
class TestNotificationBaseAddOrRemoveTimers(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

    def test_should_create_new_timers_from_notifications(
        self, mock_add_or_remove_timer_from_notification
    ):
        # given
        owner = OwnerFactory()
        NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_LOST_SHIELD
        )
        NotificationFactory(
            owner=owner, notif_type=NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE
        )
        # when
        Notification.objects.add_or_remove_timers()
        # then
        self.assertEqual(mock_add_or_remove_timer_from_notification.call_count, 1)

    def test_should_create_new_timers_from_generated_notifications(
        self, mock_add_or_remove_timer_from_notification
    ):
        # given
        GeneratedNotificationFactory()
        # when
        GeneratedNotification.objects.add_or_remove_timers()
        # then
        self.assertEqual(mock_add_or_remove_timer_from_notification.call_count, 1)


class TestOwnerManager(NoSocketsTestCase):
    def test_should_annotate_characters_count(self):
        # given
        owner = OwnerFactory()  # 1st character automatically created
        OwnerCharacterFactory(owner=owner, is_enabled=False)  # 2nd character added
        # when
        result = Owner.objects.annotate_characters_count()
        # then
        obj = result.get(pk=owner.pk)
        self.assertEqual(obj.characters_enabled_count, 1)
        self.assertEqual(obj.characters_disabled_count, 1)

    def test_should_return_when_structures_where_last_updated_for_several_owners(self):
        # given
        owner_1_structures_last_update_at = now() - dt.timedelta(hours=3)
        OwnerFactory(structures_last_update_at=owner_1_structures_last_update_at)
        owner_2_structures_last_update_at = now() - dt.timedelta(hours=1)
        OwnerFactory(structures_last_update_at=owner_2_structures_last_update_at)
        # when
        result = Owner.objects.structures_last_updated()
        # then
        self.assertEqual(result, owner_2_structures_last_update_at)

    def test_should_return_none_when_structures_where_last_updated_and_no_owners(
        self,
    ):
        # when
        result = Owner.objects.structures_last_updated()
        # then
        self.assertIsNone(result)
