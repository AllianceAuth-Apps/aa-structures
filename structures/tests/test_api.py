from unittest.mock import patch

from django.test import TestCase

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from app_utils.testing import create_user_from_evecharacter

from structures.api import add_character
from structures.models import Owner, Webhook

from .testdata.helpers import load_entities
from .testdata.load_eveuniverse import load_eveuniverse

API_PATH = "structures.api"


class TestAddCharacter(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_eveuniverse()
        load_entities([EveCorporationInfo, EveAllianceInfo, EveCharacter, Webhook])
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=["structures.basic_access", "structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        cls.character = cls.character_ownership.character

    def _add_structure_owner(self, token=None, user=None):
        if user is None:
            user = self.user
        if token is None:
            token = user.token_set.first()

        return add_character(user, token)

    @patch(API_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", True)
    @patch(API_PATH + ".tasks.update_all_for_owner")
    @patch(API_PATH + ".notify_admins")
    def test_should_add_new_structure_owner_and_notify_admins(
        self, mock_notify_admins, mock_update_all_for_owner
    ):
        owner = self._add_structure_owner()
        self.assertTrue(mock_notify_admins.called)
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertEqual(owner.webhooks.first().name, "Test Webhook 1")
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(API_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(API_PATH + ".tasks.update_all_for_owner")
    def test_should_add_character_to_existing_structure_owner_and_reactive(
        self, mock_update_all_for_owner
    ):
        owner = Owner.objects.create(
            corporation=EveCorporationInfo.objects.get(corporation_id=2102),
            is_active=False,
        )
        _, character_ownership_1011 = create_user_from_evecharacter(
            1011,
            permissions=["structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        owner.add_character(character_ownership_1011)
        user_1102, character_ownership_1102 = create_user_from_evecharacter(
            1102,
            permissions=["structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )

        self._add_structure_owner(user=user_1102)

        self.assertFalse(mock_update_all_for_owner.delay.called)

        owner.refresh_from_db()
        self.assertSetEqual(
            {character_ownership_1011.pk, character_ownership_1102.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertTrue(owner.is_active)

    @patch(API_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(API_PATH + ".tasks.update_all_for_owner")
    @patch(API_PATH + ".notify_admins")
    def test_should_add_new_structure_owner_and_not_notify_admins(
        self, mock_notify_admins, mock_update_all_for_owner
    ):
        # when
        owner = self._add_structure_owner()
        # then
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertFalse(mock_notify_admins.called)
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(API_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(API_PATH + ".tasks.update_all_for_owner")
    @patch(API_PATH + ".notify_admins")
    def test_should_add_structure_owner_with_no_default_webhook(
        self, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        Webhook.objects.filter(name="Test Webhook 1").update(is_default=False)
        # when
        self._add_structure_owner()
        # then
        self.assertFalse(mock_notify_admins.called)
        my_owner = Owner.objects.get(
            characters__character_ownership=self.character_ownership
        )
        self.assertIsNone(my_owner.webhooks.first())
        self.assertTrue(mock_update_all_for_owner.delay.called)

    def test_should_report_error_when_token_does_not_belong_to_user(self):
        # given
        other_user, _ = create_user_from_evecharacter(
            1011,
            permissions=["structures.basic_access", "structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        # when
        my_token = other_user.token_set.first()
        # then
        self.assertRaises(
            CharacterOwnership.DoesNotExist, self._add_structure_owner, token=my_token
        )
