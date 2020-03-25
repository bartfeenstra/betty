import gettext
from typing import List, Optional
from unittest import TestCase

from parameterized import parameterized

from betty.locale import validate_locale, Localized, negotiate_localizeds, Date, format_datey, DateRange, Translations, \
    negotiate_locale


class DateTest(TestCase):
    def test_year(self):
        year = 1970
        sut = Date(year=year)
        self.assertEquals(year, sut.year)

    def test_month(self):
        month = 1
        sut = Date(month=month)
        self.assertEquals(month, sut.month)

    def test_day(self):
        day = 1
        sut = Date(day=day)
        self.assertEquals(day, sut.day)

    def test_fuzzy(self):
        fuzzy = True
        sut = Date()
        sut.fuzzy = fuzzy
        self.assertEquals(fuzzy, sut.fuzzy)

    @parameterized.expand([
        (True, 1970, 1, 1),
        (False, None, 1, 1),
        (True, 1970, None, 1),
        (True, 1970, 1, None),
        (False, None, None, 1),
        (True, 1970, None, None),
        (False, None, None, None),
    ])
    def test_comparable(self, expected, year, month, day):
        sut = Date(year, month, day)
        self.assertEquals(expected, sut.comparable)

    @parameterized.expand([
        (True, 1970, 1, 1),
        (False, None, 1, 1),
        (False, 1970, None, 1),
        (False, 1970, 1, None),
        (False, None, None, 1),
        (False, 1970, None, None),
        (False, None, None, None),
    ])
    def test_complete(self, expected, year, month, day):
        sut = Date(year, month, day)
        self.assertEquals(expected, sut.complete)

    def test_to_range_when_incomparable_should_raise(self):
        with self.assertRaises(ValueError):
            Date(None, 1, 1).to_range()

    @parameterized.expand([
        (1970, 1, 1),
        (None, None, None),
    ])
    def test_parts(self, year, month, day):
        self.assertEquals((year, month, day), Date(year, month, day).parts)

    @parameterized.expand([
        (False, Date(1970, 2, 1)),
        (False, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, Date(1970)),
        (False, Date(1970, 2)),
        (True, Date(1971)),
        (True, Date(1970, 3)),
    ])
    def test_lt(self, expected, other):
        self.assertEquals(expected, Date(1970, 2, 2) < other)

    @parameterized.expand([
        (True, Date(1970, 1, 1)),
        (False, Date(1970, 1, None)),
        (False, Date(1970, None, 1)),
        (False, Date(None, 1, 1)),
        (False, Date(1970, None, None)),
        (False, Date(None, 1, None)),
        (False, Date(None, None, 1)),
        (False, None),
    ])
    def test_eq(self, expected, other):
        self.assertEquals(expected, Date(1970, 1, 1) == other)
        self.assertEquals(expected, other == Date(1970, 1, 1))

    @parameterized.expand([
        (True, Date(1970, 2, 1)),
        (False, Date(1970, 2, 2)),
        (False, Date(1970, 2, 3)),
    ])
    def test_gt(self, expected, other):
        self.assertEquals(expected, Date(1970, 2, 2) > other)


class DateRangeTest(TestCase):
    @parameterized.expand([
        (False, Date(1970, 2, 1)),
        (False, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, DateRange(Date(1970, 2, 1))),
        (False, DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3))),
        (False, DateRange(None, Date(1970, 2, 1))),
        (False, DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_lt_with_start_date(self, expected, other):
        self.assertEquals(expected, DateRange(Date(1970, 2, 2)) < other)

    @parameterized.expand([
        (False, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, DateRange(Date(1970, 2, 1))),
        (True, DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3))),
        (False, DateRange(None, Date(1970, 2, 1))),
        (False, DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_lt_with_end_date(self, expected, other):
        self.assertEquals(expected, DateRange(None, Date(1970, 2, 2)) < other)

    @parameterized.expand([
        (False, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (True, DateRange(Date(1970, 2, 1))),
        (True, DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3))),
        (False, DateRange(None, Date(1970, 2, 1))),
        (True, DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_lt_with_both_dates(self, expected, other):
        self.assertEquals(expected, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)) < other)

    @parameterized.expand([
        (True, DateRange(Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, None))),
        (False, DateRange(Date(1970, None, 2))),
        (False, DateRange(Date(None, 2, 2))),
        (False, DateRange(Date(1970, None, None))),
        (False, DateRange(Date(None, 2, None))),
        (False, DateRange(Date(None, None, 2))),
        (False, None),
    ])
    def test_eq(self, expected, other):
        self.assertEquals(expected, DateRange(Date(1970, 2, 2)) == other)

    @parameterized.expand([
        (True, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (False, Date(1970, 2, 3)),
        (True, DateRange(Date(1970, 2, 1))),
        (False, DateRange(Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 3))),
        (True, DateRange(None, Date(1970, 2, 1))),
        (True, DateRange(None, Date(1970, 2, 2))),
        (False, DateRange(None, Date(1970, 2, 3))),
        (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_gt(self, expected, other):
        self.assertEquals(expected, DateRange(Date(1970, 2, 2)) > other)


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


class NegotiateLocaleTest(TestCase):
    @parameterized.expand([
        ('nl', 'nl', ['nl']),
        ('nl-NL', 'nl', ['nl-NL']),
        ('nl', 'nl-NL', ['nl']),
        ('nl-NL', 'nl-NL', ['nl', 'nl-BE', 'nl-NL']),
        ('nl', 'nl', ['nl', 'en']),
        ('nl', 'nl', ['en', 'nl']),
        ('nl-NL', 'nl-BE', ['nl-NL'])
    ])
    def test(self, expected: Optional[str], preferred_locale: str, available_locales: List[str]):
        self.assertEqual(expected, negotiate_locale(preferred_locale, available_locales))


class NegotiateLocalizedsTest(TestCase):
    class DummyLocalized(Localized):
        def __eq__(self, other):
            return self.locale == other.locale

        def __repr__(self):
            return '%s(%s)' % (self.__class__.__name__, self.locale)

    @parameterized.expand([
        (DummyLocalized('nl'), 'nl', [DummyLocalized('nl')]),
        (DummyLocalized('nl-NL'), 'nl', [DummyLocalized('nl-NL')]),
        (DummyLocalized('nl'), 'nl-NL', [DummyLocalized('nl')]),
        (DummyLocalized('nl'), 'nl', [
         DummyLocalized('nl'), DummyLocalized('en')]),
        (DummyLocalized('nl'), 'nl', [
         DummyLocalized('en'), DummyLocalized('nl')]),
    ])
    def test_with_match_should_return_match(self, expected: Localized, preferred_locale: str, localizeds: List[Localized]):
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
        with Translations(gettext.NullTranslations()):
            self.assertEquals(expected, format_datey(date, locale))
