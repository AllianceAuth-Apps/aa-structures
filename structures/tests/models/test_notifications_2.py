import datetime as dt
from unittest.mock import patch

from django.utils.timezone import now

from app_utils.testing import NoSocketsTestCase

from structures.core.notification_types import NotificationType
from structures.models import FuelAlert, JumpFuelAlert, Notification, Structure, Webhook
from structures.tests.testdata.factories import (
    EveEntityCorporationFactory,
    FuelAlertConfigFactory,
    FuelAlertFactory,
    JumpFuelAlertConfigFactory,
    JumpGateFactory,
    NotificationFactory,
    OwnerFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    WebhookFactory,
)
from structures.tests.testdata.helpers import (
    load_eve_entities,
    load_notification_by_type,
    load_notification_entities,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.models.notifications"


@patch(MODULE_PATH + ".Webhook.send_message", spec=True)
class TestStructureFuelAlerts(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):  # Can not be setUpTestData due to conflict with redis client
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        cls.owner = OwnerFactory()
        load_notification_entities(cls.owner)
        cls.webhook = cls.owner.webhooks.first()

    def test_should_output_str(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(owner=self.owner, fuel_expires_at=None)
        alert = FuelAlertFactory(structure=structure, config=config, hours=36)
        # when
        result = str(alert)
        # then
        self.assertIsInstance(result, str)

    def test_should_send_fuel_notification_for_structure(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        obj = FuelAlert.objects.first()
        self.assertEqual(obj.hours, 36)

    def test_should_not_send_fuel_notification_for_structure_not_burning_fuel(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        StructureFactory(
            owner=self.owner, fuel_expires_at=now() - dt.timedelta(hours=2)
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)

    def test_should_not_send_fuel_notification_that_already_exists(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_message.reset_mock()
        FuelAlertFactory(structure=structure, config=config, hours=36)
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)
        self.assertEqual(FuelAlert.objects.count(), 1)

    def test_should_send_fuel_notification_for_starbase(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        StarbaseFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        obj = FuelAlert.objects.first()
        self.assertEqual(obj.hours, 36)

    def test_should_not_send_fuel_notification_for_starbase_not_burning_fuel(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        StarbaseFactory(
            owner=self.owner,
            state=Structure.State.POS_OFFLINE,
            fuel_expires_at=now() - dt.timedelta(hours=2),
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)

    def test_should_use_configured_ping_type_for_notifications(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(
            start=48,
            end=0,
            repeat=12,
            channel_ping_type=Webhook.PingType.EVERYONE,
        )
        StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        _, kwargs = mock_send_message.call_args
        self.assertIn("@everyone", kwargs["content"])

    def test_should_use_configured_level_for_notifications(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(
            start=48,
            end=0,
            repeat=12,
            color=Webhook.Color.SUCCESS,
        )
        StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        _, kwargs = mock_send_message.call_args
        embed = kwargs["embeds"][0]
        self.assertEqual(embed.color, Webhook.Color.SUCCESS)

    def test_should_send_fuel_notification_at_start(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=12, end=0, repeat=12)
        StructureFactory(
            owner=self.owner,
            fuel_expires_at=now() + dt.timedelta(hours=11, minutes=59, seconds=59),
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        obj = FuelAlert.objects.first()
        self.assertEqual(obj.hours, 12)

    def test_should_not_send_fuel_notifications_before_start(self, mock_send_message):
        # given
        config = FuelAlertConfigFactory(start=12, end=6, repeat=1)
        StructureFactory(
            owner=self.owner,
            fuel_expires_at=now() + dt.timedelta(hours=12, minutes=0, seconds=1),
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)

    def test_should_not_send_fuel_notifications_after_end(self, mock_send_message):
        # given
        config = FuelAlertConfigFactory(start=12, end=6, repeat=1)
        StructureFactory(
            owner=self.owner,
            fuel_expires_at=now() + dt.timedelta(hours=5, minutes=59, seconds=59),
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)

    def test_should_send_fuel_notification_at_start_when_repeat_is_0(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        config = FuelAlertConfigFactory(start=12, end=0, repeat=0)
        StructureFactory(
            owner=self.owner,
            fuel_expires_at=now() + dt.timedelta(hours=11, minutes=59, seconds=59),
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        obj = FuelAlert.objects.first()
        self.assertEqual(obj.hours, 12)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_send_structure_fuel_notification_to_configured_webhook_only(
        self, mock_send_to_webhook, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        webhook_2 = WebhookFactory(
            notification_types=[
                NotificationType.STRUCTURE_DESTROYED,
                NotificationType.TOWER_RESOURCE_ALERT_MSG,
            ]
        )
        self.owner.webhooks.add(webhook_2)
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_to_webhook.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertEqual(config.structure_fuel_alerts.count(), 1)
        self.assertEqual(mock_send_to_webhook.call_count, 1)
        args, _ = mock_send_to_webhook.call_args
        self.assertEqual(args[0], self.webhook)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_send_starbase_fuel_notification_to_configured_webhook_only(
        self, mock_send_to_webhook, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        webhook_2 = WebhookFactory(
            notification_types=[
                NotificationType.STRUCTURE_DESTROYED,
                NotificationType.STRUCTURE_FUEL_ALERT,
            ]
        )
        self.owner.webhooks.add(webhook_2)
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        StarbaseFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=25)
        )
        mock_send_to_webhook.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertEqual(config.structure_fuel_alerts.count(), 1)
        self.assertEqual(mock_send_to_webhook.call_count, 1)
        args, _ = mock_send_to_webhook.call_args
        self.assertEqual(args[0], self.webhook)

    def test_should_remove_alerts_when_config_changes_1(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(owner=self.owner)
        FuelAlertFactory(structure=structure, config=config, hours=36)
        # when
        config.start = 36
        config.save()
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    def test_should_remove_alerts_when_config_changes_2(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(owner=self.owner)
        FuelAlertFactory(structure=structure, config=config, hours=36)
        # when
        config.end = 2
        config.save()
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    def test_should_remove_alerts_when_config_changes_3(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(owner=self.owner)
        FuelAlertFactory(structure=structure, config=config, hours=36)
        # when
        config.repeat = 4
        config.save()
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    def test_should_keep_alerts_when_config_updated_without_change(
        self, mock_send_message
    ):
        # given
        mock_send_message.side_effect = RuntimeError
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(owner=self.owner)
        FuelAlertFactory(structure=structure, config=config, hours=36)
        # when
        config.save()
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 1)

    def test_should_return_correct_webhooks(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook_wrong_type = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_DESTROYED]
        )
        self.owner.webhooks.add(webhook_wrong_type)
        structure = StructureFactory(owner=self.owner)
        webhook_structure = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_FUEL_ALERT]
        )
        structure.webhooks.add(webhook_structure)
        webhook_inactive = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_FUEL_ALERT], is_active=False
        )
        self.owner.webhooks.add(webhook_inactive)
        WebhookFactory(notification_types=[NotificationType.STRUCTURE_FUEL_ALERT])
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        # when
        qs = config.relevant_webhooks()
        # then
        relevant_webhook_pks = qs.values_list("pk", flat=True)
        self.assertSetEqual(
            set(relevant_webhook_pks), {self.webhook.pk, webhook_structure.pk}
        )


@patch(MODULE_PATH + ".Webhook.send_message", spec=True)
class TestJumpFuelAlerts(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        EveEntityCorporationFactory(id=1000137, name="DED")

    def test_should_output_str(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        structure = JumpGateFactory()
        config = JumpFuelAlertConfigFactory(threshold=100)
        alert = structure.jump_fuel_alerts.create(config=config)
        # when
        result = str(alert)
        # then
        self.assertIsInstance(result, str)

    def test_should_send_fuel_notification_for_structure(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100)
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        alert = JumpFuelAlert.objects.first()
        self.assertEqual(alert.structure, structure)
        self.assertEqual(alert.config, config)

    def test_should_not_send_fuel_notification_for_structure_when_not_burning_fuel(
        self, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        JumpGateFactory(owner=owner, fuel_expires_at=None, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100)
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)

    def test_should_handle_no_fuel_situation(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        JumpGateFactory(owner=owner, jump_fuel_quantity=0)
        config = JumpFuelAlertConfigFactory(threshold=100)
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)

    def test_should_not_send_fuel_notification_that_already_exists(
        self, mock_send_message
    ):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100)
        alert = structure.jump_fuel_alerts.create(config=config)
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)
        self.assertEqual(structure.jump_fuel_alerts.count(), 1)
        self.assertEqual(structure.jump_fuel_alerts.first(), alert)

    def test_should_not_send_fuel_notification_if_above_threshold(
        self, mock_send_message
    ):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = JumpGateFactory(owner=owner, jump_fuel_quantity=101)
        config = JumpFuelAlertConfigFactory(threshold=100)
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertFalse(mock_send_message.called)
        self.assertEqual(structure.jump_fuel_alerts.count(), 0)

    def test_should_use_configured_ping_type_for_notifications(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(
            threshold=100, channel_ping_type=Webhook.PingType.EVERYONE
        )
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        _, kwargs = mock_send_message.call_args
        self.assertIn("@everyone", kwargs["content"])

    def test_should_use_configured_level_for_notifications(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100, color=Webhook.Color.SUCCESS)
        mock_send_message.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertTrue(mock_send_message.called)
        _, kwargs = mock_send_message.call_args
        embed = kwargs["embeds"][0]
        self.assertEqual(embed.color, Webhook.Color.SUCCESS)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_send_fuel_notification_to_configured_webhook_only(
        self, mock_send_to_webhook, mock_send_message
    ):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        webhook_other = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_UNDER_ATTACK]
        )
        owner = OwnerFactory(webhooks=[webhook, webhook_other])
        JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100)
        mock_send_to_webhook.reset_mock()
        # when
        config.send_new_notifications()
        # then
        self.assertEqual(config.jump_fuel_alerts.count(), 1)
        self.assertEqual(mock_send_to_webhook.call_count, 1)
        args, _ = mock_send_to_webhook.call_args
        self.assertEqual(args[0], webhook)

    def test_should_remove_alerts_when_config_changes(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100)
        structure.jump_fuel_alerts.create(config=config)
        # when
        config.threshold = 50
        config.save()
        # then
        self.assertEqual(structure.jump_fuel_alerts.count(), 0)

    def test_should_keep_alerts_when_config_updated_without_change(
        self, mock_send_message
    ):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = JumpGateFactory(owner=owner, jump_fuel_quantity=99)
        config = JumpFuelAlertConfigFactory(threshold=100)
        structure.jump_fuel_alerts.create(config=config)
        # when
        config.save()
        # then
        self.assertEqual(structure.jump_fuel_alerts.count(), 1)

    def test_should_return_correct_webhooks(self, mock_send_message):
        # given
        mock_send_message.side_effect = RuntimeError
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        webhook_wrong_type = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_DESTROYED]
        )
        webhook_inactive = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT],
            is_active=False,
        )
        owner = OwnerFactory(webhooks=[webhook, webhook_wrong_type, webhook_inactive])
        structure = JumpGateFactory(owner=owner)
        webhook_structure = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT]
        )
        structure.webhooks.add(webhook_structure)
        WebhookFactory(notification_types=[NotificationType.STRUCTURE_JUMP_FUEL_ALERT])
        config = JumpFuelAlertConfigFactory(threshold=100)
        # when
        qs = config.relevant_webhooks()
        # then
        relevant_webhook_pks = qs.values_list("pk", flat=True)
        self.assertSetEqual(
            set(relevant_webhook_pks), {webhook.pk, webhook_structure.pk}
        )


class TestNotificationRelatedStructures(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        cls.owner = OwnerFactory()

    def test_related_structures_for_structure_notifications(self):
        # given
        structure = StructureFactory(owner=self.owner, id=1000000000001)
        for notif_type in [
            NotificationType.STRUCTURE_ONLINE,
            NotificationType.STRUCTURE_FUEL_ALERT,
            NotificationType.STRUCTURE_SERVICES_OFFLINE,
            NotificationType.STRUCTURE_WENT_LOW_POWER,
            NotificationType.STRUCTURE_WENT_HIGH_POWER,
            NotificationType.STRUCTURE_UNANCHORING,
            NotificationType.STRUCTURE_UNDER_ATTACK,
            NotificationType.STRUCTURE_LOST_SHIELD,
            NotificationType.STRUCTURE_LOST_ARMOR,
            NotificationType.STRUCTURE_DESTROYED,
            NotificationType.OWNERSHIP_TRANSFERRED,
            NotificationType.STRUCTURE_ANCHORING,
        ]:
            with self.subTest(notif_type=notif_type):
                notif = load_notification_by_type(
                    owner=self.owner, notif_type=notif_type
                )
                # when
                result_qs = notif.calc_related_structures()
                # then
                self.assertQuerysetEqual(
                    result_qs, Structure.objects.filter(id=structure.id)
                )

    def test_related_structures_for_moon_notifications(self):
        # given
        structure = StructureFactory(owner=self.owner, id=1000000000002)
        for notif_type in [
            NotificationType.MOONMINING_EXTRACTION_STARTED,
            NotificationType.MOONMINING_EXTRACTION_FINISHED,
            NotificationType.MOONMINING_AUTOMATIC_FRACTURE,
            NotificationType.MOONMINING_EXTRACTION_CANCELLED,
            NotificationType.MOONMINING_LASER_FIRED,
        ]:
            with self.subTest(notif_type=notif_type):
                notif = load_notification_by_type(
                    owner=self.owner, notif_type=notif_type
                )
                # when
                result_qs = notif.calc_related_structures()
                # then
                self.assertQuerysetEqual(
                    result_qs, Structure.objects.filter(id=structure.id)
                )

    def test_related_structures_for_orbital_notifications(self):
        # given
        structure = PocoFactory(owner=self.owner, eve_planet_id=40161469)
        for notif_type in [
            NotificationType.ORBITAL_ATTACKED,
            NotificationType.ORBITAL_REINFORCED,
        ]:
            with self.subTest(notif_type=notif_type):
                notif = load_notification_by_type(
                    owner=self.owner, notif_type=notif_type
                )
                # when
                result_qs = notif.calc_related_structures()
                # then
                self.assertQuerysetEqual(
                    result_qs, Structure.objects.filter(id=structure.id)
                )

    def test_related_structures_for_tower_notifications(self):
        # given
        structure = StarbaseFactory(owner=self.owner, eve_moon_id=40161465)
        for notif_type in [
            NotificationType.TOWER_ALERT_MSG,
            NotificationType.TOWER_RESOURCE_ALERT_MSG,
        ]:
            with self.subTest(notif_type=notif_type):
                notif = load_notification_by_type(
                    owner=self.owner, notif_type=notif_type
                )
                # when
                result_qs = notif.calc_related_structures()
                # then
                self.assertQuerysetEqual(
                    result_qs, Structure.objects.filter(id=structure.id)
                )

    def test_related_structures_for_generated_notifications(self):
        # given
        structure = StarbaseFactory(owner=self.owner, eve_moon_id=40161465)
        for notif_type in [
            NotificationType.STRUCTURE_JUMP_FUEL_ALERT,
            NotificationType.STRUCTURE_REFUELED_EXTRA,
            NotificationType.TOWER_REFUELED_EXTRA,
        ]:
            with self.subTest(notif_type=notif_type):
                notif = Notification.create_from_structure(
                    structure, notif_type=notif_type
                )
                # when
                result_qs = notif.calc_related_structures()
                # then
                self.assertQuerysetEqual(
                    result_qs, Structure.objects.filter(id=structure.id)
                )

    def test_should_update_related_structure_when_it_exists(self):
        # given
        structure = StructureFactory(owner=self.owner)
        notif = NotificationFactory(owner=self.owner)
        # when
        with patch(MODULE_PATH + ".Notification.calc_related_structures") as m:
            m.return_value = Structure.objects.filter(id=structure.id)
            result = notif.update_related_structures()
        # then
        structure_ids = notif.structures.values_list("id", flat=True)
        self.assertSetEqual(set(structure_ids), {structure.id})
        self.assertTrue(result)

    def test_should_not_update_related_structure_when_not_found(self):
        # given
        notif = NotificationFactory(owner=self.owner)
        # when
        with patch(MODULE_PATH + ".Notification.calc_related_structures") as m:
            m.return_value = Structure.objects.none()
            result = notif.update_related_structures()
        # then
        self.assertFalse(result)

    def test_should_return_empty_qs_when_structure_id_is_missing(self):
        # given
        notif = NotificationFactory(
            notif_type=NotificationType.OWNERSHIP_TRANSFERRED.value,
            text_from_dict={
                "charID": 1001,
                "newOwnerCorpID": 2002,
                "oldOwnerCorpID": 2001,
                "solarSystemID": 30002537,
                "structureName": "Test Structure Alpha",
                "structureTypeID": 35832,
            },
        )
        # when
        result_qs = notif.calc_related_structures()
        # then
        self.assertEqual(list(result_qs), [])

    def test_should_return_empty_qs_when_all_structure_info_is_missing(self):
        # given
        notif = NotificationFactory(
            notif_type=NotificationType.STRUCTURE_REINFORCEMENT_CHANGED.value,
            text_from_dict={
                "hour": 19,
                "numStructures": 1,
                "timestamp": 132141703753688216,
                "weekday": 255,
            },
        )
        # when
        result_qs = notif.calc_related_structures()
        # then
        self.assertEqual(list(result_qs), [])

    def test_should_return_empty_qs_when_planet_id_is_missing(self):
        # given
        notif = NotificationFactory(
            notif_type=NotificationType.ORBITAL_ATTACKED.value,
            text_from_dict={
                "aggressorCorpID": 2011,
                "aggressorID": 1011,
                "planetTypeID": 2016,
                "shieldLevel": 0.9821850015653375,
                "solarSystemID": 30002537,
                "typeID": 2233,
            },
        )
        # when
        result_qs = notif.calc_related_structures()
        # then
        self.assertEqual(list(result_qs), [])

    def test_should_return_empty_qs_when_type_id_is_missing(self):
        # given
        notif = NotificationFactory(
            notif_type=NotificationType.ORBITAL_ATTACKED.value,
            text_from_dict={
                "aggressorCorpID": 2011,
                "aggressorID": 1011,
                "planetID": 40161469,
                "planetTypeID": 2016,
                "shieldLevel": 0.9821850015653375,
                "solarSystemID": 30002537,
            },
        )
        # when
        result_qs = notif.calc_related_structures()
        # then
        self.assertEqual(list(result_qs), [])

    def test_should_return_empty_qs_when_moon_id_is_missing(self):
        # given
        notif = NotificationFactory(
            notif_type=NotificationType.TOWER_ALERT_MSG.value,
            text_from_dict={
                "aggressorAllianceID": 3011,
                "aggressorCorpID": 2011,
                "aggressorID": 1011,
                "armorValue": 0.6950949076033535,
                "hullValue": 1.0,
                "shieldValue": 0.3950949076033535,
                "solarSystemID": 30002537,
                "typeID": 16213,
            },
        )
        # when
        result_qs = notif.calc_related_structures()
        # then
        self.assertEqual(list(result_qs), [])

    def test_should_return_empty_qs_when_moon_type_id_is_missing(self):
        # given
        notif = NotificationFactory(
            notif_type=NotificationType.TOWER_ALERT_MSG.value,
            text_from_dict={
                "aggressorAllianceID": 3011,
                "aggressorCorpID": 2011,
                "aggressorID": 1011,
                "armorValue": 0.6950949076033535,
                "hullValue": 1.0,
                "moonID": 40161465,
                "shieldValue": 0.3950949076033535,
                "solarSystemID": 30002537,
            },
        )
        # when
        result_qs = notif.calc_related_structures()
        # then
        self.assertEqual(list(result_qs), [])
