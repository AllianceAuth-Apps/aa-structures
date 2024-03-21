"""War embeds."""

# pylint: disable=missing-class-docstring


import dhooks_lite

from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from app_utils.datetime import ldap_time_2_datetime
from app_utils.helpers import humanize_number

from structures.helpers import get_or_create_eve_entity
from structures.models import Notification, Webhook

from .helpers import gen_eve_entity_link, target_datetime_formatted
from .main import NotificationBaseEmbed


class NotificationAcceptedAlly(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Accepted Ally")
        ally = get_or_create_eve_entity(id=self._data["allyID"])
        enemy = get_or_create_eve_entity(id=self._data["enemyID"])
        character = get_or_create_eve_entity(id=self._data["charID"])
        isk_value = self._data["iskValue"]
        time = ldap_time_2_datetime(self._data["time"])
        self._description = _(
            "%(ally)s has been accepted in a war against %(enemy)s. "
            "The offer was accepted at %(time)s by %(character)s for %(isk_value)s ISK."
        ) % {
            "enemy": gen_eve_entity_link(enemy),
            "ally": gen_eve_entity_link(ally),
            "character": gen_eve_entity_link(character),
            "isk_value": humanize_number(isk_value),
            "time": target_datetime_formatted(time),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            ally.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.WARNING


class NotificationAllWarCorpJoinedAllianceMsg(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Corporation you are at war with is joining an alliance")
        alliance = get_or_create_eve_entity(id=self._data["allianceID"])
        corporation = get_or_create_eve_entity(id=self._data["corpID"])
        self._description = _(
            "%(corporation)s is joining %(alliance)s alliance. "
            "Since you are at war with %(corporation)s, "
            "in 24 hours you will also be at war with %(alliance)s."
        ) % {
            "alliance": gen_eve_entity_link(alliance),
            "corporation": gen_eve_entity_link(corporation),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            corporation.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.INFO


class NotificationAllyJoinedWarMsg(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Ally Has Joined a War")
        aggressor = get_or_create_eve_entity(id=self._data["aggressorID"])
        ally = get_or_create_eve_entity(id=self._data["allyID"])
        defender = get_or_create_eve_entity(id=self._data["defenderID"])
        start_time = ldap_time_2_datetime(self._data["startTime"])
        self._description = _(
            "%(ally)s has joined %(defender)s in a war against %(aggressor)s. "
            "Their participation in the war will start at %(start_time)s."
        ) % {
            "aggressor": gen_eve_entity_link(aggressor),
            "ally": gen_eve_entity_link(ally),
            "defender": gen_eve_entity_link(defender),
            "start_time": target_datetime_formatted(start_time),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            ally.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.WARNING


class NotificationDeclareWar(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        entity = get_or_create_eve_entity(id=self._data["entityID"])
        defender = get_or_create_eve_entity(id=self._data["defenderID"])
        self._title = _("%(entity)s Declares War Against %(defender)s") % {
            "entity": entity.name,
            "defender": defender.name,
        }
        self._description = _(
            "%(entity)s has declared war on %(defender)s. "
            "Within 24 hours fighting can legally occur between those involved."
        ) % {
            "entity": gen_eve_entity_link(entity),
            "defender": gen_eve_entity_link(defender),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            entity.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.DANGER


class NotificationMercOfferedNegotiationMsg(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        aggressor = get_or_create_eve_entity(id=self._data["aggressorID"])
        defender = get_or_create_eve_entity(id=self._data["defenderID"])
        mercenary = get_or_create_eve_entity(id=self._data["mercID"])
        isk_value = self._data["iskValue"]
        self._title = (
            _("%s has offered its services in one of your wars") % mercenary.name
        )
        self._description = _(
            "%(mercenary)s has offered %(defender)s it's services in it's war against %(aggressor)s for %(isk_value)s. "
        ) % {
            "aggressor": gen_eve_entity_link(aggressor),
            "defender": gen_eve_entity_link(defender),
            "mercenary": gen_eve_entity_link(mercenary),
            "isk_value": humanize_number(isk_value),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            mercenary.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.INFO


class NotificationMercOfferRetractedMsg(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Mercenary offered services")
        aggressor = get_or_create_eve_entity(id=self._data["aggressorID"])
        defender = get_or_create_eve_entity(id=self._data["defenderID"])
        mercenary = get_or_create_eve_entity(id=self._data["mercID"])
        self._description = _(
            "%(mercenary)s has retracted it's offer to support %(defender)s in a war against %(aggressor)s."
        ) % {
            "aggressor": gen_eve_entity_link(aggressor),
            "defender": gen_eve_entity_link(defender),
            "mercenary": gen_eve_entity_link(mercenary),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            mercenary.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.INFO


class NotificationOfferedToAlly(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        aggressor = get_or_create_eve_entity(id=self._data["aggressorID"])
        defender = get_or_create_eve_entity(id=self._data["defenderID"])
        character = get_or_create_eve_entity(id=self._data["mercID"])
        isk_value = self._data["iskValue"]
        self._title = _("You have offered to ally with %s ") % defender.name
        self._description = _(
            "%(character)s has offered to ally to %(defender)s in their war "
            "against %(aggressor)s. The offer asked for %(isk_value)s ISK as payment."
        ) % {
            "aggressor": gen_eve_entity_link(aggressor),
            "defender": gen_eve_entity_link(defender),
            "character": gen_eve_entity_link(character),
            "isk_value": humanize_number(isk_value),
        }
        self._thumbnail = dhooks_lite.Thumbnail(
            character.icon_url(size=self.ICON_DEFAULT_SIZE)
        )
        self._color = Webhook.Color.INFO


class NotificationOfferedSurrender(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        character = get_or_create_eve_entity(id=self._data["charID"])
        entity = get_or_create_eve_entity(id=self._data["entityID"])
        offered = get_or_create_eve_entity(id=self._data["offeredID"])
        isk_value = self._data["iskValue"]
        self._title = _("%s offered to surrender") % entity.name
        self._description = _(
            "%(character)s has offered to surrender to %(offered)s, "
            "offering %(isk_value)s ISK. If accepted, the war will end in 24 hours "
            "and neither organization will be able to declare new wars against "
            "the other for the next 2 weeks."
        ) % {
            "character": gen_eve_entity_link(character),
            "offered": gen_eve_entity_link(offered),
            "isk_value": humanize_number(isk_value),
        }
        self._color = Webhook.Color.WARNING


class NotificationWarCorporationBecameEligible(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _(
            "Corporation or alliance is now eligible for formal war declarations"
        )
        self._description = _(
            "Your corporation or alliance is **now eligible** to participate in "
            "formal war declarations. This could be because your corporation "
            "and/or one of the corporations in your alliance owns a structure "
            "deployed in space."
        )
        self._color = Webhook.Color.WARNING


class NotificationWarCorporationNoLongerEligible(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _(
            "Corporation or alliance is no longer eligible for formal war declarations"
        )
        self._description = _(
            "Your corporation or alliance is **no longer eligible** to participate "
            "in formal war declarations.\n"
            "Neither your corporation nor any of the corporations "
            "in your alliance own a structure deployed in space at this time. "
            "If your corporation or alliance is currently involved in a formal war, "
            "that war will end in 24 hours."
        )
        self._color = Webhook.Color.INFO


class NotificationWarSurrenderOfferMsg(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        owner_1 = get_or_create_eve_entity(id=self._data.get("ownerID1"))
        owner_2 = get_or_create_eve_entity(id=self._data.get("ownerID2"))
        isk_value = self._data.get("iskValue", 0)
        self._title = _("%s has offered a surrender") % owner_1.name
        self._description = _(
            "%(owner_1)s has offered to end the war with %(owner_2)s in the exchange "
            "for %(isk_value)s ISK. "
            "If accepted, the war will end in 24 hours and your organizations will "
            "be unable to declare new wars against each other for the next 2 weeks."
        ) % {
            "owner_1": gen_eve_entity_link(owner_1),
            "owner_2": gen_eve_entity_link(owner_2),
            "isk_value": humanize_number(isk_value),
        }
        self._color = Webhook.Color.INFO


#################################
# War notifs with common elements
#################################


class NotificationWarBaseEmbed(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._declared_by = get_or_create_eve_entity(id=self._data["declaredByID"])
        self._against = get_or_create_eve_entity(id=self._data["againstID"])
        self._thumbnail = dhooks_lite.Thumbnail(
            self._declared_by.icon_url(size=self.ICON_DEFAULT_SIZE)
        )


class NotificationAllWarSurrenderMsg(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%s has surrendered") % self._declared_by.name
        self._description = _(
            "%(declared_by)s has surrendered in the war against  %(against)s."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
        }
        self._color = Webhook.Color.WARNING


class NotificationCorpWarSurrenderMsg(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("One party has surrendered")
        self._description = _(
            "The war between %(against)s and %(declared_by)s is coming to an end "
            "as one party has surrendered. "
            "The war will be declared as being over after approximately 24 hours."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
        }
        self._color = Webhook.Color.WARNING


class NotificationWarHQRemovedFromSpace(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        war_hq = self._data["warHQ"]
        time_declared = ldap_time_2_datetime(self._data["timeDeclared"])
        self._title = _("WarHQ %s lost") % war_hq
        self._description = _(
            "The war HQ %(war_hq)s is no more. "
            "As a consequence, the war declared by %(declared_by)s "
            "against %(against)s on %(time_declared)s "
            "has been declared invalid by CONCORD and has entered its cooldown period."
        ) % {
            "war_hq": war_hq,
            "declared_by": self._declared_by,
            "against": self._against,
            "time_declared": time_declared,
        }
        self._color = Webhook.Color.WARNING


class NotificationWarAdopted(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        alliance = get_or_create_eve_entity(id=self._data["allianceID"])
        self._title = _("War update: %(against)s has left %(alliance)s") % {
            "against": self._against.name,
            "alliance": alliance.name,
        }
        self._description = _(
            "There has been a development in the war between %(declared_by)s "
            "and %(alliance)s.\n"
            "%(against)s is no longer a member of %(alliance)s, "
            "and therefore a new war between %(declared_by)s and %(against)s has begun."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
            "alliance": gen_eve_entity_link(alliance),
        }
        self._color = Webhook.Color.WARNING


class NotificationWarDeclared(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%(declared_by)s Declares War Against %(against)s") % {
            "declared_by": self._declared_by.name,
            "against": self._against.name,
        }
        self._description = _(
            "%(declared_by)s has declared war on %(against)s with %(war_hq)s "
            "as the designated war headquarters.\n"
            "Within %(delay_hours)s hours fighting can legally occur "
            "between those involved."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
            "war_hq": Webhook.text_bold(strip_tags(self._data["warHQ"])),
            "delay_hours": Webhook.text_bold(self._data["delayHours"]),
        }
        self._color = Webhook.Color.DANGER


class NotificationWarInherited(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        alliance = get_or_create_eve_entity(id=self._data["allianceID"])
        opponent = get_or_create_eve_entity(id=self._data["opponentID"])
        quitter = get_or_create_eve_entity(id=self._data["quitterID"])
        self._title = _("%(alliance)s inherits war against %(opponent)s") % {
            "alliance": alliance.name,
            "opponent": opponent.name,
        }
        self._description = _(
            "%(alliance)s has inherited the war between %(declared_by)s and "
            "%(against)s from newly joined %(quitter)s. "
            "Within **24** hours fighting can legally occur with %(alliance)s."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
            "alliance": gen_eve_entity_link(alliance),
            "quitter": gen_eve_entity_link(quitter),
        }
        self._color = Webhook.Color.DANGER


class NotificationWarInvalid(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        war_ends = ldap_time_2_datetime(self._data["endDate"])
        self._title = _("CONCORD invalidates war")
        self._description = _(
            "The war between %(declared_by)s and %(against)s "
            "has been retracted by CONCORD, "
            "because at least one of the involved parties "
            "has become ineligible for war declarations."
            "Fighting must cease on %(end_date)s."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
            "end_date": target_datetime_formatted(war_ends),
        }
        self._color = Webhook.Color.WARNING


class NotificationWarRetractedByConcord(NotificationWarBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("CONCORD retracts war")
        war_ends = ldap_time_2_datetime(self._data["endDate"])
        self._description = _(
            "The war between %(declared_by)s and %(against)s "
            "has been retracted by CONCORD.\n"
            "After %(end_date)s CONCORD will again respond to any hostilities "
            "between those involved with full force."
        ) % {
            "declared_by": gen_eve_entity_link(self._declared_by),
            "against": gen_eve_entity_link(self._against),
            "end_date": target_datetime_formatted(war_ends),
        }
        self._color = Webhook.Color.WARNING
