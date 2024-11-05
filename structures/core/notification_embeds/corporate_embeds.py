"""Corporate embeds."""

# pylint: disable=missing-class-docstring

import dhooks_lite

from django.utils.translation import gettext as _

from structures.helpers import get_or_create_eve_entity
from structures.models import Notification, Webhook

from .helpers import (
    gen_corporation_link,
    gen_eve_entity_link,
    gen_eve_entity_link_from_id,
)
from .main import NotificationBaseEmbed


class NotificationCorpCharEmbed(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._character = get_or_create_eve_entity(id=self._data["charID"])
        self._corporation = get_or_create_eve_entity(id=self._data["corpID"])
        self._character_link = gen_eve_entity_link(self._character)
        self._corporation_link = gen_corporation_link(self._corporation.name)
        self._application_text = self._data.get("applicationText", "")
        self._thumbnail = dhooks_lite.Thumbnail(
            self._character.icon_url(size=self.ICON_DEFAULT_SIZE)
        )


class NotificationCorpAppNewMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("New application from %(character_name)s") % {
            "character_name": self._character.name,
        }
        self._description = _(
            "New application from %(character_name)s to join %(corporation_name)s:\n"
            "> %(application_text)s"
            % {
                "character_name": self._character_link,
                "corporation_name": self._corporation_link,
                "application_text": self._application_text,
            }
        )
        self._color = Webhook.Color.INFO


class NotificationCorpAppInvitedMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%(character_name)s has been invited") % {
            "character_name": self._character.name
        }
        inviting_character = gen_eve_entity_link_from_id(
            self._data.get("invokingCharID")
        )
        self._description = _(
            "%(character_name)s has been invited to join %(corporation_name)s "
            "by %(inviting_character)s.\n"
            "Application:\n"
            "> %(application_text)s"
        ) % {
            "character_name": self._character_link,
            "corporation_name": self._corporation_link,
            "inviting_character": inviting_character,
            "application_text": self._application_text,
        }

        self._color = Webhook.Color.INFO


class NotificationCharAppRejectMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%(character_name)s rejects invitation") % {
            "character_name": self._character.name
        }
        self._description = _(
            "Application from %(character_name)s to join %(corporation_name)s "
            "has been rejected."
        ) % {
            "character_name": self._character_link,
            "corporation_name": self._corporation_link,
        }
        self._color = Webhook.Color.INFO


class NotificationCorpAppRejectCustomMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Rejected application from %(character_name)s") % {
            "character_name": self._character.name
        }
        self._description = _(
            "Application from %(character_name)s to join %(corporation_name)s:\n"
            "> %(application_text)s\n"
            "Has been rejected:\n"
            "> %(customMessage)s"
        ) % {
            "character_name": self._character_link,
            "corporation_name": self._corporation_link,
            "application_text": self._application_text,
            "customMessage": self._data.get("customMessage", ""),
        }
        self._color = Webhook.Color.INFO


class NotificationCharAppWithdrawMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%(character_name)s withdrew his/her application") % {
            "character_name": self._character.name,
        }
        self._description = _(
            "%(character_name)s withdrew his/her application to join "
            "%(corporation_name)s:\n"
            "> %(application_text)s"
        ) % {
            "character_name": self._character_link,
            "corporation_name": self._corporation_link,
            "application_text": self._application_text,
        }

        self._color = Webhook.Color.INFO


class NotificationCharAppAcceptMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%(character_name)s joins %(corporation_name)s") % {
            "character_name": self._character.name,
            "corporation_name": self._corporation.name,
        }
        self._description = _(
            "%(character_name)s is now a member of %(corporation_name)s."
        ) % {
            "character_name": self._character_link,
            "corporation_name": self._corporation_link,
        }
        self._color = Webhook.Color.SUCCESS


class NotificationCharLeftCorpMsg(NotificationCorpCharEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("%(character_name)s has left %(corporation_name)s") % {
            "character_name": self._character.name,
            "corporation_name": self._corporation.name,
        }
        self._description = _(
            "%(character_name)s is no longer a member of %(corporation_name)s."
        ) % {
            "character_name": self._character_link,
            "corporation_name": self._corporation_link,
        }
        self._color = Webhook.Color.INFO


class NotificationCorpGoalEmbed(NotificationBaseEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._creator = get_or_create_eve_entity(id=self._data["creator_id"])
        self._creator_link = gen_eve_entity_link(self._creator)
        self._corporation = get_or_create_eve_entity(id=self._data["corporation_id"])
        self._goal_name = self._data["goal_name"]
        self._thumbnail = dhooks_lite.Thumbnail(
            self._corporation.icon_url(size=self.ICON_DEFAULT_SIZE)
        )


class NotificationCorpGoalClosed(NotificationCorpGoalEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Project canceled")
        closer = get_or_create_eve_entity(id=self._data["closer_id"])
        self._description = _(
            "Project **%(goal_name)s** has ben closed by %(closer)s "
            "and will not accept further contributions."
            % {
                "goal_name": self._goal_name,
                "closer": gen_eve_entity_link(closer),
            }
        )
        self._color = Webhook.Color.INFO


class NotificationCorpGoalCompleted(NotificationCorpGoalEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("Project completed")
        self._description = _(
            "Project **%(goal_name)s** created by %(creator)s "
            "has been successfully completed after reaching it's target."
            % {
                "goal_name": self._goal_name,
                "creator": self._creator_link,
            }
        )
        self._color = Webhook.Color.SUCCESS


class NotificationCorpGoalCreated(NotificationCorpGoalEmbed):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification)
        self._title = _("New Project Available")
        self._description = _(
            "Project **%(goal_name)s** has been created by %(creator)s "
            "and is open for contributions."
            % {
                "goal_name": self._goal_name,
                "creator": self._creator_link,
            }
        )
        self._color = Webhook.Color.INFO
