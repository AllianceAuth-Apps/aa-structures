"""
Handles interactions with the metenox application

https://gitlab.com/r0kym/aa-metenox
"""

from metenox.models import Moon


def get_metenox_moon_value_by_moon_id(moon_id: int) -> float:
    """
    Tries to return the monthly value of a metenox'd moon.
    Returns 0 if the moon is unknown
    """

    value = 0.0
    try:
        moon = Moon.objects.get(eve_mooon__id=moon_id)
        value = moon.value
    except Moon.DoesNotExist:
        pass

    return value
