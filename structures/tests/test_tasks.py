from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from app_utils.testdata_factories import UserFactory
from app_utils.testing import NoSocketsTestCase, generate_invalid_pk

from structures import tasks
from structures.core.notification_types import NotificationType
from structures.models import Owner, Webhook

from .testdata.factories import (
    FuelAlertConfigFactory,
    JumpFuelAlertConfigFactory,
    NotificationFactory,
    OwnerFactory,
    UserMainDefaultOwnerFactory,
    WebhookFactory,
)

MODULE_PATH = "structures.tasks"
MODULE_PATH_MODELS_OWNERS = "structures.models.owners"


@patch(MODULE_PATH + ".Webhook.send_queued_messages", spec=True)
class TestSendMessagesForWebhook(TestCase):
    @classmethod
    def setUpClass(cls):  # Can not be setUpTestData due to conflict with redis client
        super().setUpClass()
        cls.webhook = WebhookFactory()

    def test_normal(self, mock_send_queued_messages):
        tasks.send_messages_for_webhook(self.webhook.pk)
        self.assertEqual(mock_send_queued_messages.call_count, 1)

    def test_invalid_pk(self, mock_send_queued_messages):
        tasks.send_messages_for_webhook(generate_invalid_pk(Webhook))
        self.assertEqual(mock_send_queued_messages.call_count, 0)

    def test_disabled_webhook(self, mock_send_queued_messages):
        self.webhook.is_active = False
        self.webhook.save()

        tasks.send_messages_for_webhook(self.webhook.pk)
        self.assertEqual(mock_send_queued_messages.call_count, 0)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".Owner.update_structures_esi", spec=True)
class TestUpdateStructuresEsi(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, is_alliance_main=True)

    def test_call_structure_update_with_owner_only(self, mock_update_structures_esi):
        """TODO: Investigate how to call the top level method that contains the chains()"""
        tasks.update_structures_esi_for_owner(self.owner.pk)
        self.assertTrue(mock_update_structures_esi.called)

    def test_call_structure_update_with_owner_and_user(
        self, mock_update_structures_esi
    ):
        """TODO: Investigate how to call the top level method that contains the chains()"""
        tasks.update_structures_esi_for_owner(self.owner.pk, self.user.pk)
        first, _ = mock_update_structures_esi.call_args
        self.assertEqual(first[0], self.user)

    def test_call_structure_update_with_owner_and_ignores_invalid_user(
        self, mock_update_structures_esi
    ):
        """TODO: Investigate how to call the top level method that contains the chains()"""
        tasks.update_structures_esi_for_owner(self.owner.pk, generate_invalid_pk(User))
        first, _ = mock_update_structures_esi.call_args
        self.assertIsNone(first[0])

    def test_raises_exception_if_owner_is_unknown(self, mock_update_structures_esi):
        with self.assertRaises(Owner.DoesNotExist):
            """TODO: Investigate how to call the top level method that contains the chains()"""
            tasks.update_structures_esi_for_owner(owner_pk=generate_invalid_pk(Owner))


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".update_structures_for_owner", spec=True)
class TestUpdateStructuresForOwner(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, is_alliance_main=True)

    def test_can_update_structures_for_all_owners(
        self, mock_update_structures_for_owner
    ):
        # given
        owner_2 = OwnerFactory()
        # when
        tasks.update_structures()
        # then
        call_args_list = mock_update_structures_for_owner.delay.call_args_list
        owner_pks = {args[0][0] for args in call_args_list}
        self.assertSetEqual(owner_pks, {self.owner.pk, owner_2.pk})

    def test_does_not_update_structures_for_non_active_owners(
        self, mock_update_structures_for_owner
    ):
        # given
        OwnerFactory(is_active=False)
        # when
        tasks.update_structures()
        # then
        call_args_list = mock_update_structures_for_owner.delay.call_args_list
        owner_pks = {args[0][0] for args in call_args_list}
        self.assertSetEqual(owner_pks, {self.owner.pk})


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestUpdateOwnerAsset(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, is_alliance_main=True)

    @patch(MODULE_PATH + ".Owner.update_asset_esi")
    def test_call_structure_asset_update_with_owner_and_user(
        self, mock_update_asset_esi
    ):
        """TODO: Investigate how to call the top level method that contains the chains()"""
        tasks.update_structures_assets_for_owner(self.owner.pk, self.user.pk)
        first, _ = mock_update_asset_esi.call_args
        self.assertEqual(first[0], self.user)

    @patch(MODULE_PATH + ".Owner.update_asset_esi")
    def test_call_structure_asset_update_with_owner_and_ignores_invalid_user(
        self, mock_update_asset_esi
    ):
        """TODO: Investigate how to call the top level method that contains the chains()"""
        tasks.update_structures_assets_for_owner(
            self.owner.pk, generate_invalid_pk(User)
        )
        first, _ = mock_update_asset_esi.call_args
        self.assertIsNone(first[0])

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    def test_raises_exception_if_owner_is_unknown(self):
        with self.assertRaises(Owner.DoesNotExist):
            """TODO: Investigate how to call the top level method that contains the chains()"""
            tasks.update_structures_assets_for_owner(
                owner_pk=generate_invalid_pk(Owner)
            )


@patch(MODULE_PATH_MODELS_OWNERS + ".Owner.update_is_up", lambda *args, **kwargs: None)
@patch(MODULE_PATH + ".send_structure_fuel_notifications_for_config", spec=True)
@patch(MODULE_PATH + ".process_notifications_for_owner", spec=True)
class TestFetchAllNotifications(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, is_alliance_main=True)

    def test_fetch_all_notifications(
        self, mock_fetch_notifications_owner, mock_send_fuel_notifications_for_config
    ):
        # given
        owner_2 = OwnerFactory()
        OwnerFactory(is_active=False)
        # when
        tasks.fetch_all_notifications()
        # then
        call_args_list = mock_fetch_notifications_owner.apply_async.call_args_list
        owner_pks = {obj[1]["kwargs"]["owner_pk"] for obj in call_args_list}
        self.assertSetEqual(owner_pks, {self.owner.pk, owner_2.pk})

    def test_send_new_fuel_notifications(
        self, mock_fetch_notifications_owner, mock_send_fuel_notifications_for_config
    ):
        # given
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        # when
        tasks.fetch_all_notifications()
        # then
        self.assertEqual(mock_send_fuel_notifications_for_config.delay.call_count, 1)
        args, _ = mock_send_fuel_notifications_for_config.delay.call_args
        self.assertEqual(args[0], config.pk)


# TODO: Fix tests. Does not work with tox.
# @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
# @patch(MODULE_PATH + ".fetch_esi_status", lambda: EsiStatus(True, 100, 60))
# class TestProcessNotificationsForOwner(TestCase):
#     @classmethod
#     def setUpClass(cls) -> None:
#         super().setUpClass()
#         create_structures()
#         cls.user, cls.owner = set_owner_character(character_id=1001)

#     def test_should_raise_exception_if_owner_is_unknown(self):
#         with self.assertRaises(Owner.DoesNotExist):
#             tasks.process_notifications_for_owner.delay(
#                 owner_pk=generate_invalid_pk(Owner)
#             )

#     @patch(MODULE_PATH + ".send_messages_for_webhook")
#     @patch(MODULE_PATH + ".Owner.fetch_notifications_esi")
#     def test_should_send_notifications_for_owner(
#         self, mock_fetch_notifications_esi, mock_send_messages_for_webhook
#     ):
#         # given
#         load_notification_entities(self.owner)
#         Notification.objects.exclude(notification_id=1000000509).delete()
#         self.owner.webhooks.first().clear_queue()
#         # when
#         tasks.process_notifications_for_owner.delay(owner_pk=self.owner.pk)
#         # then
#         self.assertTrue(mock_fetch_notifications_esi.called)
#         self.assertEqual(mock_send_messages_for_webhook.apply_async.call_count, 1)
#         for notif in self.owner.notifications.filter(
#             notif_type__in=[NotificationType.structure_related()]
#         ):
#             structure_ids = notif.structures.values_list("id", flat=True)
#             self.assertTrue(
#                 1000000000001 in set(structure_ids)
#                 or 1000000000002 in set(structure_ids)
#             )

#     @patch(MODULE_PATH + ".send_messages_for_webhook")
#     @patch(MODULE_PATH + ".Owner.fetch_notifications_esi")
#     def test_dont_sent_if_queue_is_empty(
#         self, mock_fetch_notifications_esi, mock_send_messages_for_webhook
#     ):
#         # given
#         self.owner.webhooks.first().clear_queue()
#         # when
#         tasks.process_notifications_for_owner.delay(owner_pk=self.owner.pk)
#         # then
#         self.assertTrue(mock_fetch_notifications_esi.called)
#         self.assertEqual(mock_send_messages_for_webhook.apply_async.call_count, 0)


@patch("structures.webhooks.core.sleep", lambda _: None)
@patch(MODULE_PATH + ".notify", spec=True)
@patch("structures.models.notifications.Webhook.send_test_message", spec=True)
class TestSendTestNotification(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=cls.user, is_alliance_main=True)

    def test_send_test_notification(self, mock_send_test_message, mock_notify):
        # given
        mock_send_test_message.return_value = ("", True)
        my_webhook = self.owner.webhooks.first()

        # when
        tasks.send_test_notifications_to_webhook(my_webhook.pk, self.user.pk)

        # then
        self.assertEqual(mock_send_test_message.call_count, 1)
        self.assertTrue(mock_notify.called)
        args = mock_notify.call_args[1]
        self.assertEqual(args["level"], "success")

    def test_send_test_notification_error(self, mock_send_test_message, mock_notify):
        # given
        mock_send_test_message.return_value = ("Error", False)
        my_webhook = self.owner.webhooks.first()

        # when
        tasks.send_test_notifications_to_webhook(my_webhook.pk, self.user.pk)

        # then
        self.assertEqual(mock_send_test_message.call_count, 1)
        self.assertTrue(mock_notify.called)
        args = mock_notify.call_args[1]
        self.assertEqual(args["level"], "danger")


@patch("structures.models.notifications.Notification.update_related_structures")
class TestUpdateNotificationsStructureRelations(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory(is_alliance_main=True)

    def test_should_run_updates(self, mock_update_related_structures):
        # given
        mock_update_related_structures.return_value = True
        NotificationFactory(
            owner=self.owner, notif_type=NotificationType.STRUCTURE_UNDER_ATTACK
        )
        NotificationFactory(
            owner=self.owner, notif_type=NotificationType.CORP_APP_NEW_MSG
        )
        # when
        result = tasks.update_notifications_structure_relations(self.owner.pk)
        # then
        self.assertEqual(result, 1)

    def test_should_run_no_updates(self, mock_update_related_structures):
        # given
        mock_update_related_structures.return_value = True
        NotificationFactory(
            owner=self.owner, notif_type=NotificationType.CORP_APP_NEW_MSG
        )
        # when
        result = tasks.update_notifications_structure_relations(self.owner.pk)
        # then
        self.assertEqual(result, 0)


class TestOtherTasks(NoSocketsTestCase):
    @patch(
        MODULE_PATH + ".EveSovereigntyMap.objects.update_or_create_all_from_esi",
        spec=True,
    )
    def test_should_call_update_sov_map_from_esi(self, mock_update_from_esi):
        # when
        tasks.update_sov_map()
        # then
        self.assertTrue(mock_update_from_esi.called)

    @patch(MODULE_PATH + ".Owner.fetch_notifications_esi", spec=True)
    def test_should_fetch_notifications_for_owner(self, mock_fetch_notifications_esi):
        # given
        owner = OwnerFactory()
        # when
        tasks.fetch_notification_for_owner(owner.pk)
        # then
        self.assertTrue(mock_fetch_notifications_esi.called)

    @patch(MODULE_PATH + ".send_queued_messages_for_webhooks", spec=True)
    @patch(MODULE_PATH + ".Owner.send_new_notifications", spec=True)
    def test_should_send_notifications_for_owner(
        self, mock_send_new_notifications, mock_send_queued_messages_for_webhooks
    ):
        # given
        owner = OwnerFactory()
        # when
        tasks.send_new_notifications_for_owner(owner.pk)
        # then
        self.assertTrue(mock_send_new_notifications.called)
        self.assertTrue(mock_send_queued_messages_for_webhooks.called)

    @patch(MODULE_PATH + ".send_queued_messages_for_webhooks", spec=True)
    @patch(MODULE_PATH + ".FuelAlertConfig.send_new_notifications", spec=True)
    def test_should_send_fuel_notifications(
        self, mock_send_new_notifications, mock_send_queued_messages_for_webhooks
    ):
        # given
        config = FuelAlertConfigFactory()
        # when
        tasks.send_structure_fuel_notifications_for_config(config.pk)
        # then
        self.assertTrue(mock_send_new_notifications.called)
        self.assertTrue(mock_send_queued_messages_for_webhooks.called)

    @patch(MODULE_PATH + ".send_queued_messages_for_webhooks", spec=True)
    @patch(MODULE_PATH + ".JumpFuelAlertConfig.send_new_notifications", spec=True)
    def test_should_send_jump_fuel_notifications(
        self, mock_send_new_notifications, mock_send_queued_messages_for_webhooks
    ):
        # given
        config = JumpFuelAlertConfigFactory()
        # when
        tasks.send_jump_fuel_notifications_for_config(config.pk)
        # then
        self.assertTrue(mock_send_new_notifications.called)
        self.assertTrue(mock_send_queued_messages_for_webhooks.called)

    @patch(MODULE_PATH + ".send_messages_for_webhook", spec=True)
    @patch(MODULE_PATH + ".Webhook.queue_size", spec=True)
    def test_should_send_queued_messages_to_webhooks_1(
        self, mock_queue_size, mock_send_messages_for_webhook
    ):
        # given
        mock_queue_size.return_value = 1
        webhook_1 = WebhookFactory()
        webhook_2 = WebhookFactory()
        # when
        tasks.send_queued_messages_for_webhooks([webhook_1, webhook_2])
        # then
        called_webhook_pks = {
            obj[1]["kwargs"]["webhook_pk"]
            for obj in mock_send_messages_for_webhook.apply_async.call_args_list
        }
        expected = {webhook_1.pk, webhook_2.pk}
        self.assertSetEqual(called_webhook_pks, expected)

    @patch(MODULE_PATH + ".send_messages_for_webhook", spec=True)
    @patch(MODULE_PATH + ".Webhook.queue_size", spec=True)
    def test_should_send_queued_messages_to_webhooks_2(
        self, mock_queue_size, mock_send_messages_for_webhook
    ):
        # given
        mock_queue_size.return_value = 0
        webhook_1 = WebhookFactory()
        webhook_2 = WebhookFactory()
        # when
        tasks.send_queued_messages_for_webhooks([webhook_1, webhook_2])
        # then
        called_webhook_pks = {
            obj[1]["kwargs"]["webhook_pk"]
            for obj in mock_send_messages_for_webhook.apply_async.call_args_list
        }
        expected = set()
        self.assertSetEqual(called_webhook_pks, expected)


class TestGetUser(NoSocketsTestCase):
    def test_should_return_user(self):
        # given
        user = UserFactory()
        # when
        result = tasks._get_user(user.pk)
        # then
        self.assertEqual(result, user)

    def test_should_return_none_when_not_found(self):
        # when
        result = tasks._get_user(generate_invalid_pk(User))
        # then
        self.assertIsNone(result)

    def test_should_return_none_when_called_with_none(self):
        # when
        result = tasks._get_user(None)
        # then
        self.assertIsNone(result)
