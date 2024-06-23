from app_utils.testing import NoSocketsTestCase

from structures.tests.testdata.factories import OwnerCharacterFactory, OwnerFactory

MODULE_PATH = "structures.models.owners"


class TestOwnerCharacter(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = OwnerFactory()

    def test_should_return_str(self):
        # given
        character = OwnerCharacterFactory(owner=self.owner)
        # when/then
        self.assertTrue(str(character))

    def test_can_reset_character(self):
        # given
        character = OwnerCharacterFactory(
            owner=self.owner, is_enabled=False, disabled_reason="reason", error_count=42
        )
        # when
        character.reset()
        # then
        character.refresh_from_db()
        self.assertTrue(character.is_enabled)
        self.assertFalse(character.disabled_reason)
        self.assertFalse(character.error_count)
