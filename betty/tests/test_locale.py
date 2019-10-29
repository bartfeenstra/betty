import gettext
from typing import Iterable
from unittest import TestCase

from parameterized import parameterized

from betty.locale import validate_locale, Localized, negotiate_localizeds, format_date, Date


class ValidateLocaleTest(TestCase):
    @parameterized.expand([
        ('nl',),
        ('nl-NL',),
        ('sr-Latn-CS',),
    ])
    def test_valid_value_should_pass_through(self, locale: str):
        self.assertEquals(locale, validate_locale(locale))

    @parameterized.expand([
        ('',),
        ('123',),
        ('nl-nl-nl-nl',),
    ])
    def test_invalid_value_should_raise_error(self, locale: str):
        with self.assertRaises(ValueError):
            validate_locale(locale)


class NegotiateLocalizedsTest(TestCase):
    class DummyLocalized(Localized):
        def __eq__(self, other):
            return self._locale == other._locale

        def __repr__(self):
            return '%s(%s)' % (self.__class__.__name__, self._locale)

    @parameterized.expand([
        (DummyLocalized('nl'), 'nl', [DummyLocalized('nl')]),
        (DummyLocalized('nl-NL'), 'nl', [DummyLocalized('nl-NL')]),
        (DummyLocalized('nl'), 'nl-NL', [DummyLocalized('nl')]),
        (DummyLocalized('nl'), 'nl', [
         DummyLocalized('nl'), DummyLocalized('en')]),
        (DummyLocalized('nl'), 'nl', [
         DummyLocalized('en'), DummyLocalized('nl')]),
    ])
    def test_with_match_should_return_match(self, expected: Localized, preferred_locale: str, localizeds: Iterable[Localized]):
        self.assertEquals(expected, negotiate_localizeds(
            preferred_locale, localizeds))

    def test_without_match_should_return_default(self):
        preferred_locale = 'de'
        localizeds = [self.DummyLocalized('nl'), self.DummyLocalized(
            'en'), self.DummyLocalized('uk')]
        self.assertEquals(self.DummyLocalized('nl'), negotiate_localizeds(
            preferred_locale, localizeds))

    def test_without_localizeds_should_raise_error(self):
        with self.assertRaises(ValueError):
            negotiate_localizeds('nl', [])


class FormatDateTest(TestCase):
    @parameterized.expand([
        ('unknown date', Date()),
        ('unknown date', Date(None, None, 1)),
        ('January', Date(None, 1, None)),
        ('1970', Date(1970, None, None)),
        ('January, 1970', Date(1970, 1, None)),
        ('January 1, 1970', Date(1970, 1, 1)),
        ('January 1', Date(None, 1, 1)),
    ])
    def test(self, expected: str, date: Date):
        locale = 'en'
        translation = gettext.NullTranslations()
        self.assertEquals(expected, format_date(date, locale, translation))
