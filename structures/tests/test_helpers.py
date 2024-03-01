import datetime as dt

from django.test import TestCase
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from eveuniverse.models import EveEntity, EveType
from eveuniverse.tests.testdata.factories_2 import EveTypeFactory

from structures.helpers import (
    datetime_almost_equal,
    floating_icon_with_text_html,
    get_or_create_esi_obj,
    get_or_create_eve_entity,
    get_or_create_eve_type,
    hours_until_deadline,
    is_absolute_url,
)

ICON_URL = "https://images.evetech.net/types/670/icon?size=64"


class TestDatetimeAlmostEqual(TestCase):
    def test_should_return_true(self):
        # given
        d1 = now() + dt.timedelta(hours=0, minutes=55)
        d2 = now() + dt.timedelta(hours=1, minutes=5)
        # when / then
        self.assertTrue(datetime_almost_equal(d1, d2, 3600))
        self.assertTrue(datetime_almost_equal(d2, d1, 3600))
        self.assertFalse(datetime_almost_equal(d2, d1, 60))
        self.assertFalse(datetime_almost_equal(d1, d2, 60))

    def test_should_return_false(self):
        # given
        d1 = now() + dt.timedelta(hours=0, minutes=55)
        d2 = now() + dt.timedelta(hours=1, minutes=5)
        # when / then
        self.assertFalse(datetime_almost_equal(d2, d1, 60))
        self.assertFalse(datetime_almost_equal(d1, d2, 60))

    def test_should_return_false_for_none_dates(self):
        # given
        d1 = now() + dt.timedelta(hours=0, minutes=55)
        # when / then
        self.assertFalse(datetime_almost_equal(d1, None, 3600))
        self.assertFalse(datetime_almost_equal(None, d1, 3600))


class TestHoursUntilDeadline(TestCase):
    def test_should_return_correct_value_for_two_datetimes(self):
        # given
        d1 = now()
        d2 = d1 - dt.timedelta(hours=3)
        # when / then
        self.assertEqual(hours_until_deadline(d1, d2), 3)

    def test_should_return_correct_value_for_one_datetimes(self):
        # given
        d1 = now() + dt.timedelta(hours=3)
        # when / then
        self.assertAlmostEqual(hours_until_deadline(d1), 3, delta=0.1)

    def test_should_raise_error_when_deadline_is_not_a_datetime(self):
        with self.assertRaises(TypeError):
            hours_until_deadline(None)


class TestIsAbsoluteUrl(TestCase):
    def test_should_detect_absolute_urls(self):
        cases = [
            ("https://www.google.com", True),
            ("http://www.google.com", True),
            ("www.google.com", False),
            ("", False),
            ("/abc/x", False),
            (None, False),
        ]
        for url, expected_result in cases:
            with self.subTest(url=url):
                self.assertIs(is_absolute_url(url), expected_result)


class TestGetOrCreateObjs(TestCase):
    def test_should_return_existing_obj_generic(self):
        # given
        obj = EveTypeFactory()
        # when
        obj_2 = get_or_create_esi_obj(EveType, id=obj.id)
        # then
        self.assertEqual(obj, obj_2)

    def test_should_return_existing_obj_type(self):
        # given
        obj = EveTypeFactory()
        # when
        obj_2 = get_or_create_eve_type(id=obj.id)
        # then
        self.assertEqual(obj, obj_2)

    def test_should_return_existing_obj_entity(self):
        # given
        obj = EveEntity.objects.create(
            id=99, name="test", category=EveEntity.CATEGORY_CHARACTER
        )
        # when
        obj_2 = get_or_create_eve_entity(id=obj.id)
        # then
        self.assertEqual(obj, obj_2)


class TestIconWithParagraphHtml(TestCase):
    def test_should_create_html_with_one_line(self):
        # when
        result = floating_icon_with_text_html(ICON_URL, ["Alpha"])
        # then
        expected = (
            '<p><img src="https://images.evetech.net/types/670/icon?size=64" '
            'class="floating-icon">Alpha</p>'
        )
        self.assertEqual(result, expected)

    def test_should_create_html_with_two_line(self):
        # when
        result = floating_icon_with_text_html("#", ["Alpha", "Bravo"])
        expected = '<p><img src="#" class="floating-icon">Alpha<br>Bravo</p>'
        self.assertEqual(result, expected)

    def test_should_create_html_and_detect_safe_strings(self):
        # when
        result = floating_icon_with_text_html(
            "#", [mark_safe('<a href="#">Alpha</a>'), "Bravo"]
        )
        expected = (
            '<p><img src="#" class="floating-icon"><a href="#">Alpha</a><br>Bravo</p>'
        )
        self.assertEqual(result, expected)

    def test_should_create_html_and_escape_unsafe_strings(self):
        # when
        result = floating_icon_with_text_html("#", ['<a href="#">Alpha</a>', "Bravo"])
        expected = (
            '<p><img src="#" class="floating-icon">'
            "&lt;a href=&quot;#&quot;&gt;Alpha&lt;/a&gt;<br>Bravo</p>"
        )
        self.assertEqual(result, expected)
