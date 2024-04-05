import datetime as dt
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from app_utils.testing import response_text

from structures.tests.testdata.factories import OwnerFactory
from structures.views import status

OWNERS_PATH = "structures.models.owners"


@patch(OWNERS_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
@patch(OWNERS_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
class TestServiceStatus(TestCase):
    def test_should_report_ok(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        request = self.client.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_text(response), "service is up")

    def test_should_report_ok_when_downed_owner_is_inactive(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        OwnerFactory(
            structures_last_update_at=now() - dt.timedelta(minutes=31),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
            is_active=False,
        )
        request = self.client.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 200)

    def test_should_report_fail_when_issue_with_structures(self):
        # given
        OwnerFactory(
            structures_last_update_at=now() - dt.timedelta(minutes=31),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        request = self.client.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_text(response), "service is down")

    def test_should_report_fail_when_issue_with_notifications(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now() - dt.timedelta(minutes=31),
            forwarding_last_update_at=now(),
            assets_last_update_at=now(),
        )
        request = self.client.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_text(response), "service is down")

    def test_should_report_fail_when_issue_with_forwarding(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now() - dt.timedelta(minutes=31),
            assets_last_update_at=now(),
        )
        request = self.client.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_text(response), "service is down")

    def test_should_report_fail_when_issue_with_assets(self):
        # given
        OwnerFactory(
            structures_last_update_at=now(),
            notifications_last_update_at=now(),
            forwarding_last_update_at=now(),
            assets_last_update_at=now() - dt.timedelta(minutes=31),
        )
        request = self.client.get(reverse("structures:service_status"))
        # when
        response = status.service_status(request)
        # then
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response_text(response), "service is down")
