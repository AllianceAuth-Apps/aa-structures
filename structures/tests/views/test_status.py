import datetime as dt
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.timezone import now

from structures.tests.testdata.factories import OwnerFactory
from structures.views import status

OWNERS_PATH = "structures.models.owners"


class TestStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    def test_view_service_status_ok(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        request = self.factory.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 200)

    @patch(OWNERS_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_structures(self):
        # given
        OwnerFactory(
            structures_last_update_at=now() - dt.timedelta(minutes=31),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        request = self.factory.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)

    @patch(OWNERS_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_notifications(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now() - dt.timedelta(minutes=31),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        request = self.factory.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)

    @patch(OWNERS_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_forwarding(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now() - dt.timedelta(minutes=31),
            assets_last_update_at=now(),
        )
        request = self.factory.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)

    @patch(OWNERS_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    def test_view_service_status_fail_assets(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now() - dt.timedelta(minutes=31),
        )
        request = self.factory.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)
