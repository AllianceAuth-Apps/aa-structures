import datetime as dt
import unicodedata

import pytz
from bs4 import BeautifulSoup
from markdown import markdown


def format_datetime_esi(my_dt: dt.datetime) -> str:
    """Convert datetime to ESI format, e.g `"2019-08-16T14:08:00Z"`."""
    utc_dt = my_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def datetime_to_ldap(my_dt: dt.datetime) -> int:
    """Return a standard datetime as ldap datetime."""
    return (
        ((my_dt - dt.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
        + 11644473600
    ) * 10000000


def markdown_to_plain(text: str) -> str:
    """Convert text in markdown to plain text."""
    html = markdown(text)
    text = "".join(BeautifulSoup(html, features="html.parser").findAll(text=True))
    return unicodedata.normalize("NFKD", text)


# end
