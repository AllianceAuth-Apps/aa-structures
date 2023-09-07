"""API for Structures."""


from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.authentication.models import CharacterOwnership

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

    return owner
