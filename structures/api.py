"""API for Structures."""


from django.utils import translation
from django.utils.translation import gettext as _

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from app_utils.allianceauth import notify_admins

from . import __title__
from .app_settings import (
    STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED,
    STRUCTURES_DEFAULT_LANGUAGE,
)
from .models import Owner, Webhook


def get_add_character_permissions():
    """Return permission required for adding a character."""
    return ["structures.add_structure_owner"]


def get_add_character_esi_scopes():
    """Return ESI scopes required for adding a character."""
    return Owner.get_esi_scopes()


def add_character(request, token) -> Owner:
    """Add the character in the token as a structure owner."""
    token_char = EveCharacter.objects.get(character_id=token.character_id)
    character_ownership = CharacterOwnership.objects.get(
        user=request.user, character=token_char
    )
    try:
        corporation = EveCorporationInfo.objects.get(
            corporation_id=token_char.corporation_id
        )
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(
            token_char.corporation_id
        )
    owner, created = Owner.objects.update_or_create(
        corporation=corporation, defaults={"is_active": True}
    )
    owner.add_character(character_ownership)
    if created:
        default_webhooks = Webhook.objects.filter(is_default=True)
        if default_webhooks:
            for webhook in default_webhooks:
                owner.webhooks.add(webhook)
            owner.save()

    if owner.characters.count() == 1 and STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED:
        with translation.override(STRUCTURES_DEFAULT_LANGUAGE):
            notify_admins(
                message=_(
                    "%(corporation)s was added as new structure owner by %(user)s."
                )
                % {"corporation": owner, "user": request.user.username},
                title=_("%s: Structure owner added: %s") % (__title__, owner),
            )
    elif STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED:
        with translation.override(STRUCTURES_DEFAULT_LANGUAGE):
            notify_admins(
                message=_(
                    "%(character)s was added as sync character to "
                    "%(corporation)s by %(user)s.\n"
                    "We now have %(characters_count)d sync character(s) configured."
                )
                % {
                    "character": token_char,
                    "corporation": owner,
                    "user": request.user.username,
                    "characters_count": owner.characters_count(),
                },
                title=_("%s: Character added to: %s") % (__title__, owner),
            )

    return owner
