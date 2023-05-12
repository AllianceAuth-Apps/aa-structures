from app_utils.app_settings import clean_setting

STRUCTURES_ADD_TIMERS = clean_setting("STRUCTURES_ADD_TIMERS", True)
"""Whether to automatically add timers for certain notifications
on the timerboard (will have no effect if aa-timerboard app is not installed).
"""

STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED = clean_setting(
    "STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", True
)
"""Whether admins will get notifications about import events like
when someone adds a structure owner.
"""

STRUCTURES_DEFAULT_LANGUAGE = clean_setting("STRUCTURES_DEFAULT_LANGUAGE", "en")
"""Sets the default language to be used in case no language can be determined
e.g. this language will be used when creating timers

Please use the language codes as defined in the base.py settings file.
"""

STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED = clean_setting(
    "STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", False
)
"""Whether the structure list has default tags filter enabled by default."""

STRUCTURES_DEVELOPER_MODE = clean_setting("STRUCTURES_DEVELOPER_MODE", False)
"""Enables features for developers
e.g. write access to all models in admin and writing raw data received from ESI

UNDOCUMENTED SETTING.
"""

STRUCTURES_FEATURE_CUSTOMS_OFFICES = clean_setting(
    "STRUCTURES_FEATURE_CUSTOMS_OFFICES", True
)
"""Whether the customs offices feature is active."""

STRUCTURES_FEATURE_STARBASES = clean_setting("STRUCTURES_FEATURE_STARBASES", True)
"""Whether the starbases / POSes feature is active."""

STRUCTURES_HOURS_UNTIL_STALE_NOTIFICATION = clean_setting(
    "STRUCTURES_HOURS_UNTIL_STALE_NOTIFICATION", 24
)
"""Defines after how many hours a notification becomes stale
stale notification will no longer be sent automatically
"""

STRUCTURES_MOON_EXTRACTION_TIMERS_ENABLED = clean_setting(
    "STRUCTURES_MOON_EXTRACTION_TIMERS_ENABLED", True
)
"""Whether to create / remove timers from moon extraction notifications."""

STRUCTURES_NOTIFICATION_MAX_RETRIES = clean_setting(
    "STRUCTURES_NOTIFICATION_MAX_RETRIES", 3
)
"""Max number of retries for sending a notification if an error occurred
e.g. rate limiting.
"""

STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES = clean_setting(
    "STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES", 40
)
"""Max time in minutes since last successful notification sync
before service is reported as down.
"""

STRUCTURES_NOTIFICATIONS_DAYS_UNTIL_STALE = clean_setting(
    "STRUCTURES_NOTIFICATIONS_DAYS_UNTIL_STALE", 30
)
"""Days until notifications become stale in the database.
Stale notifications will be deleted automatically.
"""

STRUCTURES_NOTIFICATIONS_DELETE_BATCH_SIZE = clean_setting(
    "STRUCTURES_NOTIFICATIONS_DELETE_BATCH_SIZE", 2000
)
"""How many notifications are deleted in one batch."""

STRUCTURES_NOTIFICATIONS_DELETE_BATCH_SIZE = clean_setting(
    "STRUCTURES_NOTIFICATIONS_DELETE_BATCH_SIZE", 2000
)
"""How many notifications are deleted in one batch."""


STRUCTURES_NOTIFICATION_WAIT_SEC = clean_setting("STRUCTURES_NOTIFICATION_WAIT_SEC", 5)
"""Default wait time in seconds before retrying to send a notification
to Discord after an error occurred.
"""

STRUCTURES_NOTIFICATIONS_ARCHIVING_ENABLED = clean_setting(
    "STRUCTURES_NOTIFICATIONS_ARCHIVING_ENABLED", False
)
"""Enables archiving of all notifications received from ESI to files
notifications will by stored into one continuous file per corporations
UNDOCUMENTED SETTING.
"""
STRUCTURES_NOTIFICATION_SET_AVATAR = clean_setting(
    "STRUCTURES_NOTIFICATION_SET_AVATAR", True
)
"""Wether structures sets the name and avatar icon of a webhook
else the webhook will show it's default names as set when defining the webhook.
"""

STRUCTURES_NOTIFICATION_SHOW_MOON_ORE = clean_setting(
    "STRUCTURES_NOTIFICATION_SHOW_MOON_ORE", True
)
"""Wether ore details are shown on moon timers."""

STRUCTURES_REPORT_NPC_ATTACKS = clean_setting("STRUCTURES_REPORT_NPC_ATTACKS", True)
"""How to handle notification about NPC attacks."""

STRUCTURES_SHOW_FUEL_EXPIRES_RELATIVE = clean_setting(
    "STRUCTURES_SHOW_FUEL_EXPIRES_RELATIVE", True
)
"""Whether fuel expires in structures browser is shown as absolute value."""

STRUCTURES_SHOW_JUMP_GATES = clean_setting("STRUCTURES_SHOW_JUMP_GATES", True)
"""Whether to show the jump gates tab."""

STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES = clean_setting(
    "STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES", 120
)
"""Max time in minutes since last successful structures sync
before service is reported as down.
"""

STRUCTURES_TASKS_TIME_LIMIT = clean_setting("STRUCTURES_TASKS_TIME_LIMIT", 7200)
"""Hard timeout for tasks in seconds to reduce task accumulation during outages."""

STRUCTURES_TIMERS_ARE_CORP_RESTRICTED = clean_setting(
    "STRUCTURES_TIMERS_ARE_CORP_RESTRICTED", False
)
"""Whether created timers are corp restricted on the timerboard."""

STRUCTURES_ESI_TIMEOUT_ENABLED = clean_setting("STRUCTURES_ESI_TIMEOUT_ENABLED", True)
"""Whether ESI timeout is enabled."""

STRUCTURES_DEFAULT_PAGE_LENGTH = clean_setting("STRUCTURES_DEFAULT_PAGE_LENGTH", 10)
"""Default page size for structure list.

Must be an integer value from the current options as seen in the app.
"""

STRUCTURES_PAGING_ENABLED = clean_setting("STRUCTURES_PAGING_ENABLED", True)
"""Wether paging is enabled for the structure list."""

# INTERNAL SETTINGS

STRUCTURES_NOTIFICATION_TURNAROUND_SHORT = clean_setting(
    "STRUCTURES_NOTIFICATION_TURNAROUND_SHORT", 5
)
"""Number of notifications to count for short mean turnaround time."""

STRUCTURES_NOTIFICATION_TURNAROUND_MEDIUM = clean_setting(
    "STRUCTURES_NOTIFICATION_TURNAROUND_MEDIUM", 15
)
"""Number of notifications to count for medium mean turnaround time."""

STRUCTURES_NOTIFICATION_TURNAROUND_LONG = clean_setting(
    "STRUCTURES_NOTIFICATION_TURNAROUND_LONG", 50
)
"""Number of notifications to count for long mean turnaround time."""

STRUCTURES_NOTIFICATION_TURNAROUND_MAX_VALID = clean_setting(
    "STRUCTURES_NOTIFICATION_TURNAROUND_MAX_VALID", 3600
)
"""Turnaround duration with more than x seconds are regarded as outliers
and will be ignored when calculating the averages.
"""

STRUCTURES_NOTIFY_THROTTLED_TIMEOUT = clean_setting(
    "STRUCTURES_NOTIFY_THROTTLED_TIMEOUT", 86400
)
"""Timeout for throttled issue notifications to users and admins in seconds."""

STRUCTURES_NOTIFICATION_DISABLE_ESI_FUEL_ALERTS = clean_setting(
    "STRUCTURES_NOTIFICATION_DISABLE_ESI_FUEL_ALERTS", False
)
"""This allows you to turn off ESI fuel alert notifications
to use the Structure's generated fuel notifications exclusively.
"""

STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS = clean_setting(
    "STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS", True
)
"""Feature flag to enable refueled notifications"""

STRUCTURES_ESI_DIRECTOR_ERROR_MAX_RETRIES = clean_setting(
    "STRUCTURES_ESI_DIRECTOR_ERROR_MAX_RETRIES", 3
)
"""Max retries before a character is deleted when ESI claims the character
is not a director (Since this sometimes is reported wrongly by ESI).
"""
