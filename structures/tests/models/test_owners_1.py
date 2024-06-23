import datetime as dt
from datetime import datetime, timedelta
from unittest.mock import patch

from django.utils.timezone import now, utc
from esi.errors import TokenError
from esi.models import Token
from eveuniverse.models import EveSolarSystem

from app_utils.testing import NoSocketsTestCase

from structures.models import Owner, OwnerCharacter
from structures.tests.testdata.factories import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveSovereigntyMapFactory,
    OwnerCharacterFactory,
    OwnerFactory,
    UserMainBasicFactory,
    UserMainDefaultOwnerFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "structures.models.owners"


class TestOwner(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alliance = EveAllianceInfoFactory(
            alliance_name="Wayne Enterprises", alliance_ticker="WYE"
        )
        corporation = EveCorporationInfoFactory(
            corporation_name="Wayne Technologies", alliance=cls.alliance
        )
        character = EveCharacterFactory(corporation=corporation)
        cls.user = UserMainDefaultOwnerFactory(main_character__character=character)
        cls.owner = OwnerFactory(user=cls.user)

    def test_str(self):
        # when
        result = str(self.owner)
        # then
        self.assertEqual(result, "Wayne Technologies")

    def test_repr(self):
        # when
        result = repr(self.owner)
        # then
        self.assertEqual(
            result, f"Owner(pk={self.owner.pk}, corporation='Wayne Technologies')"
        )

    @patch(MODULE_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    def test_is_structure_sync_fresh(self):
        # no errors and recent sync
        self.owner.structures_last_update_at = now()
        self.assertTrue(self.owner.is_structure_sync_fresh)

        # no errors and sync within grace period
        self.owner.structures_last_update_at = now() - timedelta(minutes=29)
        self.assertTrue(self.owner.is_structure_sync_fresh)

        # no error, but no sync within grace period
        self.owner.structures_last_update_at = now() - timedelta(minutes=31)
        self.assertFalse(self.owner.is_structure_sync_fresh)

    @patch(MODULE_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_is_notification_sync_fresh(self):
        # no errors and recent sync
        self.owner.notifications_last_update_at = now()
        self.assertTrue(self.owner.is_notification_sync_fresh)

        # no errors and sync within grace period
        self.owner.notifications_last_update_at = now() - timedelta(minutes=29)
        self.assertTrue(self.owner.is_notification_sync_fresh)

        # no error, but no sync within grace period
        self.owner.notifications_last_update_at = now() - timedelta(minutes=31)
        self.assertFalse(self.owner.is_notification_sync_fresh)

    @patch(MODULE_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_is_forwarding_sync_fresh(self):
        # no errors and recent sync
        self.owner.forwarding_last_update_at = now()
        self.assertTrue(self.owner.is_forwarding_sync_fresh)

        # no errors and sync within grace period
        self.owner.forwarding_last_update_at = now() - timedelta(minutes=29)
        self.assertTrue(self.owner.is_forwarding_sync_fresh)

        # no error, but no sync within grace period
        self.owner.forwarding_last_update_at = now() - timedelta(minutes=31)
        self.assertFalse(self.owner.is_forwarding_sync_fresh)

    @patch(MODULE_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    def test_is_assets_sync_fresh(self):
        # no errors and recent sync
        self.owner.assets_last_update_at = now()
        self.assertTrue(self.owner.is_assets_sync_fresh)

        # no errors and sync within grace period
        self.owner.assets_last_update_at = now() - timedelta(minutes=29)
        self.assertTrue(self.owner.is_assets_sync_fresh)

        # no error, but no sync within grace period
        self.owner.assets_last_update_at = now() - timedelta(minutes=31)
        self.assertFalse(self.owner.is_assets_sync_fresh)

    @patch(MODULE_PATH + ".STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 30)
    @patch(MODULE_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    @patch(MODULE_PATH + ".STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 30)
    def test_is_all_syncs_ok(self):
        self.owner.structures_last_update_at = now()
        self.owner.notifications_last_update_at = now()
        self.owner.forwarding_last_update_at = now()
        self.owner.assets_last_update_at = now()
        self.assertTrue(self.owner.are_all_syncs_ok)

    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
    def test_get_esi_scopes_pocos_off(self):
        self.assertSetEqual(
            set(Owner.get_esi_scopes()),
            {
                "esi-corporations.read_structures.v1",
                "esi-universe.read_structures.v1",
                "esi-characters.read_notifications.v1",
                "esi-assets.read_corporation_assets.v1",
            },
        )

    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", True)
    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", False)
    def test_get_esi_scopes_pocos_on(self):
        self.assertSetEqual(
            set(Owner.get_esi_scopes()),
            {
                "esi-corporations.read_structures.v1",
                "esi-universe.read_structures.v1",
                "esi-characters.read_notifications.v1",
                "esi-planets.read_customs_offices.v1",
                "esi-assets.read_corporation_assets.v1",
            },
        )

    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", False)
    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
    def test_get_esi_scopes_starbases_on(self):
        self.assertSetEqual(
            set(Owner.get_esi_scopes()),
            {
                "esi-corporations.read_structures.v1",
                "esi-universe.read_structures.v1",
                "esi-characters.read_notifications.v1",
                "esi-corporations.read_starbases.v1",
                "esi-assets.read_corporation_assets.v1",
            },
        )

    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_CUSTOMS_OFFICES", True)
    @patch(MODULE_PATH + ".STRUCTURES_FEATURE_STARBASES", True)
    def test_get_esi_scopes_starbases_and_custom_offices(self):
        self.assertSetEqual(
            set(Owner.get_esi_scopes()),
            {
                "esi-corporations.read_structures.v1",
                "esi-universe.read_structures.v1",
                "esi-characters.read_notifications.v1",
                "esi-corporations.read_starbases.v1",
                "esi-planets.read_customs_offices.v1",
                "esi-assets.read_corporation_assets.v1",
            },
        )

    def test_should_ensure_only_one_owner_in_same_alliance_is_main(self):
        # given
        self.owner.is_alliance_main = True
        self.owner.save()
        corporation = EveCorporationInfoFactory(alliance=self.alliance)
        owner = OwnerFactory(corporation=corporation)
        # when
        owner.is_alliance_main = True
        owner.save()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_alliance_main)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_alliance_main)

    def test_should_ensure_is_alliance_main_is_set_for_update_fields_1(self):
        # given
        corporation = EveCorporationInfoFactory(alliance=self.alliance)
        owner = OwnerFactory(corporation=corporation, is_alliance_main=True)
        # when
        owner.save(update_fields={"is_active"})
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_alliance_main)

    def test_should_ensure_is_alliance_main_is_set_for_update_fields_2(self):
        # given
        corporation = EveCorporationInfoFactory(alliance=self.alliance)
        owner = OwnerFactory(corporation=corporation, is_alliance_main=True)
        # when
        owner.save(update_fields=["is_active"])
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_alliance_main)

    def test_should_allow_mains_from_other_alliances(self):
        # given
        self.owner.is_alliance_main = True
        self.owner.save()
        owner = OwnerFactory()
        # when
        owner.is_alliance_main = True
        owner.save()
        # then
        owner.refresh_from_db()
        self.assertTrue(owner.is_alliance_main)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_alliance_main)

    def test_should_allow_other_corporations_to_be_main(self):
        # given
        self.owner.is_alliance_main = True
        self.owner.save()
        owner_2 = OwnerFactory(is_alliance_main=True)
        owner_3 = OwnerFactory()
        # when
        owner_3.is_alliance_main = True
        owner_3.save()
        # then
        owner_3.refresh_from_db()
        self.assertTrue(owner_3.is_alliance_main)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_alliance_main)
        owner_2.refresh_from_db()
        self.assertTrue(owner_2.is_alliance_main)


class TestOwnerHasSov(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        EveSovereigntyMapFactory(
            corporation=cls.owner.corporation, eve_solar_system_name="1-PGSG"
        )

    def test_should_return_true_when_owner_has_sov(self):
        # given
        system = EveSolarSystem.objects.get(name="1-PGSG")
        # when/then
        self.assertTrue(self.owner.has_sov(system))

    def test_should_return_false_when_owner_has_no_sov(self):
        # given
        system = EveSolarSystem.objects.get(name="A-C5TC")
        # when/then
        self.assertFalse(self.owner.has_sov(system))

    def test_should_return_false_when_owner_is_outside_nullsec(self):
        # given
        system = EveSolarSystem.objects.get(name="Amamake")
        # when/then
        self.assertFalse(self.owner.has_sov(system))


@patch(MODULE_PATH + ".notify")
@patch(MODULE_PATH + ".notify_admins")
class TestOwnerFetchToken(NoSocketsTestCase):
    def test_should_return_correct_token(self, mock_notify_admins, mock_notify):
        # given
        character = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        owner = OwnerFactory(user=user, characters=[character])
        # when
        token = owner.fetch_token()
        # then
        self.assertIsInstance(token, Token)
        self.assertEqual(token.user, user)
        self.assertEqual(token.character_id, character.character_id)
        self.assertSetEqual(
            set(Owner.get_esi_scopes()),
            set(token.scopes.values_list("name", flat=True)),
        )
        self.assertFalse(mock_notify_admins.called)
        self.assertFalse(mock_notify.called)
        self.assertEqual(owner.characters.count(), 1)

    def test_raise_error_when_no_sync_char_defined(
        self, mock_notify_admins, mock_notify
    ):
        # given
        owner = OwnerFactory(characters=False)
        # when/then
        with self.assertRaises(TokenError):
            owner.fetch_token()
        self.assertFalse(mock_notify_admins.called)
        self.assertFalse(mock_notify.called)

    def test_raise_error_when_user_has_no_permission_and_delete_character(
        self, mock_notify_admins, mock_notify
    ):
        # given
        character = EveCharacterFactory()
        user = UserMainBasicFactory(main_character__character=character)
        owner = OwnerFactory(user=user, characters=[character])
        # when/then
        with self.assertRaises(TokenError):
            owner.fetch_token()
        self.assertTrue(mock_notify_admins.called)
        self.assertTrue(mock_notify.called)
        self.assertEqual(owner.characters.count(), 0)

    def test_raise_error_when_no_valid_token_found_and_disable_character(
        self, mock_notify_admins, mock_notify
    ):
        # given
        eve_character = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=eve_character)
        owner = OwnerFactory(user=user, characters=[eve_character])
        user.token_set.first().scopes.clear()  # token no longer valid
        # when/then
        with self.assertRaises(TokenError):
            owner.fetch_token()
        character = owner.characters.first()
        self.assertFalse(character.is_enabled)
        self.assertTrue(mock_notify_admins.called)
        self.assertTrue(mock_notify.called)

    def test_raise_error_when_character_no_longer_a_corporation_member_and_delete_it(
        self, mock_notify_admins, mock_notify
    ):
        # given
        character = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        owner = OwnerFactory(user=user, characters=[character])
        new_corporation = EveCorporationInfoFactory()
        character.corporation_id = new_corporation.corporation_id
        character.corporation_name = new_corporation.corporation_name
        character.save()
        # when/then
        with self.assertRaises(TokenError):
            owner.fetch_token()
        self.assertTrue(mock_notify_admins.called)
        self.assertTrue(mock_notify.called)
        self.assertEqual(owner.characters.count(), 0)

    def test_should_rotate_through_enabled_characters_for_notification(
        self, mock_notify_admins, mock_notify
    ):
        # given
        owner = OwnerFactory(characters=False)
        character_1 = OwnerCharacterFactory(
            owner=owner,
            notifications_last_used_at=dt.datetime(2021, 1, 1, 1, 0, tzinfo=utc),
        )
        character_2 = OwnerCharacterFactory(
            owner=owner,
            notifications_last_used_at=dt.datetime(2021, 1, 1, 2, 0, tzinfo=utc),
        )
        character_3 = OwnerCharacterFactory(
            owner=owner,
            notifications_last_used_at=dt.datetime(2021, 1, 1, 3, 0, tzinfo=utc),
        )
        OwnerCharacterFactory(
            owner=owner, is_enabled=False
        )  # this one should be ignore
        tokens_received = []

        # when
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.NOTIFICATIONS,
                ignore_schedule=True,
            ).character_id
        )
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.NOTIFICATIONS,
                ignore_schedule=True,
            ).character_id
        )
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.NOTIFICATIONS,
                ignore_schedule=True,
            ).character_id
        )
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.NOTIFICATIONS,
                ignore_schedule=True,
            ).character_id
        )

        # then
        self.assertListEqual(
            tokens_received,
            [
                character_1.character_id(),
                character_2.character_id(),
                character_3.character_id(),
                character_1.character_id(),
            ],
        )

    def test_should_rotate_through_characters_for_structures(
        self, mock_notify_admins, mock_notify
    ):
        # given
        owner = OwnerFactory(characters=False)
        character_1 = OwnerCharacterFactory(
            owner=owner,
            structures_last_used_at=dt.datetime(2021, 1, 1, 3, 0, tzinfo=utc),
        )
        character_2 = OwnerCharacterFactory(
            owner=owner,
            structures_last_used_at=dt.datetime(2021, 1, 1, 1, 0, tzinfo=utc),
        )
        character_3 = OwnerCharacterFactory(
            owner=owner,
            structures_last_used_at=dt.datetime(2021, 1, 1, 2, 0, tzinfo=utc),
        )
        tokens_received = []

        # when
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.STRUCTURES,
                ignore_schedule=True,
            ).character_id
        )
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.STRUCTURES,
                ignore_schedule=True,
            ).character_id
        )
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.STRUCTURES,
                ignore_schedule=True,
            ).character_id
        )
        tokens_received.append(
            owner.fetch_token(
                rotate_characters=Owner.RotateCharactersType.STRUCTURES,
                ignore_schedule=True,
            ).character_id
        )

        # then
        self.assertListEqual(
            tokens_received,
            [
                character_2.character_id(),
                character_3.character_id(),
                character_1.character_id(),
                character_2.character_id(),
            ],
        )

    def test_should_delete_invalid_characters_and_return_token_from_valid_char(
        self, mock_notify_admins, mock_notify
    ):
        # given
        character_1 = EveCharacterFactory()
        user = UserMainDefaultOwnerFactory(main_character__character=character_1)
        owner = OwnerFactory(
            user=user,
            characters=[character_1],
            characters__notifications_last_used_at=dt.datetime(
                2021, 1, 1, 1, 2, tzinfo=utc
            ),
        )
        character_2 = EveCharacterFactory()  # invalid, because of different corporation
        OwnerCharacterFactory(
            owner=owner,
            eve_character=character_2,
            notifications_last_used_at=dt.datetime(2021, 1, 1, 1, 1, tzinfo=utc),
        )

        # when
        token = owner.fetch_token()

        # then
        self.assertIsInstance(token, Token)
        self.assertEqual(token.user, user)
        self.assertTrue(mock_notify_admins.called)
        self.assertTrue(mock_notify.called)
        self.assertEqual(owner.characters.count(), 1)


class TestOwnerCharacters(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory()

    def test_should_add_new_character(self):
        # given
        character = EveCharacterFactory(corporation=self.owner.corporation)
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        character_ownership = user.profile.main_character.character_ownership
        # when
        result = self.owner.add_character(character_ownership)
        # then
        self.assertIsInstance(result, OwnerCharacter)
        self.assertEqual(result.owner, self.owner)
        self.assertEqual(result.character_ownership, character_ownership)
        self.assertIsNone(result.notifications_last_used_at)
        character_ownership_pks = self.owner.characters.values_list(
            "character_ownership", flat=True
        )
        self.assertIn(character_ownership.pk, character_ownership_pks)
        self.assertEqual(character_ownership_pks.count(), 2)

    def test_should_not_overwrite_existing_characters(self):
        # given
        character = self.owner.characters.first()
        my_dt = datetime(year=2021, month=2, day=11, hour=12, tzinfo=utc)
        character.notifications_last_used_at = my_dt
        character.save()
        # when
        result = self.owner.add_character(character.character_ownership)
        # then
        self.assertIsInstance(result, OwnerCharacter)
        self.assertEqual(result.owner, self.owner)
        self.assertEqual(result.character_ownership, character.character_ownership)
        self.assertEqual(result.notifications_last_used_at, my_dt)

    def test_should_prevent_adding_character_from_other_corporation(self):
        # given
        user = UserMainDefaultOwnerFactory()
        character_ownership = user.profile.main_character.character_ownership
        # when
        with self.assertRaises(ValueError):
            self.owner.add_character(character_ownership)

    def test_should_count_enabled_characters_only(self):
        # given
        OwnerCharacterFactory(owner=self.owner, is_enabled=False)
        # when
        result = self.owner.valid_characters_count()
        # then
        self.assertEqual(result, 1)

    def test_should_count_characters_when_empty(self):
        # given
        owner = OwnerFactory(characters=False)
        # when
        result = owner.valid_characters_count()
        # then
        self.assertEqual(result, 0)

    def test_should_reset_character_when_re_adding(self):
        # given
        character: OwnerCharacter = self.owner.characters.first()
        character.is_enabled = False
        character.disabled_reason = "some reason"
        character.save()
        # when
        self.owner.add_character(character.character_ownership)
        # then
        character.refresh_from_db()
        self.assertTrue(character.is_enabled)
        self.assertFalse(character.disabled_reason)


@patch(MODULE_PATH + ".notify", spec=True)
@patch(MODULE_PATH + ".notify_admins", spec=True)
class TestOwnerDeleteCharacter(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory(characters=False)

    def test_should_delete_character_and_notify(self, mock_notify_admins, mock_notify):
        # given
        character = OwnerCharacterFactory(owner=self.owner)
        user = character.character_ownership.user

        # when
        self.owner.delete_character(character=character, reason="dummy error")

        # then
        self.assertEqual(self.owner.characters.count(), 0)
        self.assertTrue(mock_notify_admins.called)
        _, kwargs = mock_notify_admins.call_args
        self.assertIn("dummy error", kwargs["message"])
        self.assertEqual(kwargs["level"], "danger")
        self.assertTrue(mock_notify.called)
        _, kwargs = mock_notify.call_args
        self.assertIn("dummy error", kwargs["message"])
        self.assertEqual(kwargs["user"], user)
        self.assertEqual(kwargs["level"], "warning")


@patch(MODULE_PATH + ".notify", spec=True)
@patch(MODULE_PATH + ".notify_admins", spec=True)
class TestOwnerDisableCharacters(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory(characters=False)

    def test_should_disable_character_and_notify(self, mock_notify_admins, mock_notify):
        # given
        character = OwnerCharacterFactory(owner=self.owner)
        user = character.character_ownership.user

        # when
        self.owner.disable_character(character=character, reason="dummy error")

        # then
        character.refresh_from_db()
        self.assertFalse(character.is_enabled)
        self.assertTrue(character.disabled_reason)
        self.assertTrue(mock_notify_admins.called)
        _, kwargs = mock_notify_admins.call_args
        self.assertIn("dummy error", kwargs["message"])
        self.assertEqual(kwargs["level"], "danger")
        self.assertTrue(mock_notify.called)
        _, kwargs = mock_notify.call_args
        self.assertIn("dummy error", kwargs["message"])
        self.assertEqual(kwargs["user"], user)
        self.assertEqual(kwargs["level"], "warning")

    def test_should_not_disable_when_error_counter_above_zero(
        self, mock_notify_admins, mock_notify
    ):
        # given
        character = OwnerCharacterFactory(owner=self.owner)

        # when
        self.owner.disable_character(
            character=character, reason="dummy error", max_allowed_errors=1
        )
        # then
        character.refresh_from_db()
        self.assertTrue(character.is_enabled)
        self.assertEqual(character.error_count, 1)
        self.assertFalse(mock_notify_admins.called)
        self.assertFalse(mock_notify.called)
