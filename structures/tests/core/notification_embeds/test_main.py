import datetime as dt

import dhooks_lite

from django.test import TestCase, override_settings
from django.utils.timezone import now

from app_utils.testing import NoSocketsTestCase

from structures.core.notification_embeds import NotificationBaseEmbed
from structures.core.notification_embeds.billing_embeds import BillType
from structures.core.notification_embeds.tower_embeds import (
    NotificationTowerReinforcedExtra,
)
from structures.core.notification_embeds.war_embeds import (
    NotificationWarCorporationBecameEligible,
)
from structures.core.notification_types import NotificationType
from structures.models.notifications import Notification, Webhook
from structures.tests.testdata.factories import (
    EveAllianceInfoFactory,
    EveCorporationInfoFactory,
    EveEntityAllianceFactory,
    EveEntityCorporationFactory,
    GeneratedNotificationFactory,
    NotificationFactory,
    OwnerFactory,
    StarbaseFactory,
    StructureFactory,
    UserMainDefaultOwnerFactory,
)
from structures.tests.testdata.helpers import (
    load_eve_entities,
    load_notification_entities,
    markdown_to_plain,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.core.notification_embeds"


class TestBilType(TestCase):
    def test_should_create_from_valid_id(self):
        self.assertEqual(BillType.to_enum(7), BillType.INFRASTRUCTURE_HUB)

    def test_should_create_from_invalid_id(self):
        for bill_id in range(7):
            with self.subTest(bill_id=bill_id):
                self.assertEqual(BillType.to_enum(bill_id), BillType.UNKNOWN)


class TestNotificationEmbeds(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory()

    def test_should_create_obj_from_notification(self):
        # given
        notification = NotificationFactory(
            owner=self.owner,
            notification_id=1000000999,
            notif_type=NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE,
        )
        # when
        notification_embed = NotificationBaseEmbed.create(notification)
        # then
        self.assertIsInstance(
            notification_embed, NotificationWarCorporationBecameEligible
        )
        self.assertEqual(str(notification_embed), "1000000999:CorpBecameWarEligible")

    def test_should_require_notification_for_init(self):
        with self.assertRaises(TypeError):
            NotificationBaseEmbed(notification="dummy")

    def test_should_require_notification_for_factory(self):
        with self.assertRaises(TypeError):
            NotificationBaseEmbed.create(notification="dummy")


class TestNotificationEmbedsGenerate(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        load_eve_entities()
        alliance = EveAllianceInfoFactory(alliance_id=3001)
        corporation = EveCorporationInfoFactory(corporation_id=2001, alliance=alliance)
        cls.owner = OwnerFactory(corporation=corporation)
        load_notification_entities(cls.owner)

    def test_should_generate_embed_from_notification(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertIsInstance(discord_embed, dhooks_lite.Embed)
        self.assertEqual(discord_embed.footer.text, "Eve Online")
        self.assertIn("eve_symbol_128.png", discord_embed.footer.icon_url)

    def test_should_generate_embed_from_notification_with_custom_color(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification._color_override = Webhook.Color.SUCCESS
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertIsInstance(discord_embed, dhooks_lite.Embed)
        self.assertEqual(discord_embed.color, Webhook.Color.SUCCESS)

    def test_should_generate_embed_from_notification_without_custom_color(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertIsInstance(discord_embed, dhooks_lite.Embed)
        self.assertNotEqual(discord_embed.color, Webhook.Color.SUCCESS)

    def test_should_generate_embed_from_notification_with_ping_type_override(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification._ping_type_override = Webhook.PingType.EVERYONE
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        notification_embed.generate_embed()
        # then
        self.assertEqual(notification_embed.ping_type, Webhook.PingType.EVERYONE)

    def test_should_generate_embed_for_all_supported_esi_notification_types_minimal(
        self,
    ):
        for notif_type in NotificationType.esi_notifications():
            with self.subTest(notif_type=notif_type):
                # given
                notif = (
                    Notification.objects.select_related("owner", "sender")
                    .filter(notif_type=notif_type)
                    .first()
                )
                self.assertIsInstance(notif, Notification)
                notif_embed = NotificationBaseEmbed.create(notif)

                # when
                obj = notif_embed.generate_embed()

                # then
                self.assertIsInstance(obj, dhooks_lite.Embed)

    def test_should_generate_embed_for_all_supported_esi_notification_types_normal(
        self,
    ):
        # Pre-generate structures referenced in notifications
        StructureFactory(owner=self.owner, id=1000000000001, eve_type_name="Astrahus")
        StructureFactory(owner=self.owner, id=1000000000002, eve_type_name="Athanor")

        for notif_type in NotificationType.esi_notifications():
            with self.subTest(notif_type=notif_type):
                # given
                notif = (
                    Notification.objects.select_related("owner", "sender")
                    .filter(notif_type=notif_type)
                    .first()
                )
                self.assertIsInstance(notif, Notification)
                notif_embed = NotificationBaseEmbed.create(notif)

                # when
                obj = notif_embed.generate_embed()

                # then
                self.assertIsInstance(obj, dhooks_lite.Embed)
                self.assertTrue(obj.description)

    def test_should_set_ping_everyone_for_color_danger(self):
        # given
        notification = Notification.objects.get(notification_id=1000000513)
        notification_embed = NotificationBaseEmbed.create(notification)
        notification_embed._color = Webhook.Color.DANGER
        # when
        notification_embed.generate_embed()
        # then
        self.assertEqual(notification_embed.ping_type, Webhook.PingType.EVERYONE)

    def test_should_set_ping_everyone_for_color_warning(self):
        # given
        notification = Notification.objects.get(notification_id=1000000513)
        notification_embed = NotificationBaseEmbed.create(notification)
        notification_embed._color = Webhook.Color.WARNING
        # when
        notification_embed.generate_embed()
        # then
        self.assertEqual(notification_embed.ping_type, Webhook.PingType.HERE)

    def test_should_not_set_ping_everyone_for_color_info(self):
        # given
        notification = Notification.objects.get(notification_id=1000000513)
        notification_embed = NotificationBaseEmbed.create(notification)
        notification_embed._color = Webhook.Color.INFO
        # when
        notification_embed.generate_embed()
        # then
        self.assertEqual(notification_embed.ping_type, Webhook.PingType.NONE)

    def test_should_not_set_ping_everyone_for_color_success(self):
        # given
        notification = Notification.objects.get(notification_id=1000000513)
        notification_embed = NotificationBaseEmbed.create(notification)
        notification_embed._color = Webhook.Color.SUCCESS
        # when
        notification_embed.generate_embed()
        # then
        self.assertEqual(notification_embed.ping_type, Webhook.PingType.NONE)

    @override_settings(DEBUG=True)
    def test_should_set_footer_in_developer_mode(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertTrue(discord_embed.footer)

    def test_should_set_special_footer_for_generated_notifications(self):
        # given
        structure = StructureFactory(owner=self.owner)
        notification = Notification.create_from_structure(
            structure, notif_type=NotificationType.STRUCTURE_FUEL_ALERT
        )
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertEqual(discord_embed.footer.text, "Structures")
        self.assertIn("structures_logo.png", discord_embed.footer.icon_url)

    def test_should_not_break_with_too_large_description(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification_embed = NotificationBaseEmbed.create(notification)
        notification_embed._description = "x" * 2049
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertIsInstance(discord_embed, dhooks_lite.Embed)

    def test_should_not_break_with_too_large_title(self):
        # given
        notification = Notification.objects.get(notification_id=1000000403)
        notification_embed = NotificationBaseEmbed.create(notification)
        notification_embed._title = "x" * 257
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        self.assertIsInstance(discord_embed, dhooks_lite.Embed)


class TestNotificationEmbedsClasses(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        user = UserMainDefaultOwnerFactory()
        cls.owner = OwnerFactory(user=user)
        cls.moon_id = 40161465
        cls.solar_system_id = 30002537
        cls.type_id = 16213
        EveEntityCorporationFactory(id=1000137, name="DED")

    def test_should_generate_embed_for_normal_tower_resource_alert(self):
        # given
        StarbaseFactory(
            owner=self.owner,
            eve_moon_id=self.moon_id,
            eve_solar_system_id=self.solar_system_id,
            eve_type_id=self.type_id,
        )
        data = {
            "corpID": self.owner.corporation.corporation_id,
            "moonID": self.moon_id,
            "solarSystemID": self.solar_system_id,
            "typeID": self.type_id,
            "wants": [{"quantity": 120, "typeID": 4051}],
        }
        notification = NotificationFactory(
            owner=self.owner,
            notif_type=NotificationType.TOWER_RESOURCE_ALERT_MSG,
            text_from_dict=data,
        )
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        description = markdown_to_plain(discord_embed.description)
        self.assertIn("is running out of fuel in 3 hours", description)

    def test_should_generate_embed_for_generated_tower_resource_alert(self):
        # given
        structure = StarbaseFactory(
            owner=self.owner,
            eve_moon_id=self.moon_id,
            eve_solar_system_id=self.solar_system_id,
            eve_type_id=self.type_id,
            fuel_expires_at=now() + dt.timedelta(hours=2, seconds=20),
        )
        notification = Notification.create_from_structure(
            structure=structure, notif_type=NotificationType.TOWER_RESOURCE_ALERT_MSG
        )
        notification_embed = NotificationBaseEmbed.create(notification)
        # when
        discord_embed = notification_embed.generate_embed()
        # then
        description = markdown_to_plain(discord_embed.description)
        self.assertIn("is running out of fuel in 2 hours", description)


class TestGeneratedNotification(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

    def test_should_create_tower_reinforced_embed(self):
        # given
        notif = GeneratedNotificationFactory()
        # when
        obj = NotificationBaseEmbed.create(notif)
        # then
        self.assertIsInstance(obj, NotificationTowerReinforcedExtra)

    def test_should_generate_embed(self):
        # given
        notif = GeneratedNotificationFactory()
        embed = NotificationBaseEmbed.create(notif)
        # when
        obj = embed.generate_embed()
        # then
        self.assertIsInstance(obj, dhooks_lite.Embed)
        starbase = notif.structures.first()
        self.assertIn(starbase.name, obj.description)


class TestEveNotificationEmbeds(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()

    def test_should_create_sov_embed(self):
        # given
        notif = NotificationFactory(
            owner=self.owner,
            sender=EveEntityAllianceFactory(),
            notif_type=NotificationType.SOV_ENTOSIS_CAPTURE_STARTED,
            text_from_dict={"solarSystemID": 30000474, "structureTypeID": 32226},
        )
        embed = NotificationBaseEmbed.create(notif)
        # when
        obj = embed.generate_embed()
        # then
        self.assertTrue(obj.description)

    def test_should_create_sov_embed_without_sender(self):
        # given
        notif = NotificationFactory(
            owner=self.owner,
            sender=None,
            notif_type=NotificationType.SOV_ENTOSIS_CAPTURE_STARTED,
            text_from_dict={"solarSystemID": 30000474, "structureTypeID": 32226},
        )
        embed = NotificationBaseEmbed.create(notif)
        # when
        obj = embed.generate_embed()
        # then
        self.assertTrue(obj.description)
