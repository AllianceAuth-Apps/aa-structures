"""Global definition of known notification types."""

from typing import List, Set

from django.db import models
from django.utils.translation import gettext_lazy as _

from structures.app_settings import STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS


class NotificationType(models.TextChoices):
    """Definition of all supported notification types."""

    # upwell structures
    OWNERSHIP_TRANSFERRED = "OwnershipTransferred", _(
        "Upwell structure ownership transferred"
    )
    STRUCTURE_ANCHORING = "StructureAnchoring", _("Upwell structure anchoring")
    STRUCTURE_DESTROYED = "StructureDestroyed", _("Upwell structure destroyed")
    STRUCTURE_FUEL_ALERT = "StructureFuelAlert", _("Upwell structure fuel alert")
    STRUCTURE_JUMP_FUEL_ALERT = "StructureJumpFuelAlert", _(
        "Upwell structure jump fuel alert"
    )
    STRUCTURE_LOST_ARMOR = "StructureLostArmor", _("Upwell structure lost armor")
    STRUCTURE_LOST_SHIELD = "StructureLostShields", _("Upwell structure lost shields")
    STRUCTURE_LOW_REAGENTS_ALERT = "StructureLowReagentsAlert", _(
        "Structure low reagents alert"
    )
    STRUCTURE_NO_REAGENTS_ALERT = "StructureNoReagentsAlert", _(
        "Structure no reagents alert"
    )
    STRUCTURE_ONLINE = "StructureOnline", _("Upwell structure went online")
    STRUCTURE_REFUELED_EXTRA = "StructureRefueledExtra", _("Upwell structure refueled")
    STRUCTURE_REINFORCEMENT_CHANGED = "StructuresReinforcementChanged", _(
        "Upwell structure reinforcement time changed"
    )
    STRUCTURE_SERVICES_OFFLINE = "StructureServicesOffline", _(
        "Upwell structure services went offline"
    )
    STRUCTURE_UNANCHORING = "StructureUnanchoring", _("Upwell structure unanchoring")
    STRUCTURE_UNDER_ATTACK = "StructureUnderAttack", _(
        "Upwell structure is under attack"
    )
    STRUCTURE_WENT_HIGH_POWER = "StructureWentHighPower", _(
        "Upwell structure went high power"
    )
    STRUCTURE_WENT_LOW_POWER = "StructureWentLowPower", _(
        "Upwell structure went low power"
    )

    # Skyhook structures
    SKYHOOK_DEPLOYED = "SkyhookDeployed", _("Skyhook deployed")
    SKYHOOK_DESTROYED = "SkyhookDestroyed", _("Skyhook destroyed")
    SKYHOOK_LOST_SHIELDS = "SkyhookLostShields", _("Skyhook lost shields")
    SKYHOOK_ONLINE = "SkyhookOnline", _("Skyhook online")
    SKYHOOK_UNDER_ATTACK = "SkyhookUnderAttack", _("Skyhook under attack")

    # customs offices
    ORBITAL_ATTACKED = "OrbitalAttacked", _("Customs office attacked")
    ORBITAL_REINFORCED = "OrbitalReinforced", _("Customs office reinforced")

    # starbases
    TOWER_ALERT_MSG = "TowerAlertMsg", _("Starbase attacked")
    TOWER_REFUELED_EXTRA = "TowerRefueledExtra", _("Starbase refueled (BETA)")
    TOWER_REINFORCED_EXTRA = "TowerReinforcedExtra", _("Starbase reinforced (BETA)")
    TOWER_RESOURCE_ALERT_MSG = "TowerResourceAlertMsg", _("Starbase fuel alert")

    # moon mining
    MOONMINING_AUTOMATIC_FRACTURE = "MoonminingAutomaticFracture", _(
        "Moon mining automatic fracture triggered"
    )
    MOONMINING_EXTRACTION_CANCELLED = "MoonminingExtractionCancelled", _(
        "Moon mining extraction cancelled"
    )
    MOONMINING_EXTRACTION_FINISHED = "MoonminingExtractionFinished", _(
        "Moon mining extraction finished"
    )
    MOONMINING_EXTRACTION_STARTED = "MoonminingExtractionStarted", _(
        "Moon mining extraction started"
    )
    MOONMINING_LASER_FIRED = "MoonminingLaserFired", _("Moonmining laser fired")

    # sov
    SOV_ALL_CLAIM_ACQUIRED_MSG = "SovAllClaimAquiredMsg", _(
        "Sovereignty claim acknowledgment"  # SovAllClaimAquiredMsg [sic!]
    )
    SOV_ALL_CLAIM_LOST_MSG = "SovAllClaimLostMsg", _("Sovereignty lost")
    SOV_ALL_ANCHORING_MSG = "AllAnchoringMsg", _(
        "Structure anchoring in alliance space"
    )
    SOV_ENTOSIS_CAPTURE_STARTED = "EntosisCaptureStarted", _(
        "Sovereignty entosis capture started"
    )
    SOV_STRUCTURE_DESTROYED = "SovStructureDestroyed", _(
        "Sovereignty structure destroyed"
    )
    SOV_STRUCTURE_REINFORCED = "SovStructureReinforced", _(
        "Sovereignty structure reinforced"
    )
    SOV_COMMAND_NODE_EVENT_STARTED = "SovCommandNodeEventStarted", _(
        "Sovereignty command node event started"
    )

    # wars
    WAR_ACCEPTED_ALLY = "AcceptedAlly", _("War accepted ally")
    WAR_ALL_WAR_CORP_JOINED_ALLIANCE_MSG = "AllWarCorpJoinedAllianceMsg", _(
        "Alliance war corporation joined alliance message"
    )
    WAR_ALL_WAR_SURRENDER_MSG = "AllWarSurrenderMsg", _(
        "Alliance war surrender message"
    )
    WAR_ALLY_JOINED_WAR_AGGRESSOR_MSG = "AllyJoinedWarAggressorMsg", _(
        "War ally joined aggressor"
    )
    WAR_ALLY_JOINED_WAR_ALLY_MSG = "AllyJoinedWarAllyMsg", _("War ally joined ally")
    WAR_ALLY_JOINED_WAR_DEFENDER_MSG = "AllyJoinedWarDefenderMsg", _(
        "War ally joined defender"
    )
    WAR_CORP_WAR_SURRENDER_MSG = "CorpWarSurrenderMsg", _("War party surrendered")
    WAR_CORPORATION_BECAME_ELIGIBLE = "CorpBecameWarEligible", _(
        "War corporation became eligible"
    )
    WAR_CORPORATION_NO_LONGER_ELIGIBLE = "CorpNoLongerWarEligible", _(
        "War corporation no longer eligible"
    )
    WAR_DECLARE_WAR = "DeclareWar", _("War declared")
    WAR_HQ_REMOVED_FROM_SPACE = "WarHQRemovedFromSpace", _("War HQ removed from space")
    WAR_INVALID = "WarInvalid", _("War invalid")
    WAR_MERC_OFFERED_NEGOTIATION_MSG = "MercOfferedNegotiationMsg", _(
        "War mercenary offered negotiation message"
    )
    WAR_MERC_OFFER_RETRACTED_MSG = "MercOfferRetractedMsg", _(
        "War mercenary offer retracted message"
    )
    WAR_OFFERED_SURRENDER = "OfferedSurrender", _("War offered surrender")
    WAR_OFFERED_TO_ALLY = "OfferedToAlly", _("War offered to become ally")
    WAR_WAR_ADOPTED = "WarAdopted", _("War adopted")  # FIXME: Should be "WarAdopted "
    WAR_WAR_DECLARED = "WarDeclared", _("War declared")
    WAR_WAR_INHERITED = "WarInherited", _("War inherited")
    WAR_WAR_RETRACTED_BY_CONCORD = "WarRetractedByConcord", _(
        "War retracted by Concord"
    )
    WAR_WAR_SURRENDER_OFFER_MSG = "WarSurrenderOfferMsg", _("War surrender offered")

    # corporation membership
    CHAR_APP_ACCEPT_MSG = "CharAppAcceptMsg", _("Character joins corporation")
    CORP_APP_INVITED_MSG = "CorpAppInvitedMsg", _(
        "Character invited to join corporation"
    )
    CORP_APP_NEW_MSG = "CorpAppNewMsg", _("Character submitted application")
    CORP_APP_REJECT_MSG = "CharAppRejectMsg", _("Corp application rejected message")
    CORP_APP_REJECT_CUSTOM_MSG = "CorpAppRejectCustomMsg", _(
        "Corp application rejected custom message"
    )
    CHAR_APP_WITHDRAW_MSG = "CharAppWithdrawMsg", _("Character withdrew application")
    CHAR_LEFT_CORP_MSG = "CharLeftCorpMsg", _("Character leaves corporation")

    # billing
    BILLING_BILL_OUT_OF_MONEY_MSG = "BillOutOfMoneyMsg", _("Bill out of money")
    BILLING_CORP_ALL_BILL_MSG = "CorpAllBillMsg", _("Corp alliance billing message")
    BILLING_I_HUB_BILL_ABOUT_TO_EXPIRE = (
        "InfrastructureHubBillAboutToExpire",
        _("I-HUB bill about to expire"),
    )
    BILLING_I_HUB_DESTROYED_BY_BILL_FAILURE = (
        "IHubDestroyedByBillFailure",
        _("I_HUB destroyed by bill failure"),
    )

    @classmethod
    def esi_notifications(cls) -> Set["NotificationType"]:
        """Return all ESI notification types."""
        return set(cls) - cls.generated_notifications()

    @classmethod
    def generated_notifications(cls) -> Set["NotificationType"]:
        """Return all generated notification types."""
        return {
            cls.STRUCTURE_JUMP_FUEL_ALERT,
            cls.STRUCTURE_REFUELED_EXTRA,
            cls.TOWER_REFUELED_EXTRA,
            cls.TOWER_REINFORCED_EXTRA,
        }

    @classmethod
    def webhook_defaults(cls) -> List["NotificationType"]:
        """List of default notifications for new webhooks."""
        return [
            cls.ORBITAL_ATTACKED,
            cls.ORBITAL_REINFORCED,
            cls.SKYHOOK_DESTROYED,
            cls.SKYHOOK_LOST_SHIELDS,
            cls.SKYHOOK_ONLINE,
            cls.SKYHOOK_UNDER_ATTACK,
            cls.SOV_STRUCTURE_DESTROYED,
            cls.SOV_STRUCTURE_REINFORCED,
            cls.STRUCTURE_ANCHORING,
            cls.STRUCTURE_DESTROYED,
            cls.STRUCTURE_FUEL_ALERT,
            cls.STRUCTURE_LOST_ARMOR,
            cls.STRUCTURE_LOST_SHIELD,
            cls.STRUCTURE_LOW_REAGENTS_ALERT,
            cls.STRUCTURE_NO_REAGENTS_ALERT,
            cls.STRUCTURE_ONLINE,
            cls.STRUCTURE_SERVICES_OFFLINE,
            cls.STRUCTURE_UNDER_ATTACK,
            cls.STRUCTURE_WENT_HIGH_POWER,
            cls.STRUCTURE_WENT_LOW_POWER,
            cls.TOWER_ALERT_MSG,
            cls.TOWER_RESOURCE_ALERT_MSG,
        ]

    @classmethod
    def relevant_for_timerboard(cls) -> Set["NotificationType"]:
        """Notification types that can create timers."""
        return {
            cls.MOONMINING_EXTRACTION_CANCELLED,
            cls.MOONMINING_EXTRACTION_STARTED,
            cls.ORBITAL_REINFORCED,
            cls.SOV_STRUCTURE_REINFORCED,
            cls.STRUCTURE_LOST_ARMOR,
            cls.STRUCTURE_LOST_SHIELD,
            cls.TOWER_REINFORCED_EXTRA,
            cls.SKYHOOK_LOST_SHIELDS,
        }

    @classmethod
    def relevant_for_alliance_level(cls) -> Set["NotificationType"]:
        """Notification types that require the alliance level flag."""
        return {
            # billing
            cls.BILLING_BILL_OUT_OF_MONEY_MSG,
            cls.BILLING_I_HUB_BILL_ABOUT_TO_EXPIRE,
            cls.BILLING_I_HUB_DESTROYED_BY_BILL_FAILURE,
            # sov
            cls.SOV_ALL_CLAIM_ACQUIRED_MSG,
            cls.SOV_ALL_CLAIM_LOST_MSG,
            cls.SOV_COMMAND_NODE_EVENT_STARTED,
            cls.SOV_ENTOSIS_CAPTURE_STARTED,
            cls.SOV_STRUCTURE_DESTROYED,
            cls.SOV_STRUCTURE_REINFORCED,
            # cls.SOV_ALL_ANCHORING_MSG, # This notif is not broadcasted to all corporations
            # wars
            cls.WAR_ALLY_JOINED_WAR_AGGRESSOR_MSG,
            cls.WAR_ALLY_JOINED_WAR_ALLY_MSG,
            cls.WAR_ALLY_JOINED_WAR_DEFENDER_MSG,
            cls.WAR_CORP_WAR_SURRENDER_MSG,
            cls.WAR_CORPORATION_BECAME_ELIGIBLE,
            cls.WAR_CORPORATION_NO_LONGER_ELIGIBLE,
            cls.WAR_WAR_ADOPTED,
            cls.WAR_WAR_DECLARED,
            cls.WAR_WAR_INHERITED,
            cls.WAR_WAR_RETRACTED_BY_CONCORD,
            cls.WAR_WAR_SURRENDER_OFFER_MSG,
        }

    @classmethod
    def relevant_for_moonmining(cls) -> Set["NotificationType"]:
        """Notification types about moon mining."""
        return {
            cls.MOONMINING_AUTOMATIC_FRACTURE,
            cls.MOONMINING_EXTRACTION_CANCELLED,
            cls.MOONMINING_EXTRACTION_FINISHED,
            cls.MOONMINING_EXTRACTION_STARTED,
            cls.MOONMINING_LASER_FIRED,
        }

    @classmethod
    def structure_related(cls) -> Set["NotificationType"]:
        """Notification types that are related to a structure."""
        return {
            cls.MOONMINING_AUTOMATIC_FRACTURE,
            cls.MOONMINING_EXTRACTION_CANCELLED,
            cls.MOONMINING_EXTRACTION_FINISHED,
            cls.MOONMINING_EXTRACTION_STARTED,
            cls.MOONMINING_LASER_FIRED,
            cls.ORBITAL_ATTACKED,
            cls.ORBITAL_REINFORCED,
            cls.OWNERSHIP_TRANSFERRED,
            cls.STRUCTURE_ANCHORING,
            cls.STRUCTURE_DESTROYED,
            cls.STRUCTURE_FUEL_ALERT,
            cls.STRUCTURE_JUMP_FUEL_ALERT,
            cls.STRUCTURE_LOST_ARMOR,
            cls.STRUCTURE_LOST_SHIELD,
            cls.STRUCTURE_LOW_REAGENTS_ALERT,
            cls.STRUCTURE_NO_REAGENTS_ALERT,
            cls.STRUCTURE_ONLINE,
            cls.STRUCTURE_REFUELED_EXTRA,
            cls.STRUCTURE_REINFORCEMENT_CHANGED,
            cls.STRUCTURE_SERVICES_OFFLINE,
            cls.STRUCTURE_UNANCHORING,
            cls.STRUCTURE_UNDER_ATTACK,
            cls.STRUCTURE_WENT_HIGH_POWER,
            cls.STRUCTURE_WENT_LOW_POWER,
            cls.TOWER_ALERT_MSG,
            cls.TOWER_REFUELED_EXTRA,
            cls.TOWER_REINFORCED_EXTRA,
            cls.TOWER_RESOURCE_ALERT_MSG,
        }

    @classmethod
    def relevant_for_forwarding(cls) -> Set["NotificationType"]:
        """Notification types that are forwarded to Discord."""
        my_set = cls.values_enabled()
        # if STRUCTURES_NOTIFICATION_DISABLE_ESI_FUEL_ALERTS:
        #     my_set.discard(cls.STRUCTURE_FUEL_ALERT)
        #     my_set.discard(cls.TOWER_RESOURCE_ALERT_MSG)
        return my_set

    @classmethod
    def values_enabled(cls) -> Set["NotificationType"]:
        """Values of enabled notif types only."""
        my_set = set(cls.values)  # type: ignore
        if not STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS:
            my_set.discard(cls.STRUCTURE_REFUELED_EXTRA)
            my_set.discard(cls.TOWER_REFUELED_EXTRA)
        return my_set

    @classmethod
    def choices_enabled(cls) -> List[tuple]:
        """Choices list containing enabled notif types only."""
        return [choice for choice in cls.choices if choice[0] in cls.values_enabled()]
