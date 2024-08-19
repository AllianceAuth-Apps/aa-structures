# flake8: noqa
"""
this scripts create a test owner and adds test notifications to it
"""

import datetime as dt
import json
from pathlib import Path

from app_utils.scripts import start_django

start_django()


def main():

    from django.utils.timezone import now
    from esi.clients import esi_client_factory
    from eveuniverse.models import EveEntity

    from allianceauth.eveonline.models import EveCorporationInfo

    from structures.core.notification_types import NotificationType
    from structures.models import Notification, Owner, Structure, Webhook

    # corporation / structure the notifications will be added to
    CORPORATION_ID = 1000127  # Guristas

    print(
        "load_test_notifications - "
        "script loads test notification into the local database "
    )

    print("Connecting to ESI ...")
    client = esi_client_factory()

    print("Creating base data ...")
    try:
        corporation = EveCorporationInfo.objects.get(corporation_id=CORPORATION_ID)
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(CORPORATION_ID)

    owner, created = Owner.objects.get_or_create(
        corporation=corporation, defaults={"is_active": False}
    )
    if created and not owner.webhooks.exists():
        webhook = Webhook.objects.filter(is_active=True, is_default=True).first()
        if webhook:
            owner.webhooks.add(webhook)

    structure = {
        "fuel_expires": None,
        "name": "Test Structure Alpha",
        "next_reinforce_apply": None,
        "next_reinforce_hour": None,
        "position": {"x": 55028384780.0, "y": 7310316270.0, "z": -163686684205.0},
        "profile_id": 101853,
        "reinforce_hour": 18,
        "services": [
            {
                "name": "Clone Bay",
                "name_de": "Clone Bay_de",
                "name_ko": "Clone Bay_ko",
                "state": "online",
            },
            {
                "name": "Market Hub",
                "name_de": "Market Hub_de",
                "name_ko": "Market Hub_ko",
                "state": "offline",
            },
        ],
        "state": "shield_vulnerable",
        "state_timer_end": None,
        "state_timer_start": None,
        "structure_id": 1999999999999,
        "system_id": 30002537,
        "type_id": 35832,
        "unanchors_at": None,
    }
    structure, _ = Structure.objects.update_or_create_from_dict(structure, owner)

    p = Path(__file__).parent / "/entities.json"
    with p.open(mode="r", encoding="utf-8") as fp:
        data = json.load(fp)

    notifications = data["Notification"]
    for n in notifications:
        if n["sender_id"] == 2901:
            n["sender_id"] = 1000137  # DED
        if n["sender_id"] == 2902:
            n["sender_id"] = 1000125  # Concord
        elif n["sender_id"] == 1011:
            n["sender_id"] = 3004029
        elif n["sender_id"] == 2022:
            n["sender_id"] = 1000127  # Guristas
        elif n["sender_id"] == 3001:
            n["sender_id"] = 99010298
        n["text"] = n["text"].replace("1000000000001", str(structure.id))
        n["text"] = n["text"].replace("35835", str(structure.eve_type_id))
        n["text"] = n["text"].replace("35835", str(structure.eve_type_id))
        n["text"] = n["text"].replace("30002537", str(structure.eve_solar_system_id))
        n["text"] = n["text"].replace("1001", "3004037")
        n["text"] = n["text"].replace("1002", "3019491")
        n["text"] = n["text"].replace("1011", "3004029")
        n["text"] = n["text"].replace("2001", "98394960")
        n["text"] = n["text"].replace("2002", "1000134")  # Blood Raiders
        n["text"] = n["text"].replace("3001", "99005502")
        n["text"] = n["text"].replace("3002", "99009333")
        n["text"] = n["text"].replace("3011", "1354830081")

    timestamp_start = now() - dt.timedelta(hours=2)

    for n in notifications:
        notif_type = n["type"]
        if notif_type not in NotificationType.values:
            print(f"Skipping unsupported: {notif_id} {notif_type}")

        notif_id = n["notification_id"]
        sender, _ = EveEntity.objects.get_or_create_esi(id=n["sender_id"])
        text = n["text"] if "text" in n else None
        is_read = n["is_read"] if "is_read" in n else None
        timestamp_start = timestamp_start + dt.timedelta(minutes=5)
        obj, created = Notification.objects.update_or_create(
            notification_id=notif_id,
            owner=owner,
            defaults={
                "sender": sender,
                "timestamp": timestamp_start,
                "notif_type": notif_type,
                "text": text,
                "is_read": is_read,
                "last_updated": now(),
                "is_sent": False,
            },
        )
        if created:
            print(f"Created: {notif_id} {notif_type}")

    print("DONE")

    """
    for notification in notifications:
        dt = datetime.datetime.utcfromtimestamp(notification['timestamp'])
        dt = pytz.utc.localize(dt)
        notification['timestamp'] = dt.isoformat()

    with open(
        file=currentdir + '/td_notifications_2.json',
        mode='w',
        encoding='utf-8'
    ) as f:
        json.dump(
            notifications,
            f,
            sort_keys=True,
            indent=4
        )

    """


if __name__ == "__main__":
    main()
