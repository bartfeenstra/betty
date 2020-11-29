import gettext
from os import makedirs, path
from tempfile import TemporaryDirectory
from typing import List, Optional

from parameterized import parameterized

from betty.locale import Localized, negotiate_localizeds, Date, format_datey, DateRange, Translations, negotiate_locale, \
    Datey, open_translations
from betty.tests import TestCase


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
        (True, Date(1970, 2, 2)),
        (False, Date(1970, 2, 3)),
        (False, DateRange()),
    ])
    def test_in(self, expected, other):
        self.assertEquals(expected, other in Date(1970, 2, 2))

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
    _TEST_IN_PARAMETERS = [
        (False, Date(1970, 2, 2), DateRange()),
        (False, Date(1970, 2), DateRange()),
        (False, Date(1970), DateRange()),
        (False, Date(1970, 2, 1), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 2), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 3), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 1), DateRange(None, Date(1970, 2, 2))),
        (True, Date(1970, 2, 2), DateRange(None, Date(1970, 2, 2))),
        (False, Date(1970, 2, 3), DateRange(None, Date(1970, 2, 2))),
        (False, Date(1969, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, Date(1970, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, Date(1971, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3)), DateRange(Date(1970, 2, 2))),
        (False, DateRange(None, Date(1970, 2, 1)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 3)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 1)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(Date(1969, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, DateRange(Date(1971, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, DateRange(None, Date(1969, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(None, Date(1971, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, DateRange(Date(1969, 2, 2), Date(1970, 2, 2)), DateRange(Date(1971, 2, 2), Date(1972, 2, 2))),
        (True, DateRange(Date(1969, 2, 2), Date(1971, 2, 2)), DateRange(Date(1970, 2, 2), Date(1972, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1971, 2, 2)), DateRange(Date(1969, 2, 2), Date(1972, 2, 2))),
    ]

    # Mirror the arguments because we want the containment check to work in either direction.
    @parameterized.expand(_TEST_IN_PARAMETERS + list(map(lambda x: (x[0], x[2], x[1]), _TEST_IN_PARAMETERS)))
    def test_in(self, expected: bool, other: Datey, sut: DateRange):
        self.assertEquals(expected, other in sut)

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
        (None, 'nl', []),
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


_FORMAT_DATE_TEST_PARAMETERS = [
    # Dates that cannot be formatted.
    ('unknown date', Date()),
    ('unknown date', Date(None, None, 1)),
    # Single dates.
    ('January', Date(None, 1, None)),
    ('around January', Date(None, 1, None, fuzzy=True)),
    ('1970', Date(1970, None, None)),
    ('around 1970', Date(1970, None, None, fuzzy=True)),
    ('January, 1970', Date(1970, 1, None)),
    ('around January, 1970', Date(1970, 1, None, fuzzy=True)),
    ('January 1, 1970', Date(1970, 1, 1)),
    ('around January 1, 1970', Date(1970, 1, 1, fuzzy=True)),
    ('January 1', Date(None, 1, 1)),
    ('around January 1', Date(None, 1, 1, fuzzy=True)),
]


class FormatDateTest(TestCase):
    @parameterized.expand(_FORMAT_DATE_TEST_PARAMETERS)
    def test(self, expected: str, datey: Datey):
        locale = 'en'
        with Translations(gettext.NullTranslations()):
            self.assertEquals(expected, format_datey(datey, locale))


_FORMAT_DATE_RANGE_TEST_PARAMETERS = [
    ('from January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31))),
    ('from January 1, 1970 until sometime before December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True)),
    ('from January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True))),
    ('from January 1, 1970 until sometime before around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), end_is_boundary=True)),
    ('from sometime after January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31), start_is_boundary=True)),
    ('sometime between January 1, 1970 and December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31), start_is_boundary=True, end_is_boundary=True)),
    ('from sometime after January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True)),
    ('sometime between January 1, 1970 and around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True, end_is_boundary=True)),
    ('from around January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31))),
    ('from around January 1, 1970 until sometime before December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), end_is_boundary=True)),
    ('from around January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True))),
    ('from around January 1, 1970 until sometime before around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True), end_is_boundary=True)),
    ('from sometime after around January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), start_is_boundary=True)),
    ('sometime between around January 1, 1970 and December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), start_is_boundary=True, end_is_boundary=True)),
    ('from sometime after around January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True)),
    ('sometime between around January 1, 1970 and around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True, end_is_boundary=True)),
    ('from January 1, 1970', DateRange(Date(1970, 1, 1))),
    ('sometime after January 1, 1970', DateRange(Date(1970, 1, 1), start_is_boundary=True)),
    ('from around January 1, 1970', DateRange(Date(1970, 1, 1, fuzzy=True))),
    ('sometime after around January 1, 1970', DateRange(Date(1970, 1, 1, fuzzy=True), start_is_boundary=True)),
    ('until December 31, 1999', DateRange(None, Date(1999, 12, 31))),
    ('sometime before December 31, 1999', DateRange(None, Date(1999, 12, 31), end_is_boundary=True)),
    ('until around December 31, 1999', DateRange(None, Date(1999, 12, 31, fuzzy=True))),
    ('sometime before around December 31, 1999', DateRange(None, Date(1999, 12, 31, fuzzy=True), end_is_boundary=True)),
]


class FormatDateRangeTest(TestCase):
    @parameterized.expand(_FORMAT_DATE_RANGE_TEST_PARAMETERS)
    def test(self, expected: str, datey: Datey):
        locale = 'en'
        with Translations(gettext.NullTranslations()):
            self.assertEquals(expected, format_datey(datey, locale))


class FormatDateyTest(TestCase):
    @parameterized.expand(_FORMAT_DATE_TEST_PARAMETERS + _FORMAT_DATE_RANGE_TEST_PARAMETERS)
    def test(self, expected: str, datey: Datey):
        locale = 'en'
        with Translations(gettext.NullTranslations()):
            self.assertEquals(expected, format_datey(datey, locale))


class OpenTranslationsTest(TestCase):
    def test(self) -> None:
        locale = 'nl-NL'
        locale_path_name = 'nl_NL'
        with TemporaryDirectory() as assets_directory_path:
            lc_messages_directory_path = path.join(assets_directory_path, 'locale', locale_path_name, 'LC_MESSAGES')
            makedirs(lc_messages_directory_path)
            po = """
# Dutch translations for PROJECT.
# Copyright (C) 2019 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2019.
#
msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2020-11-18 23:28+0000\n"
"PO-Revision-Date: 2019-10-05 11:38+0100\n"
"Last-Translator: \n"
"Language: nl\n"
"Language-Team: nl <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.7.0\n"

#: betty/ancestry.py:457
msgid "Subject"
msgstr "Onderwerp"
"""
            with open(path.join(lc_messages_directory_path, 'betty.po'), 'w') as f:
                f.write(po)
            self.assertIsInstance(open_translations(locale, assets_directory_path), gettext.NullTranslations)
