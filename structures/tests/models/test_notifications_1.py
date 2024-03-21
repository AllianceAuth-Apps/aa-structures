import datetime as dt
from unittest.mock import patch

from django.utils.timezone import now

from app_utils.testing import NoSocketsTestCase

from structures.core.notification_types import NotificationType
from structures.models import Notification, Webhook
from structures.tests.testdata.factories import (
    EveCorporationInfoFactory,
    EveEntityCorporationFactory,
    NotificationFactory,
    OwnerFactory,
    StarbaseFactory,
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


class TestNotification(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        cls.owner = OwnerFactory()
        load_notification_entities(cls.owner)

    def test_str(self):
        # given
        obj = Notification.objects.get(notification_id=1000000403)
        # when/then
        self.assertEqual(str(obj), "1000000403:MoonminingExtractionFinished")

    def test_get_parsed_text(self):
        # given
        obj = Notification.objects.get(notification_id=1000000404)
        # when
        parsed_text = obj.parsed_text()
        # then
        self.assertEqual(parsed_text["autoTime"], 132186924601059151)
        self.assertEqual(parsed_text["structureName"], "Dummy")
        self.assertEqual(parsed_text["solarSystemID"], 30002537)

    def test_is_npc_attacking(self):
        for notification_id, expected in [
            (1000000509, False),
            (1000010509, True),
            (1000010601, True),
        ]:
            obj = Notification.objects.get(notification_id=notification_id)
            with self.subTest(notification=str(obj)):
                self.assertIs(obj.is_npc_attacking(), expected)

    @patch(MODULE_PATH + ".STRUCTURES_REPORT_NPC_ATTACKS", True)
    def test_filter_npc_attacks_1(self):
        # NPC reporting allowed and not a NPC attacker
        obj = Notification.objects.get(notification_id=1000000509)
        self.assertFalse(obj.filter_for_npc_attacks())

        # NPC reporting allowed and a NPC attacker
        obj = Notification.objects.get(notification_id=1000010509)
        self.assertFalse(obj.filter_for_npc_attacks())

    @patch(MODULE_PATH + ".STRUCTURES_REPORT_NPC_ATTACKS", False)
    def test_filter_npc_attacks_2(self):
        # NPC reporting not allowed and not a NPC attacker
        obj = Notification.objects.get(notification_id=1000000509)
        self.assertFalse(obj.filter_for_npc_attacks())

        # NPC reporting not allowed and a NPC attacker
        obj = Notification.objects.get(notification_id=1000010509)
        self.assertTrue(obj.filter_for_npc_attacks())

    def test_can_be_rendered_1(self):
        for notif_type in NotificationType.values:
            with self.subTest(notification_type=notif_type):
                notif = Notification.objects.filter(notif_type=notif_type).first()
                if notif:
                    self.assertTrue(notif.can_be_rendered)

    def test_can_be_rendered_2(self):
        structure = StructureFactory(owner=self.owner, id=1000000000001)
        for notif_type in [
            NotificationType.STRUCTURE_REFUELED_EXTRA,
            NotificationType.TOWER_REFUELED_EXTRA,
        ]:
            with self.subTest(notification_type=notif_type):
                notif = Notification.create_from_structure(structure, notif_type)
                if notif:
                    self.assertTrue(notif.can_be_rendered)

    def test_can_be_rendered_3(self):
        for notif_type in ["UnknownNotificationType"]:
            with self.subTest(notification_type=notif_type):
                notif = Notification.objects.filter(notif_type=notif_type).first()
                if notif:
                    self.assertFalse(notif.can_be_rendered)


class TestNotificationFilterForAllianceLevel(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):  # TODO: Refactor so it works with setUpTestData()
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        cls.owner = OwnerFactory()
        load_notification_entities(cls.owner)

    def test_should_not_filter_non_alliance_notifications_1(self):
        # given
        self.owner.is_alliance_main = False
        self.owner.save()
        notifs = self.owner.notification_set.exclude(
            notif_type__in=NotificationType.relevant_for_alliance_level()
        )
        # when/then
        for notif in notifs:
            with self.subTest(notif=str(notif)):
                self.assertFalse(notif.filter_for_alliance_level())

    def test_should_not_filter_non_alliance_notifications_2(self):
        # given
        self.owner.is_alliance_main = True
        self.owner.save()
        notifs = self.owner.notification_set.exclude(
            notif_type__in=NotificationType.relevant_for_alliance_level()
        )
        # when/then
        for notif in notifs:
            with self.subTest(notif=str(notif)):
                self.assertFalse(notif.filter_for_alliance_level())

    def test_should_filter_alliance_notifications(self):
        # given
        self.owner.is_alliance_main = False
        self.owner.save()
        notifs = self.owner.notification_set.filter(
            notif_type__in=NotificationType.relevant_for_alliance_level()
        )
        # when/then
        for notif in notifs:
            with self.subTest(notif=str(notif)):
                self.assertTrue(notif.filter_for_alliance_level())

    def test_should_not_filter_alliance_notifications_1(self):
        # given
        self.owner.is_alliance_main = True
        self.owner.save()
        notifs = self.owner.notification_set.filter(
            notif_type__in=NotificationType.relevant_for_alliance_level()
        )
        # when/then
        for notif in notifs:
            with self.subTest(notif=str(notif)):
                self.assertFalse(notif.filter_for_alliance_level())

    def test_should_not_filter_alliance_notifications_2(self):
        # given
        self.owner.is_alliance_main = True
        self.owner.save()
        notifs = self.owner.notification_set.filter(
            notif_type__in=NotificationType.relevant_for_alliance_level()
        )
        # when/then
        for notif in notifs:
            with self.subTest(notif=str(notif)):
                self.assertFalse(notif.filter_for_alliance_level())

    def test_should_not_filter_alliance_notifications_3(self):
        # given
        corporation = EveCorporationInfoFactory(create_alliance=False)
        owner = OwnerFactory(corporation=corporation, is_alliance_main=True)
        load_notification_entities(owner)
        notifs = self.owner.notification_set.filter(
            notif_type__in=NotificationType.relevant_for_alliance_level()
        )
        # when/then
        for notif in notifs:
            with self.subTest(notif=str(notif)):
                self.assertFalse(notif.filter_for_alliance_level())


class TestNotificationCreateFromStructure(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        EveEntityCorporationFactory(id=1000137, name="DED")
        cls.owner = OwnerFactory()

    def test_should_create_notification_for_structure_fuel_alerts(self):
        # given
        structure = StructureFactory(owner=self.owner)
        # when
        notif = Notification.create_from_structure(
            structure, notif_type=NotificationType.STRUCTURE_FUEL_ALERT
        )
        # then
        self.assertIsInstance(notif, Notification)
        self.assertTrue(notif.is_temporary)
        self.assertAlmostEqual(notif.timestamp, now(), delta=dt.timedelta(seconds=10))
        self.assertAlmostEqual(
            notif.last_updated, now(), delta=dt.timedelta(seconds=10)
        )
        self.assertEqual(notif.owner, structure.owner)
        self.assertEqual(notif.sender_id, 1000137)
        self.assertEqual(notif.notif_type, NotificationType.STRUCTURE_FUEL_ALERT)

    def test_should_create_notification_for_tower_fuel_alerts(self):
        # given
        structure = StarbaseFactory(owner=self.owner)
        # when
        notif = Notification.create_from_structure(
            structure, notif_type=NotificationType.TOWER_RESOURCE_ALERT_MSG
        )
        # then
        self.assertIsInstance(notif, Notification)
        self.assertTrue(notif.is_temporary)
        self.assertAlmostEqual(notif.timestamp, now(), delta=dt.timedelta(seconds=10))
        self.assertAlmostEqual(
            notif.last_updated, now(), delta=dt.timedelta(seconds=10)
        )
        self.assertEqual(notif.owner, structure.owner)
        self.assertEqual(notif.sender_id, 1000137)
        self.assertEqual(notif.notif_type, NotificationType.TOWER_RESOURCE_ALERT_MSG)

    def test_should_create_notification_with_additional_params(self):
        # given
        structure = StructureFactory(owner=self.owner)
        # when
        notif = Notification.create_from_structure(
            structure, notif_type=NotificationType.STRUCTURE_FUEL_ALERT, is_read=True
        )
        # then
        self.assertIsInstance(notif, Notification)
        self.assertEqual(notif.notif_type, NotificationType.STRUCTURE_FUEL_ALERT)
        self.assertTrue(notif.is_read)

    def test_should_raise_error_when_text_is_missing(self):
        # given
        structure = StructureFactory(owner=self.owner)
        # when/then
        with self.assertRaises(ValueError):
            Notification.create_from_structure(
                structure, notif_type=NotificationType.STRUCTURE_LOST_ARMOR
            )


class TestNotificationRelevantWebhooks(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()

    def test_should_return_owner_webhooks_for_non_structure_notif(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.CHAR_APP_ACCEPT_MSG]
        )
        owner = OwnerFactory(webhooks=[webhook])
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.CHAR_APP_ACCEPT_MSG
        )
        # when
        result_qs = notif.relevant_webhooks()
        # then
        self.assertQuerysetEqual(result_qs, Webhook.objects.filter(pk=webhook.pk))

    def test_should_return_no_webhooks(self):
        # given
        owner = OwnerFactory(webhooks=False)
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.CHAR_APP_ACCEPT_MSG
        )
        # when
        result_qs = notif.relevant_webhooks()
        # then
        self.assertQuerysetEqual(result_qs, Webhook.objects.none())

    def test_should_return_owner_webhooks_for_structure_notif(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_UNDER_ATTACK]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = StructureFactory(owner=owner)
        notif = NotificationFactory(
            owner=owner,
            notif_type=NotificationType.STRUCTURE_UNDER_ATTACK,
            text_from_dict={
                "allianceID": 3011,
                "allianceLinkData": ["showinfo", 16159, 3011],
                "allianceName": "Big Bad Alliance",
                "armorPercentage": 98.65129050962584,
                "charID": 1011,
                "corpLinkData": ["showinfo", 2, 2011],
                "corpName": "Bad Company",
                "hullPercentage": 100.0,
                "shieldPercentage": 4.704536686417284e-14,
                "solarsystemID": structure.eve_solar_system_id,
                "structureID": structure.id,
                "structureShowInfoData": [
                    "showinfo",
                    structure.eve_type_id,
                    structure.id,
                ],
                "structureTypeID": structure.eve_type_id,
            },
        )
        # when
        result_qs = notif.relevant_webhooks()
        # then
        self.assertQuerysetEqual(result_qs, Webhook.objects.filter(pk=webhook.pk))

    def test_should_return_structure_webhooks_for_structure_notif(self):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_UNDER_ATTACK]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = StructureFactory(owner=owner)
        webhook_structure = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_UNDER_ATTACK]
        )
        structure.webhooks.add(webhook_structure)
        notif = NotificationFactory(
            owner=owner,
            notif_type=NotificationType.STRUCTURE_UNDER_ATTACK,
            text_from_dict={
                "allianceID": 3011,
                "allianceLinkData": ["showinfo", 16159, 3011],
                "allianceName": "Big Bad Alliance",
                "armorPercentage": 98.65129050962584,
                "charID": 1011,
                "corpLinkData": ["showinfo", 2, 2011],
                "corpName": "Bad Company",
                "hullPercentage": 100.0,
                "shieldPercentage": 4.704536686417284e-14,
                "solarsystemID": structure.eve_solar_system_id,
                "structureID": structure.id,
                "structureShowInfoData": [
                    "showinfo",
                    structure.eve_type_id,
                    structure.id,
                ],
                "structureTypeID": structure.eve_type_id,
            },
        )
        # when
        result_qs = notif.relevant_webhooks()
        # then
        self.assertQuerysetEqual(
            result_qs, Webhook.objects.filter(pk=webhook_structure.pk)
        )

    def test_should_return_owner_webhooks_when_notif_has_multiple_structures(self):
        # given
        webhook_owner = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REINFORCEMENT_CHANGED]
        )
        owner = OwnerFactory(webhooks=[webhook_owner])
        structure_1 = StructureFactory(owner=owner)
        webhook_structure = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REINFORCEMENT_CHANGED]
        )
        structure_1.webhooks.add(webhook_structure)
        structure_2 = StructureFactory(owner=owner)
        webhook_structure = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REINFORCEMENT_CHANGED]
        )
        structure_2.webhooks.add(webhook_structure)
        notif = NotificationFactory(
            owner=owner,
            notif_type=NotificationType.STRUCTURE_REINFORCEMENT_CHANGED,
            text_from_dict={
                "allStructureInfo": [
                    [
                        structure_1.id,
                        structure_1.name,
                        structure_1.eve_type_id,
                    ],
                    [
                        structure_2.id,
                        structure_2.name,
                        structure_2.eve_type_id,
                    ],
                ],
                "hour": 19,
                "numStructures": 2,
                "timestamp": 132141703753688216,
                "weekday": 255,
            },
        )
        # when
        result_qs = notif.relevant_webhooks()
        # then
        self.assertQuerysetEqual(result_qs, Webhook.objects.filter(pk=webhook_owner.pk))


class TestNotificationSendToConfiguredWebhooks(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_send_to_webhook(self, mock_send_to_webhook):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA]
        )
        owner = OwnerFactory(webhooks=[webhook])
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_configured_webhooks()
        # then
        self.assertTrue(result)
        self.assertTrue(mock_send_to_webhook.called)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_send_to_multiple_webhooks(self, mock_send_to_webhook):
        # given
        webhook_1 = WebhookFactory(
            notification_types=[
                NotificationType.STRUCTURE_REFUELED_EXTRA,
                NotificationType.STRUCTURE_ANCHORING,
            ]
        )
        webhook_2 = WebhookFactory(
            notification_types=[
                NotificationType.STRUCTURE_REFUELED_EXTRA,
                NotificationType.STRUCTURE_DESTROYED,
            ]
        )
        owner = OwnerFactory(webhooks=[webhook_1, webhook_2])
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_configured_webhooks()
        # then
        self.assertTrue(result)
        self.assertEqual(mock_send_to_webhook.call_count, 2)
        webhook_pks = {call[0][0].pk for call in mock_send_to_webhook.call_args_list}
        self.assertSetEqual(webhook_pks, {webhook_1.pk, webhook_2.pk})

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_not_send_when_webhooks_are_inactive(self, mock_send_to_webhook):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA],
            is_active=False,
        )
        owner = OwnerFactory(webhooks=[webhook])
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_configured_webhooks()
        # then
        self.assertIsNone(result)
        self.assertFalse(mock_send_to_webhook.called)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_not_send_when_notif_types_dont_match(self, mock_send_to_webhook):
        # given
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_UNDER_ATTACK]
        )
        owner = OwnerFactory(webhooks=[webhook])
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_configured_webhooks()
        # then
        self.assertIsNone(result)
        self.assertFalse(mock_send_to_webhook.called)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_return_false_when_sending_failed(self, mock_send_to_webhook):
        # given
        mock_send_to_webhook.return_value = False
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA]
        )
        owner = OwnerFactory(webhooks=[webhook])
        notif = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_configured_webhooks()
        # then
        self.assertFalse(result)
        self.assertTrue(mock_send_to_webhook.called)

    @patch(MODULE_PATH + ".Notification.send_to_webhook")
    def test_should_send_to_structure_webhook(self, mock_send_to_webhook):
        # given
        webhook_owner = WebhookFactory(notification_types=[])
        owner = OwnerFactory(webhooks=[webhook_owner])
        structure = StructureFactory(owner=owner)
        webhook_structure = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_UNDER_ATTACK]
        )
        structure.webhooks.add(webhook_structure)
        notif = NotificationFactory(
            owner=owner,
            notif_type=NotificationType.STRUCTURE_UNDER_ATTACK,
            text_from_dict={
                "allianceID": 3011,
                "allianceLinkData": ["showinfo", 16159, 3011],
                "allianceName": "Big Bad Alliance",
                "armorPercentage": 98.65129050962584,
                "charID": 1011,
                "corpLinkData": ["showinfo", 2, 2011],
                "corpName": "Bad Company",
                "hullPercentage": 100.0,
                "shieldPercentage": 4.704536686417284e-14,
                "solarsystemID": structure.eve_solar_system_id,
                "structureID": structure.id,
                "structureShowInfoData": [
                    "showinfo",
                    structure.eve_type_id,
                    structure.id,
                ],
                "structureTypeID": structure.eve_type_id,
            },
        )
        # when
        result = notif.send_to_configured_webhooks()
        # then
        self.assertTrue(result)
        self.assertTrue(mock_send_to_webhook.called)


@patch(MODULE_PATH + ".Webhook.send_message")
class TestNotificationSendToWebhook(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        EveEntityCorporationFactory(id=1000137, name="DED")

    def test_should_override_ping_type(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = StructureFactory(owner=owner)
        notif = Notification.create_from_structure(
            structure, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        notif.send_to_configured_webhooks(ping_type_override=Webhook.PingType.HERE)
        # then
        self.assertTrue(mock_send_message.called)
        _, kwargs = mock_send_message.call_args
        self.assertIn("@here", kwargs["content"])

    def test_should_override_color(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory(
            notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA]
        )
        owner = OwnerFactory(webhooks=[webhook])
        structure = StructureFactory(owner=owner)
        notif = Notification.create_from_structure(
            structure, notif_type=NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        notif.send_to_configured_webhooks(
            use_color_override=True, color_override=Webhook.Color.DANGER
        )
        # then
        self.assertTrue(mock_send_message.called)
        _, kwargs = mock_send_message.call_args
        self.assertEqual(kwargs["embeds"][0].color, Webhook.Color.DANGER)


@patch(MODULE_PATH + ".Webhook.send_message", spec=True)
class TestNotificationSendMessage(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):  # Can not be setUpTestData due to conflict with redis client
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        cls.owner = OwnerFactory(is_alliance_main=True)
        cls.webhook = cls.owner.webhooks.first()
        load_notification_entities(cls.owner)

    def test_can_send_message_normal(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        obj = clone_notification(Notification.objects.get(notification_id=1000020601))
        # when
        result = obj.send_to_webhook(self.webhook)
        # then
        self.assertTrue(result)
        _, kwargs = mock_send_message.call_args
        self.assertIsNotNone(kwargs["content"])
        self.assertIsNotNone(kwargs["embeds"])

    def test_should_mark_notification_as_sent_when_successful(self, mock_send_message):
        # given
        mock_send_message.return_value = True
        obj = NotificationFactory(owner=self.owner)
        # when
        obj.send_to_webhook(self.webhook)
        # then
        obj.refresh_from_db()
        self.assertTrue(obj.is_sent)

    def test_should_not_mark_notification_as_sent_when_error(self, mock_send_message):
        # given
        mock_send_message.return_value = 0
        obj = NotificationFactory(owner=self.owner)
        # when
        obj.send_to_webhook(self.webhook)
        # then
        obj.refresh_from_db()
        self.assertFalse(obj.is_sent)

    def test_can_send_all_notification_types(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        types_tested = set()
        # when /then
        for notif in Notification.objects.all():
            obj = clone_notification(notif)
            with self.subTest(notif_type=obj.notif_type):
                if obj.notif_type in NotificationType.values:
                    self.assertFalse(obj.is_sent)
                    self.assertTrue(obj.send_to_webhook(self.webhook))
                    types_tested.add(obj.notif_type)

        # make sure we have tested all existing esi notification types
        self.assertSetEqual(NotificationType.esi_notifications(), types_tested)

    def test_should_create_notification_for_structure_refueled(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        structure = StructureFactory(owner=self.owner, id=1000000000001)
        notif = Notification.create_from_structure(
            structure, NotificationType.STRUCTURE_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_webhook(self.webhook)
        # then
        self.assertTrue(result)

    def test_should_create_notification_for_tower_refueled(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        structure = StarbaseFactory(owner=self.owner, id=1300000000001)
        notif = Notification.create_from_structure(
            structure, NotificationType.TOWER_REFUELED_EXTRA
        )
        # when
        result = notif.send_to_webhook(self.webhook)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".STRUCTURES_DEFAULT_LANGUAGE", "en")
    def test_send_notification_without_existing_structure(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        obj = clone_notification(Notification.objects.get(notification_id=1000000505))
        # when
        obj.send_to_webhook(self.webhook)
        # then
        embed = mock_send_message.call_args[1]["embeds"][0]
        self.assertEqual(
            embed.description[:39], "The Astrahus **(unknown)** in [Amamake]"
        )

    @patch(MODULE_PATH + ".STRUCTURES_DEFAULT_LANGUAGE", "en")
    def test_notification_with_null_aggressor_alliance(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        obj = clone_notification(Notification.objects.get(notification_id=1000020601))
        # when
        result = obj.send_to_webhook(self.webhook)
        # then
        self.assertTrue(result)

    @patch(MODULE_PATH + ".STRUCTURES_NOTIFICATION_SET_AVATAR", True)
    def test_can_send_message_with_setting_avatar(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        obj = clone_notification(Notification.objects.get(notification_id=1000020601))
        # when
        result = obj.send_to_webhook(self.webhook)
        # then
        self.assertTrue(result)
        _, kwargs = mock_send_message.call_args
        self.assertIsNotNone(kwargs["avatar_url"])
        self.assertIsNotNone(kwargs["username"])

    @patch(MODULE_PATH + ".STRUCTURES_NOTIFICATION_SET_AVATAR", False)
    def test_can_send_message_without_setting_avatar(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        obj = clone_notification(Notification.objects.get(notification_id=1000020601))
        # when
        result = obj.send_to_webhook(self.webhook)
        # then
        self.assertTrue(result)
        _, kwargs = mock_send_message.call_args
        self.assertIsNone(kwargs["avatar_url"])
        self.assertIsNone(kwargs["username"])


@patch(MODULE_PATH + ".Webhook.send_message", spec=True)
class TestNotificationPings(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        corporation = EveEntityCorporationFactory()
        cls.notif_params = {
            "notif_type": NotificationType.BILLING_I_HUB_BILL_ABOUT_TO_EXPIRE,
            "text_from_dict": {
                "billID": 24803231,
                "corpID": corporation.id,
                "dueDate": 132936111600000000,
                "solarSystemID": 30000474,
            },
        }

    def test_can_ping(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook = WebhookFactory()
        owner = OwnerFactory(webhooks=[webhook])
        obj = NotificationFactory(owner=owner, **self.notif_params)
        # when
        result = obj.send_to_webhook(webhook)
        # then
        self.assertTrue(result)
        _, kwargs = mock_send_message.call_args
        self.assertIn("@everyone", kwargs["content"])

    def test_can_disable_pinging_webhook(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook_no_pings = WebhookFactory(has_default_pings_enabled=False)
        owner = OwnerFactory(webhooks=[webhook_no_pings])
        obj = NotificationFactory(owner=owner, **self.notif_params)
        # when
        result = obj.send_to_webhook(webhook_no_pings)
        self.assertTrue(result)
        _, kwargs = mock_send_message.call_args
        self.assertNotIn("@everyone", kwargs["content"])

    def test_can_disable_pinging_owner(self, mock_send_message):
        # given
        mock_send_message.return_value = 1
        webhook_normal = WebhookFactory()
        owner = OwnerFactory(has_default_pings_enabled=False, webhooks=[webhook_normal])
        obj = NotificationFactory(owner=owner, **self.notif_params)
        # when
        result = obj.send_to_webhook(webhook_normal)
        # then
        self.assertTrue(result)
        _, kwargs = mock_send_message.call_args
        self.assertNotIn("@everyone", kwargs["content"])
