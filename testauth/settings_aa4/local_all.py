# flake8: noqa

from .local_core import *

# Add any additional apps to this list.
INSTALLED_APPS += [
    "allianceauth.timerboard",
    "allianceauth.services.modules.discord",
    "structuretimers",
]
