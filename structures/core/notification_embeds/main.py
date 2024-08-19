"""Billing embeds."""

# pylint: disable=missing-class-docstring

import re
from typing import Optional

import dhooks_lite

from django.conf import settings
from django.utils.translation import gettext as _

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag
from app_utils.urls import reverse_absolute, static_file_absolute_url

from structures import __title__
from structures.core.notification_types import NotificationType
from structures.helpers import get_or_create_eve_entity, is_absolute_url
from structures.models.notifications import Notification, NotificationBase, Webhook

from .helpers import gen_alliance_link, gen_corporation_link, target_datetime_formatted

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class NotificationBaseEmbed:
    """Base class for all notification embeds.

    You must subclass this class to create an embed for a notification type.
    At least title and description must be defined in the subclass.
    """

    ICON_DEFAULT_SIZE = 64

    def __init__(self, notification: Notification) -> None:
        if not isinstance(notification, NotificationBase):
            raise TypeError("notification must be of type Notification")
        self._notification = notification
        self._data = notification.parsed_text()
        self._title = ""
        self._description = ""
        self._color = None
        self._thumbnail = None
        self._ping_type = None

    def __str__(self) -> str:
        return str(self.notification)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(notification={self.notification!r})"

    @property
    def notification(self) -> Notification:
        """Return notification object this embed is created from."""
        return self._notification

    @property
    def ping_type(self) -> Optional[Webhook.PingType]:
        """Return Ping Type of the related notification."""
        return self._ping_type

    def compile_damage_text(self, field_postfix: str, factor: int = 1) -> str:
        """Compile damage text for Structures and POSes"""
        damage_labels = [
            ("shield", _("shield")),
            ("armor", _("armor")),
            ("hull", _("hull")),
        ]
        damage_parts = []
        for prop in damage_labels:
            field_name = f"{prop[0]}{field_postfix}"
            if field_name in self._data:
                label = prop[1]
                value = self._data[field_name] * factor
                damage_parts.append(f"{label}: {value:.1f}%")
        damage_text = " | ".join(damage_parts)
        return damage_text

    def gen_aggressor_link(self) -> str:
        """Returns the aggressor link from a parsed_text for POS and POCOs only."""
        if key := self._data.get("aggressorAllianceID"):
            key = "aggressorAllianceID"
        elif self._data.get("aggressorCorpID"):
            key = "aggressorCorpID"
        elif self._data.get("aggressorID"):
            key = "aggressorID"
        else:
            return "(Unknown aggressor)"
        entity = get_or_create_eve_entity(id=self._data[key])
        return Webhook.create_link(entity.name, entity.profile_url)

    def gen_attacker_link(self) -> str:
        """Returns the attacker link from a parsed_text for Upwell structures only."""
        if name := self._data.get("allianceName"):
            return gen_alliance_link(name)

        if name := self._data.get("corpName"):
            return gen_corporation_link(name)

        return _("(unknown)")

    def fuel_expires_target_date(self) -> str:
        """Return calculated target date when fuel expires. Returns '?' when no data."""
        if self._structure and self._structure.fuel_expires_at:
            return target_datetime_formatted(self._structure.fuel_expires_at)
        return "?"

    def generate_embed(self) -> dhooks_lite.Embed:
        """Returns generated Discord embed for this object.

        Will use custom color for embeds if self.notification has the
        property "color_override" defined

        Will use custom ping type if self.notification has the
        property "ping_type_override" defined

        """
        corporation = self.notification.owner.corporation
        if self.notification.is_alliance_level and corporation.alliance:
            author_name = corporation.alliance.alliance_name
            author_url = corporation.alliance.logo_url(size=self.ICON_DEFAULT_SIZE)
        else:
            author_name = corporation.corporation_name
            author_url = corporation.logo_url(size=self.ICON_DEFAULT_SIZE)
        app_url = reverse_absolute("structures:index")
        app_url = app_url if is_absolute_url(app_url) else None
        author = dhooks_lite.Author(name=author_name, icon_url=author_url, url=app_url)
        if self.notification.color_override:
            self._color = self.notification.color_override
        if self.notification.ping_type_override:
            self._ping_type = self.notification.ping_type_override
        elif self._color == Webhook.Color.DANGER:
            self._ping_type = Webhook.PingType.EVERYONE
        elif self._color == Webhook.Color.WARNING:
            self._ping_type = Webhook.PingType.HERE
        else:
            self._ping_type = Webhook.PingType.NONE
        if self.notification.is_generated:
            footer_text = __title__
            footer_icon_url = static_file_absolute_url(
                "structures/img/structures_logo.png"
            )
        else:
            footer_text = "Eve Online"
            footer_icon_url = static_file_absolute_url(
                "structures/img/eve_symbol_128.png"
            )
        if settings.DEBUG:
            my_text = (
                self.notification.notification_id
                if not self.notification.is_generated
                else "GENERATED"
            )
            footer_text += f" #{my_text}"
        footer_icon_url = footer_icon_url if is_absolute_url(footer_icon_url) else None
        footer = dhooks_lite.Footer(text=footer_text, icon_url=footer_icon_url)
        max_description = dhooks_lite.Embed.MAX_DESCRIPTION
        if self._description and len(self._description) > max_description:
            logger.warning(
                "%s: Description of notification is too long: %s",
                self,
                self._description,
            )
            self._description = self._description[:max_description]
        max_title = dhooks_lite.Embed.MAX_TITLE
        if self._title and len(self._title) > max_title:
            logger.warning(
                "%s: Title of notification is too long: %s", self, self._title
            )
            self._title = self._title[:max_title]
        return dhooks_lite.Embed(
            author=author,
            color=self._color,
            description=self._description,
            footer=footer,
            timestamp=self.notification.timestamp,
            title=self._title,
            thumbnail=self._thumbnail,
        )

    # pylint: disable = too-many-locals
    @staticmethod
    def create(notif: "NotificationBase") -> "NotificationBaseEmbed":
        """Creates a new instance of the respective subclass for given Notification."""

        from .billing_embeds import (
            NotificationBillingBillOutOfMoneyMsg,
            NotificationBillingIHubBillAboutToExpire,
            NotificationBillingIHubDestroyedByBillFailure,
            NotificationCorpAllBillMsg,
        )
        from .corporate_embeds import (
            NotificationCharAppAcceptMsg,
            NotificationCharAppRejectMsg,
            NotificationCharAppWithdrawMsg,
            NotificationCharLeftCorpMsg,
            NotificationCorpAppInvitedMsg,
            NotificationCorpAppNewMsg,
            NotificationCorpAppRejectCustomMsg,
        )
        from .moonmining_embeds import (
            NotificationMoonminningAutomaticFracture,
            NotificationMoonminningExtractionCanceled,
            NotificationMoonminningExtractionFinished,
            NotificationMoonminningExtractionStarted,
            NotificationMoonminningLaserFired,
        )
        from .orbital_embeds import (
            NotificationOrbitalAttacked,
            NotificationOrbitalReinforced,
        )
        from .skyhook_embeds import (
            NotificationSkyhookDeployed,
            NotificationSkyhookDestroyed,
            NotificationSkyhookLostShield,
            NotificationSkyhookOnline,
            NotificationSkyhookUnderAttack,
        )
        from .sov_embeds import (
            NotificationSovAllAnchoringMsg,
            NotificationSovAllClaimAcquiredMsg,
            NotificationSovAllClaimLostMsg,
            NotificationSovCommandNodeEventStarted,
            NotificationSovEntosisCaptureStarted,
            NotificationSovStructureDestroyed,
            NotificationSovStructureReinforced,
        )
        from .structures_embeds import (
            NotificationStructureAnchoring,
            NotificationStructureDestroyed,
            NotificationStructureFuelAlert,
            NotificationStructureJumpFuelAlert,
            NotificationStructureLostArmor,
            NotificationStructureLostShield,
            NotificationStructureLowReagentsAlert,
            NotificationStructureNoReagentsAlert,
            NotificationStructureOnline,
            NotificationStructureOwnershipTransferred,
            NotificationStructureRefueledExtra,
            NotificationStructureReinforceChange,
            NotificationStructureServicesOffline,
            NotificationStructureUnanchoring,
            NotificationStructureUnderAttack,
            NotificationStructureWentHighPower,
            NotificationStructureWentLowPower,
        )
        from .tower_embeds import (
            NotificationTowerAlertMsg,
            NotificationTowerRefueledExtra,
            NotificationTowerReinforcedExtra,
            NotificationTowerResourceAlertMsg,
        )
        from .war_embeds import (
            NotificationAcceptedAlly,
            NotificationAllWarCorpJoinedAllianceMsg,
            NotificationAllWarSurrenderMsg,
            NotificationAllyJoinedWarMsg,
            NotificationCorpWarSurrenderMsg,
            NotificationDeclareWar,
            NotificationMercOfferedNegotiationMsg,
            NotificationMercOfferRetractedMsg,
            NotificationOfferedSurrender,
            NotificationOfferedToAlly,
            NotificationWarAdopted,
            NotificationWarCorporationBecameEligible,
            NotificationWarCorporationNoLongerEligible,
            NotificationWarDeclared,
            NotificationWarHQRemovedFromSpace,
            NotificationWarInherited,
            NotificationWarInvalid,
            NotificationWarRetractedByConcord,
            NotificationWarSurrenderOfferMsg,
        )

        if not isinstance(notif, NotificationBase):
            raise TypeError("notification must be of type NotificationBase")

        NT = NotificationType
        notif_type_2_class = {
            # Billing
            NT.BILLING_BILL_OUT_OF_MONEY_MSG: NotificationBillingBillOutOfMoneyMsg,
            NT.BILLING_CORP_ALL_BILL_MSG: NotificationCorpAllBillMsg,
            NT.BILLING_I_HUB_BILL_ABOUT_TO_EXPIRE: NotificationBillingIHubBillAboutToExpire,
            NT.BILLING_I_HUB_DESTROYED_BY_BILL_FAILURE: NotificationBillingIHubDestroyedByBillFailure,
            # character
            NT.CHAR_APP_ACCEPT_MSG: NotificationCharAppAcceptMsg,
            NT.CHAR_APP_WITHDRAW_MSG: NotificationCharAppWithdrawMsg,
            NT.CHAR_LEFT_CORP_MSG: NotificationCharLeftCorpMsg,
            NT.CORP_APP_INVITED_MSG: NotificationCorpAppInvitedMsg,
            NT.CORP_APP_NEW_MSG: NotificationCorpAppNewMsg,
            NT.CORP_APP_REJECT_CUSTOM_MSG: NotificationCorpAppRejectCustomMsg,
            NT.CORP_APP_REJECT_MSG: NotificationCharAppRejectMsg,
            # moonmining
            NT.MOONMINING_AUTOMATIC_FRACTURE: NotificationMoonminningAutomaticFracture,
            NT.MOONMINING_EXTRACTION_CANCELLED: NotificationMoonminningExtractionCanceled,
            NT.MOONMINING_EXTRACTION_FINISHED: NotificationMoonminningExtractionFinished,
            NT.MOONMINING_EXTRACTION_STARTED: NotificationMoonminningExtractionStarted,
            NT.MOONMINING_LASER_FIRED: NotificationMoonminningLaserFired,
            # Orbitals
            NT.ORBITAL_ATTACKED: NotificationOrbitalAttacked,
            NT.ORBITAL_REINFORCED: NotificationOrbitalReinforced,
            # Sov
            NT.SOV_ALL_ANCHORING_MSG: NotificationSovAllAnchoringMsg,
            NT.SOV_ALL_CLAIM_ACQUIRED_MSG: NotificationSovAllClaimAcquiredMsg,
            NT.SOV_ALL_CLAIM_LOST_MSG: NotificationSovAllClaimLostMsg,
            NT.SOV_COMMAND_NODE_EVENT_STARTED: NotificationSovCommandNodeEventStarted,
            NT.SOV_ENTOSIS_CAPTURE_STARTED: NotificationSovEntosisCaptureStarted,
            NT.SOV_STRUCTURE_DESTROYED: NotificationSovStructureDestroyed,
            NT.SOV_STRUCTURE_REINFORCED: NotificationSovStructureReinforced,
            # Towers
            NT.TOWER_ALERT_MSG: NotificationTowerAlertMsg,
            NT.TOWER_REFUELED_EXTRA: NotificationTowerRefueledExtra,
            NT.TOWER_REINFORCED_EXTRA: NotificationTowerReinforcedExtra,
            NT.TOWER_RESOURCE_ALERT_MSG: NotificationTowerResourceAlertMsg,
            # Skyhooks
            NT.SKYHOOK_DEPLOYED: NotificationSkyhookDeployed,
            NT.SKYHOOK_DESTROYED: NotificationSkyhookDestroyed,
            NT.SKYHOOK_LOST_SHIELDS: NotificationSkyhookLostShield,
            NT.SKYHOOK_ONLINE: NotificationSkyhookOnline,
            NT.SKYHOOK_UNDER_ATTACK: NotificationSkyhookUnderAttack,
            # Upwell structures
            NT.OWNERSHIP_TRANSFERRED: NotificationStructureOwnershipTransferred,
            NT.STRUCTURE_ANCHORING: NotificationStructureAnchoring,
            NT.STRUCTURE_DESTROYED: NotificationStructureDestroyed,
            NT.STRUCTURE_FUEL_ALERT: NotificationStructureFuelAlert,
            NT.STRUCTURE_JUMP_FUEL_ALERT: NotificationStructureJumpFuelAlert,
            NT.STRUCTURE_LOST_ARMOR: NotificationStructureLostArmor,
            NT.STRUCTURE_LOST_SHIELD: NotificationStructureLostShield,
            NT.STRUCTURE_LOW_REAGENTS_ALERT: NotificationStructureLowReagentsAlert,
            NT.STRUCTURE_NO_REAGENTS_ALERT: NotificationStructureNoReagentsAlert,
            NT.STRUCTURE_ONLINE: NotificationStructureOnline,
            NT.STRUCTURE_REFUELED_EXTRA: NotificationStructureRefueledExtra,
            NT.STRUCTURE_REINFORCEMENT_CHANGED: NotificationStructureReinforceChange,
            NT.STRUCTURE_SERVICES_OFFLINE: NotificationStructureServicesOffline,
            NT.STRUCTURE_UNANCHORING: NotificationStructureUnanchoring,
            NT.STRUCTURE_UNDER_ATTACK: NotificationStructureUnderAttack,
            NT.STRUCTURE_WENT_HIGH_POWER: NotificationStructureWentHighPower,
            NT.STRUCTURE_WENT_LOW_POWER: NotificationStructureWentLowPower,
            # War
            NT.WAR_ACCEPTED_ALLY: NotificationAcceptedAlly,
            NT.WAR_ALL_WAR_CORP_JOINED_ALLIANCE_MSG: NotificationAllWarCorpJoinedAllianceMsg,
            NT.WAR_ALL_WAR_SURRENDER_MSG: NotificationAllWarSurrenderMsg,
            NT.WAR_ALLY_JOINED_WAR_AGGRESSOR_MSG: NotificationAllyJoinedWarMsg,
            NT.WAR_ALLY_JOINED_WAR_ALLY_MSG: NotificationAllyJoinedWarMsg,
            NT.WAR_ALLY_JOINED_WAR_DEFENDER_MSG: NotificationAllyJoinedWarMsg,
            NT.WAR_CORP_WAR_SURRENDER_MSG: NotificationCorpWarSurrenderMsg,
            NT.WAR_CORPORATION_BECAME_ELIGIBLE: NotificationWarCorporationBecameEligible,
            NT.WAR_CORPORATION_NO_LONGER_ELIGIBLE: NotificationWarCorporationNoLongerEligible,
            NT.WAR_DECLARE_WAR: NotificationDeclareWar,
            NT.WAR_HQ_REMOVED_FROM_SPACE: NotificationWarHQRemovedFromSpace,
            NT.WAR_INVALID: NotificationWarInvalid,
            NT.WAR_MERC_OFFER_RETRACTED_MSG: NotificationMercOfferRetractedMsg,
            NT.WAR_MERC_OFFERED_NEGOTIATION_MSG: NotificationMercOfferedNegotiationMsg,
            NT.WAR_OFFERED_SURRENDER: NotificationOfferedSurrender,
            NT.WAR_OFFERED_TO_ALLY: NotificationOfferedToAlly,
            NT.WAR_WAR_ADOPTED: NotificationWarAdopted,
            NT.WAR_WAR_DECLARED: NotificationWarDeclared,
            NT.WAR_WAR_INHERITED: NotificationWarInherited,
            NT.WAR_WAR_RETRACTED_BY_CONCORD: NotificationWarRetractedByConcord,
            NT.WAR_WAR_SURRENDER_OFFER_MSG: NotificationWarSurrenderOfferMsg,
        }
        try:
            notif_class = notif_type_2_class[notif.notif_type]
        except KeyError:
            return NotificationGenericEmbed(notif)

        return notif_class(notif)


class NotificationGenericEmbed(NotificationBaseEmbed):
    """A generic embed for undefined notifs."""

    def __init__(self, notif: Notification) -> None:
        super().__init__(notif)
        self._title = re.sub(
            r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))", r" \1", notif.notif_type
        )
        self._color = Webhook.Color.INFO
        self._thumbnail = dhooks_lite.Thumbnail(
            notif.sender.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
