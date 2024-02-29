"""Resolve text for notification types."""

from typing import NamedTuple, Optional

from esi.models import Token

from structures.models import Notification


class NotificationResolved(NamedTuple):
    title: str
    text: str
    is_resolved: bool


def resolve(
    notification: Notification, token: Optional[Token] = None
) -> NotificationResolved:
    pass
