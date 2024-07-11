import re
from unittest.mock import patch

from requests.exceptions import HTTPError

from django.contrib.auth.models import Group

from app_utils.django import app_labels
from app_utils.testing import NoSocketsTestCase

from structures.models import Notification
from structures.tests.testdata.factories import (
    OwnerFactory,
    StructureFactory,
    WebhookFactory,
)
from structures.tests.testdata.helpers import (
    clone_notification,
    load_eve_entities,
    load_notification_entities,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.models.notifications"

if "discord" in app_labels():

    @patch(MODULE_PATH + ".Notification._import_discord")
    @patch(MODULE_PATH + ".Webhook.send_message", spec=True)
    class TestGroupPings(NoSocketsTestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            load_eveuniverse()
            load_eve_entities()

            cls.group_1 = Group.objects.create(name="Dummy Group 1")
            cls.group_2 = Group.objects.create(name="Dummy Group 2")
            cls.owner = OwnerFactory()
            load_notification_entities(cls.owner)
            StructureFactory(id=1000000000001)

        @staticmethod
        def _my_group_to_role(group: Group) -> dict:
            if not isinstance(group, Group):
                raise TypeError("group must be of type Group")
            return {"id": group.pk, "name": group.name}

        def test_can_ping_via_webhook(self, mock_send_message, mock_import_discord):
            # given
            mock_send_message.return_value = 1
            mock_import_discord.return_value.objects.group_to_role.side_effect = (
                self._my_group_to_role
            )
            webhook = WebhookFactory()
            webhook.ping_groups.add(self.group_1)
            obj = clone_notification(
                Notification.objects.get(notification_id=1000000509)
            )
            # when
            result = obj.send_to_webhook(webhook)
            # then
            self.assertTrue(result)
            self.assertTrue(mock_import_discord.called)
            _, kwargs = mock_send_message.call_args
            self.assertIn(f"<@&{self.group_1.pk}>", kwargs["content"])

        def test_can_ping_via_owner(self, mock_send_message, mock_import_discord):
            # given
            mock_send_message.return_value = 1
            mock_import_discord.return_value.objects.group_to_role.side_effect = (
                self._my_group_to_role
            )
            webhook = WebhookFactory()
            self.owner.ping_groups.add(self.group_2)
            obj = clone_notification(
                Notification.objects.get(notification_id=1000000509)
            )
            # when
            result = obj.send_to_webhook(webhook)
            # then
            self.assertTrue(result)
            self.assertTrue(mock_import_discord.called)
            _, kwargs = mock_send_message.call_args
            self.assertIn(f"<@&{self.group_2.pk}>", kwargs["content"])

        def test_can_ping_both(self, mock_send_message, mock_import_discord):
            # given
            mock_send_message.return_value = 1
            mock_import_discord.return_value.objects.group_to_role.side_effect = (
                self._my_group_to_role
            )
            webhook = WebhookFactory()
            webhook.ping_groups.add(self.group_1)
            self.owner.ping_groups.add(self.group_2)
            obj = clone_notification(
                Notification.objects.get(notification_id=1000000509)
            )
            # when
            result = obj.send_to_webhook(webhook)
            # then
            self.assertTrue(result)
            self.assertTrue(mock_import_discord.called)
            _, kwargs = mock_send_message.call_args
            self.assertIn(f"<@&{self.group_1.pk}>", kwargs["content"])
            self.assertIn(f"<@&{self.group_2.pk}>", kwargs["content"])

        def test_no_ping_if_not_set(self, mock_send_message, mock_import_discord):
            # given
            mock_send_message.return_value = 1
            mock_import_discord.return_value.objects.group_to_role.side_effect = (
                self._my_group_to_role
            )
            webhook = WebhookFactory()
            obj = clone_notification(
                Notification.objects.get(notification_id=1000000509)
            )
            # when
            result = obj.send_to_webhook(webhook)
            # then
            self.assertTrue(result)
            self.assertFalse(mock_import_discord.called)
            _, kwargs = mock_send_message.call_args
            self.assertFalse(re.search(r"(<@&\d+>)", kwargs["content"]))

        def test_can_handle_http_error(self, mock_send_message, mock_import_discord):
            # given
            mock_send_message.return_value = 1
            mock_import_discord.return_value.objects.group_to_role.side_effect = (
                HTTPError
            )
            webhook = WebhookFactory()
            webhook.ping_groups.add(self.group_1)
            obj = clone_notification(
                Notification.objects.get(notification_id=1000000509)
            )
            # when
            result = obj.send_to_webhook(webhook)
            # then
            self.assertTrue(result)
            self.assertTrue(mock_import_discord.called)
            _, kwargs = mock_send_message.call_args
            self.assertFalse(re.search(r"(<@&\d+>)", kwargs["content"]))

        def test_should_abort_when_content_is_too_large(
            self, mock_send_message, mock_import_discord
        ):
            # given
            mock_send_message.return_value = 1
            mock_import_discord.return_value.objects.group_to_role.side_effect = (
                self._my_group_to_role
            )
            webhook = WebhookFactory()
            for i in range(286):
                group = Group.objects.create(name=f"Group {i+1}")
                webhook.ping_groups.add(group)
            obj = clone_notification(
                Notification.objects.get(notification_id=1000000509)
            )
            # when
            result = obj.send_to_webhook(webhook)
            # then
            self.assertFalse(result)
