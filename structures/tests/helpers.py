import datetime as dt
import unicodedata

from bs4 import BeautifulSoup
from markdown import markdown

from django.core.cache import cache
from django.test import TestCase


def datetime_to_ldap(my_dt: dt.datetime) -> int:
    """Return a standard datetime as ldap datetime."""
    return (
        ((my_dt - dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)).total_seconds())
        + 11644473600
    ) * 10000000


def markdown_to_plain(text: str) -> str:
    """Convert text in markdown to plain text."""
    html = markdown(text)
    text = "".join(BeautifulSoup(html, features="html.parser").findAll(text=True))
    return unicodedata.normalize("NFKD", text)


class TestCaseWithClearCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
