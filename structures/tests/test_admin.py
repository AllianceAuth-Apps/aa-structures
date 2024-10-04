import datetime as dt
from unittest.mock import patch

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.timezone import now

from structures.admin import (
    NotificationAdmin,
    OwnerAdmin,
    OwnerAllianceFilter,
    OwnerCorporationsFilter,
    RenderableNotificationFilter,
    StructureAdmin,
    StructureFuelAlertConfigAdmin,
    WebhookAdmin,
)
from structures.core.notification_types import NotificationType
from structures.models import (
    FuelAlertConfig,
    Notification,
    Owner,
    Structure,
    StructureTag,
    Webhook,
)

from .testdata.factories import (
    EveAllianceInfoFactory,
    EveCorporationInfoFactory,
    FuelAlertConfigFactory,
    NotificationFactory,
    OwnerCharacterFactory,
    OwnerFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    StructureTagFactory,
    SuperuserFactory,
    WebhookFactory,
)
from .testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.admin"


class MockRequest(object):
    def __init__(self, user=None):
        self.user = user


class TestFuelNotificationConfigAdminView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.defaults = {
            "is_enabled": True,
            "channel_ping_type": Webhook.PingType.HERE,
            "color": Webhook.Color.WARNING,
        }
        cls.user = SuperuserFactory()
        load_eveuniverse()

    def test_should_create_new_config(self):
        # given
        self.client.force_login(self.user)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 12, "end": 5, "repeat": 2}},
        )
        # then
        self.assertRedirects(
            response, reverse("admin:structures_fuelalertconfig_changelist")
        )
        self.assertEqual(FuelAlertConfig.objects.count(), 1)

    def test_should_update_existing_config(self):
        # given
        self.client.force_login(self.user)
        config = FuelAlertConfigFactory(start=48, end=24, repeat=12)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_change", args=[config.pk]),
            data={**self.defaults, **{"start": 48, "end": 0, "repeat": 2}},
        )
        # then
        self.assertRedirects(
            response, reverse("admin:structures_fuelalertconfig_changelist")
        )
        self.assertEqual(FuelAlertConfig.objects.count(), 1)

    def test_should_remove_existing_fuel_notifications_when_timing_changed(self):
        # given
        self.client.force_login(self.user)
        config = FuelAlertConfigFactory(start=48, end=24, repeat=12)
        structure = StructureFactory()
        structure.structure_fuel_alerts.create(
            config=config, structure=structure, hours=5
        )
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_change", args=[config.pk]),
            data={**self.defaults, **{"start": 48, "end": 0, "repeat": 2}},
        )
        # then
        self.assertRedirects(
            response, reverse("admin:structures_fuelalertconfig_changelist")
        )
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    def test_should_not_remove_existing_fuel_notifications_on_other_changes(self):
        # given
        self.client.force_login(self.user)
        config = FuelAlertConfigFactory(start=48, end=24, repeat=12)
        structure = StructureFactory()
        structure.structure_fuel_alerts.create(
            config=config, structure=structure, hours=5
        )
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_change", args=[config.pk]),
            data={
                **self.defaults,
                **{"start": 48, "end": 24, "repeat": 12, "is_enabled": False},
            },
        )
        # then
        self.assertRedirects(
            response, reverse("admin:structures_fuelalertconfig_changelist")
        )
        self.assertEqual(structure.structure_fuel_alerts.count(), 1)

    def test_should_not_allow_end_before_start(self):
        # given
        self.client.force_login(self.user)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 1, "end": 2, "repeat": 1}},
        )
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errornote")
        self.assertEqual(FuelAlertConfig.objects.count(), 0)

    def test_should_not_allow_invalid_frequency(self):
        # given
        self.client.force_login(self.user)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 48, "end": 24, "repeat": 36}},
        )
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errornote")
        self.assertEqual(FuelAlertConfig.objects.count(), 0)

    def test_should_not_allow_creating_overlapping(self):
        # given
        self.client.force_login(self.user)
        FuelAlertConfigFactory(start=48, end=24, repeat=12)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 36, "end": 0, "repeat": 8}},
        )
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errornote")
        self.assertEqual(FuelAlertConfig.objects.count(), 1)

    def test_should_work_with_empty_end_field(self):
        # given
        self.client.force_login(self.user)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 36, "repeat": 8}},
        )
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errornote")
        self.assertEqual(FuelAlertConfig.objects.count(), 0)

    def test_should_work_with_empty_start_field(self):
        # given
        self.client.force_login(self.user)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 36, "end": 8}},
        )
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errornote")
        self.assertEqual(FuelAlertConfig.objects.count(), 0)

    def test_should_work_with_empty_repeat_field(self):
        # given
        self.client.force_login(self.user)
        # when
        response = self.client.post(
            reverse("admin:structures_fuelalertconfig_add"),
            data={**self.defaults, **{"start": 36, "end": 8}},
        )
        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errornote")
        self.assertEqual(FuelAlertConfig.objects.count(), 0)


class TestStructureFuelAlertAdmin(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modeladmin = StructureFuelAlertConfigAdmin(
            model=FuelAlertConfig, admin_site=AdminSite()
        )
        load_eveuniverse()

    @patch(MODULE_PATH + ".StructureFuelAlertConfigAdmin.message_user", spec=True)
    @patch(MODULE_PATH + ".tasks", spec=True)
    def test_should_send_fuel_notifications(self, mock_tasks, mock_message_user):
        # given
        config = FuelAlertConfigFactory()
        request = MockRequest()
        queryset = FuelAlertConfig.objects.filter(pk=config.pk)
        # when
        self.modeladmin.send_fuel_notifications(request, queryset)
        # then
        self.assertTrue(mock_tasks.send_queued_messages_for_webhooks.called)
        self.assertTrue(mock_message_user.called)


class TestNotificationAdmin(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.modeladmin = NotificationAdmin(model=Notification, admin_site=AdminSite())
        cls.user = SuperuserFactory()
        cls.owner = OwnerFactory()

    def test_structures_when_structure_related(self):
        # given
        obj = NotificationFactory(
            owner=self.owner, notif_type=NotificationType.STRUCTURE_LOST_SHIELD
        )
        # when
        result = self.modeladmin._structures(obj)
        self.assertEqual(result, "?")

    def test_structures_when_not_structure_related(self):
        # given
        obj = NotificationFactory(
            owner=self.owner, notif_type=NotificationType.CHAR_APP_ACCEPT_MSG
        )
        # when
        result = self.modeladmin._structures(obj)
        # then
        self.assertIsNone(result)

    # FIXME: Does not seam to work with special prefetch list
    # def test_webhooks(self):
    #     self.owner.webhooks.add(Webhook.objects.get(name="Test Webhook 2"))
    #     self.assertEqual(
    #         self.modeladmin._webhooks(self.obj), "Test Webhook 1, Test Webhook 2"
    #     )

    @patch(MODULE_PATH + ".NotificationAdmin.message_user", spec=True)
    def test_action_mark_as_sent(self, mock_message_user):
        # given
        notif = NotificationFactory(owner=self.owner, is_sent=False)
        queryset = Notification.objects.all()
        # when
        self.modeladmin.mark_as_sent(MockRequest(self.user), queryset)
        # then
        notif.refresh_from_db()
        self.assertTrue(notif.is_sent)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".NotificationAdmin.message_user", spec=True)
    def test_action_mark_as_unsent(self, mock_message_user):
        # given
        notif = NotificationFactory(owner=self.owner, is_sent=True)
        queryset = Notification.objects.all()
        # when
        self.modeladmin.mark_as_unsent(MockRequest(self.user), queryset)
        # then
        notif.refresh_from_db()
        self.assertFalse(notif.is_sent)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".NotificationAdmin.message_user", spec=True)
    @patch(MODULE_PATH + ".tasks.send_queued_messages_for_webhooks")
    def test_action_send_to_webhook(self, mock_task, mock_message_user):
        # given
        NotificationFactory(
            owner=self.owner, notif_type=NotificationType.STRUCTURE_LOST_SHIELD
        )
        queryset = Notification.objects.all()
        # when
        with patch(MODULE_PATH + ".Notification.send_to_webhook", return_value=True):
            self.modeladmin.send_to_configured_webhooks(
                MockRequest(self.user), queryset
            )
        # then
        self.assertEqual(mock_task.call_count, 1)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".NotificationAdmin.message_user", spec=True)
    @patch(MODULE_PATH + ".Notification.add_or_remove_timer")
    def test_action_process_for_timerboard(
        self, mock_process_for_timerboard, mock_message_user
    ):
        # given
        NotificationFactory(
            owner=self.owner, notif_type=NotificationType.STRUCTURE_LOST_SHIELD
        )
        queryset = Notification.objects.all()
        # when
        self.modeladmin.add_or_remove_timer(MockRequest(self.user), queryset)
        # then
        self.assertEqual(mock_process_for_timerboard.call_count, 1)
        self.assertTrue(mock_message_user.called)

    def test_filter_renderable_notifications(self):
        class NotificationAdminTest(admin.ModelAdmin):
            list_filter = (RenderableNotificationFilter,)

        # create test data
        positive_notif = NotificationFactory(
            owner=self.owner,
            notif_type=NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE,
        )
        NotificationFactory(owner=self.owner, notif_type="unknown")
        modeladmin = NotificationAdminTest(Notification, AdminSite())

        # Make sure the lookups are correct
        request = self.factory.get("/")
        request.user = self.user
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [("yes", "yes"), ("no", "no")]
        self.assertEqual(filterspec.lookup_choices, expected)

        # Make sure the correct queryset is returned
        request = self.factory.get("/", {"notification_renderable": "yes"})
        request.user = self.user
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        expected = Notification.objects.filter(pk=positive_notif.pk)
        self.assertSetEqual(set(queryset), set(expected))


class TestNotificationAdminWebhooks(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.modeladmin = NotificationAdmin(model=Notification, admin_site=AdminSite())
        cls.user = SuperuserFactory()

    def test_should_return_name_of_owner_webhook(self):
        # given
        owner = OwnerFactory(webhooks__name="Alpha")
        obj = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_LOST_SHIELD
        )
        obj2 = self.modeladmin.get_queryset(MockRequest(user=self.user)).get(pk=obj.pk)
        # when
        result = self.modeladmin._webhooks(obj2)
        # then
        self.assertEqual("Alpha", result)

    def test_should_report_missing_webhook(self):
        # given
        owner = OwnerFactory(webhooks=False)
        obj = NotificationFactory(
            owner=owner, notif_type=NotificationType.STRUCTURE_LOST_SHIELD
        )
        obj2 = self.modeladmin.get_queryset(MockRequest(user=self.user)).get(pk=obj.pk)
        # when
        result = self.modeladmin._webhooks(obj2)
        # then
        self.assertIn("Not configured", result)

    def test_should_report_when_webhooks_not_configured_for_this_notif_type(self):
        # given
        owner = OwnerFactory()
        obj = NotificationFactory(
            owner=owner, notif_type=NotificationType.SOV_ENTOSIS_CAPTURE_STARTED
        )
        obj2 = self.modeladmin.get_queryset(MockRequest(user=self.user)).get(pk=obj.pk)
        # when
        result = self.modeladmin._webhooks(obj2)
        # then
        self.assertIn("Not configured", result)


class TestOwnerAdmin(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.modeladmin = OwnerAdmin(model=Owner, admin_site=AdminSite())
        load_eveuniverse()
        cls.user = SuperuserFactory()
        cls.alliance = EveAllianceInfoFactory(
            alliance_id=3001, alliance_name="Wayne Enterprises"
        )
        cls.corporation = EveCorporationInfoFactory(
            corporation_id=2001,
            corporation_name="Wayne Technologies",
            alliance=cls.alliance,
        )

    def test_corporation(self):
        obj = OwnerFactory(corporation=self.corporation)
        self.assertEqual(self.modeladmin._corporation(obj), "Wayne Technologies")

    def test_alliance_normal(self):
        obj = OwnerFactory(corporation=self.corporation)
        self.assertEqual(self.modeladmin._alliance(obj), "Wayne Enterprises")

    def test_alliance_none(self):
        corporation = EveCorporationInfoFactory(create_alliance=False)
        obj = OwnerFactory(corporation=corporation)
        self.assertIsNone(self.modeladmin._alliance(obj))

    def test_webhooks(self):
        # given
        webhook_1 = WebhookFactory(name="Test Webhook 1")
        webhook_2 = WebhookFactory(name="Test Webhook 2")
        obj = OwnerFactory(webhooks=[webhook_1, webhook_2])
        # when/then
        self.assertEqual(
            self.modeladmin._webhooks(obj), "Test Webhook 1<br>Test Webhook 2"
        )

    @patch(MODULE_PATH + ".OwnerAdmin.message_user", spec=True)
    @patch(MODULE_PATH + ".tasks.update_structures_for_owner")
    def test_action_update_structures(self, mock_task, mock_message_user):
        # given
        OwnerFactory()
        queryset = Owner.objects.all()
        # when
        self.modeladmin.update_structures(MockRequest(self.user), queryset)
        # then
        self.assertEqual(mock_task.delay.call_count, 1)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".OwnerAdmin.message_user", spec=True)
    @patch(MODULE_PATH + ".tasks.process_notifications_for_owner")
    def test_action_fetch_notifications(self, mock_task, mock_message_user):
        # given
        OwnerFactory()
        queryset = Owner.objects.all()
        # when
        self.modeladmin.fetch_notifications(MockRequest(self.user), queryset)
        # then
        self.assertEqual(mock_task.delay.call_count, 1)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".OwnerAdmin.message_user", spec=True)
    def test_action_reset_characters(self, mock_message_user):
        # given
        owner_1 = OwnerFactory(characters=False)
        character_1 = OwnerCharacterFactory(owner=owner_1, is_enabled=False)
        owner_2 = OwnerFactory(characters=False)
        character_2 = OwnerCharacterFactory(owner=owner_2, is_enabled=False)
        # when
        queryset = Owner.objects.filter(pk=owner_1.pk)
        self.modeladmin.reset_characters(MockRequest(self.user), queryset)
        # then
        self.assertTrue(mock_message_user.called)
        character_1.refresh_from_db()
        self.assertTrue(character_1.is_enabled)
        character_2.refresh_from_db()
        self.assertFalse(character_2.is_enabled)

    def test_should_return_empty_turnaround_times(self):
        # given
        obj = OwnerFactory()
        # when
        result = self.modeladmin._avg_turnaround_time(obj)
        # then
        self.assertEqual(result, "- | - | -")

    @patch(MODULE_PATH + ".app_settings.STRUCTURES_NOTIFICATION_TURNAROUND_SHORT", 5)
    @patch(MODULE_PATH + ".app_settings.STRUCTURES_NOTIFICATION_TURNAROUND_MEDIUM", 15)
    @patch(MODULE_PATH + ".app_settings.STRUCTURES_NOTIFICATION_TURNAROUND_LONG", 50)
    @patch(
        MODULE_PATH + ".app_settings.STRUCTURES_NOTIFICATION_TURNAROUND_MAX_VALID", 3600
    )
    def test_should_return_correct_turnaround_times(self):
        # given
        my_owner = OwnerFactory()
        my_now = now()
        NotificationFactory(
            owner=my_owner,
            timestamp=my_now,
            created=my_now + dt.timedelta(seconds=3601),
        )
        for i in range(50):
            timestamp = my_now + dt.timedelta(minutes=i)
            NotificationFactory(
                owner=my_owner,
                timestamp=timestamp,
                created=timestamp + dt.timedelta(seconds=2),
            )
        # when
        result = self.modeladmin._avg_turnaround_time(my_owner)
        # then
        self.assertEqual(result, "2 | 2 | 2")


class TestStructureAdmin(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.modeladmin = StructureAdmin(model=Structure, admin_site=AdminSite())
        cls.user = SuperuserFactory()
        cls.alliance = EveAllianceInfoFactory(
            alliance_id=3001, alliance_name="Wayne Enterprises"
        )
        corporation = EveCorporationInfoFactory(
            corporation_id=2001,
            corporation_name="Wayne Technologies",
            alliance=cls.alliance,
        )
        cls.owner = OwnerFactory(corporation=corporation)

    def test_owner(self):
        # given
        obj = StructureFactory(owner=self.owner)
        # when/then
        self.assertEqual(
            self.modeladmin._owner(obj),
            "Wayne Technologies<br>Wayne Enterprises",
        )

    def test_location_structure(self):
        # given
        obj = StructureFactory(
            owner=self.owner, eve_solar_system_name="Amamake", eve_type_name="Astrahus"
        )
        # when/then
        self.assertEqual(self.modeladmin._location(obj), "Amamake<br>Heimatar")

    def test_location_poco(self):
        # given
        obj = PocoFactory(owner=self.owner, eve_planet_name="Amamake V")
        # when/then
        self.assertEqual(self.modeladmin._location(obj), "Amamake V<br>Heimatar")

    def test_location_starbase(self):
        # given
        obj = StarbaseFactory(owner=self.owner, eve_moon_name="Amamake II - Moon 1")
        self.assertEqual(
            self.modeladmin._location(obj), "Amamake II - Moon 1<br>Heimatar"
        )

    def test_type(self):
        # given
        obj = StructureFactory(owner=self.owner, eve_type_name="Astrahus")
        # when/then
        self.assertEqual(self.modeladmin._type(obj), "Astrahus<br>Citadel")

    def test_tags_1(self):
        # given
        obj = StructureFactory(
            owner=self.owner,
            eve_solar_system_name="Amamake",
            tags=[StructureTagFactory(name="my_tag")],
        )
        # when/then
        self.assertSetEqual(set(self.modeladmin._tags(obj)), {"lowsec", "my_tag"})

    def test_tags_2(self):
        # given
        obj = StructureFactory(owner=self.owner)
        obj.tags.clear()
        # when/then
        self.assertListEqual(self.modeladmin._tags(obj), [])

    @patch(MODULE_PATH + ".StructureAdmin.message_user", spec=True)
    def test_action_add_default_tags(self, mock_message_user):
        # given
        obj = StructureFactory()
        obj.tags.clear()
        queryset = Structure.objects.all()
        # when
        self.modeladmin.add_default_tags(MockRequest(self.user), queryset)
        default_tags = StructureTag.objects.filter(is_default=True)
        for obj in queryset:
            self.assertSetEqual(set(obj.tags.all()), set(default_tags))
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".StructureAdmin.message_user", spec=True)
    def test_action_remove_user_tags(self, mock_message_user):
        # given
        obj = StructureFactory(tags=[StructureTagFactory(name="my_tag")])
        queryset = Structure.objects.all()
        # when
        self.modeladmin.remove_user_tags(MockRequest(self.user), queryset)
        for obj in queryset:
            self.assertFalse(obj.tags.filter(is_user_managed=True).exists())
        self.assertTrue(mock_message_user.called)

    def test_owner_corporations_status_filter(self):
        class StructureAdminTest(admin.ModelAdmin):
            list_filter = (OwnerCorporationsFilter,)

        OwnerFactory(
            corporation=EveCorporationInfoFactory(
                corporation_id=2002, corporation_name="Wayne Foods"
            )
        )
        my_modeladmin = StructureAdminTest(Structure, AdminSite())

        # Make sure the lookups are correct
        request = self.factory.get("/")
        request.user = self.user
        changelist = my_modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [(2002, "Wayne Foods"), (2001, "Wayne Technologies")]
        self.assertEqual(filterspec.lookup_choices, expected)

        # Make sure the correct queryset is returned
        request = self.factory.get("/", {"owner_corporation_id__exact": 2001})
        request.user = self.user
        changelist = my_modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        expected = Structure.objects.filter(owner=self.owner)
        self.assertSetEqual(set(queryset), set(expected))

    def test_owner_alliance_status_filter(self):
        class StructureAdminTest(admin.ModelAdmin):
            list_filter = (OwnerAllianceFilter,)

        # create test data
        owner_2002 = OwnerFactory(
            corporation=EveCorporationInfoFactory(
                corporation_id=2002, alliance=self.alliance
            )
        )
        OwnerFactory(
            corporation=EveCorporationInfoFactory(
                corporation_id=2102, create_alliance=False
            )
        )
        modeladmin = StructureAdminTest(Structure, AdminSite())

        # Make sure the lookups are correct
        request = self.factory.get("/")
        request.user = self.user
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [(3001, "Wayne Enterprises")]
        self.assertEqual(filterspec.lookup_choices, expected)

        # Make sure the correct queryset is returned
        request = self.factory.get("/", {"owner_alliance_id__exact": 3001})
        request.user = self.user
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        expected = Structure.objects.filter(owner__in=[self.owner, owner_2002])
        self.assertSetEqual(set(queryset), set(expected))


class TestWebhookAdmin(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modeladmin = WebhookAdmin(model=Webhook, admin_site=AdminSite())
        cls.user = SuperuserFactory()

    @patch(MODULE_PATH + ".WebhookAdmin.message_user", spec=True)
    @patch(MODULE_PATH + ".tasks.send_test_notifications_to_webhook")
    def test_action_test_notification(self, mock_task, mock_message_user):
        # given
        WebhookFactory()
        queryset = Webhook.objects.all()
        # when
        self.modeladmin.test_notification(MockRequest(self.user), queryset)
        # then
        self.assertEqual(mock_task.delay.call_count, 1)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".WebhookAdmin.message_user", spec=True)
    def test_action_activate(self, mock_message_user):
        # given
        webhook = WebhookFactory(is_active=False)
        queryset = Webhook.objects.all()
        # when
        self.modeladmin.activate(MockRequest(self.user), queryset)
        # then
        webhook.refresh_from_db()
        self.assertTrue(webhook.is_active)
        self.assertTrue(mock_message_user.called)

    @patch(MODULE_PATH + ".WebhookAdmin.message_user", spec=True)
    def test_action_deactivate(self, mock_message_user):
        # given
        webhook = WebhookFactory(is_active=True)
        queryset = Webhook.objects.all()
        # when
        self.modeladmin.deactivate(MockRequest(self.user), queryset)
        # then
        webhook.refresh_from_db()
        self.assertFalse(webhook.is_active)
        self.assertTrue(mock_message_user.called)

    def test_can_assign_owner(self):
        # given
        owner = OwnerFactory()
        webhook = WebhookFactory()
        self.client.force_login(self.user)
        data = {
            "name": webhook.name,
            "notification_types": NotificationType.webhook_defaults(),
            "owners": [owner.pk],
            "url": webhook.url,
            "webhook_type": webhook.webhook_type,
        }
        r = self.client.post(
            f"/admin/structures/webhook/{webhook.pk}/change/", data=data
        )
        self.assertEqual(r.status_code, 302)
        webhook.refresh_from_db()
        self.assertIn(owner, webhook.owners.all())
