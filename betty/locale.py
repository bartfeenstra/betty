import datetime
import gettext
import os
from functools import total_ordering
from typing import Optional, Tuple, Iterable

import babel
from babel import dates


class Locale:
    def __init__(self, language: str, region: Optional[str] = None, script: Optional[str] = None, variant: Optional[str] = None):
        self._language = language
        self._region = region
        self._script = script
        self._variant = variant

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._language == other._language and self._region == other._region and self._script == other._script and self._variant == other._variant

    def __repr__(self):
        return self.get_identifier()

    def __hash__(self):
        return hash(self.get_identifier())

    @property
    def language(self) -> str:
        return self._language

    @property
    def region(self) -> Optional[str]:
        return self._region

    @property
    def script(self) -> Optional[str]:
        return self._script

    @property
    def variant(self) -> Optional[str]:
        return self._variant

    def get_identifier(self, separator: str = '_'):
        return separator.join(filter(None, (self._language, self._region, self._script, self._variant)))

    @property
    def info(self) -> babel.Locale:
        return babel.Locale(self._language, self._region, self._script, self._variant)


class Localized:
    def __init__(self):
        self._locale = None

    @property
    def locale(self) -> Optional[Locale]:
        return self._locale

    @locale.setter
    def locale(self, locale: Optional[Locale]) -> None:
        self._locale = locale


def _score(locale_1: Locale, locale_2: Locale) -> int:
    if locale_1 is None or locale_2 is None:
        return 0
    if locale_1.language != locale_2.language:
        return 0
    if locale_1.region != locale_2.region:
        return 1
    if locale_1.region is None and locale_2.region is None:
        return 1
    if locale_1.script != locale_2.script:
        return 2
    if locale_1.script is None and locale_2.script is None:
        return 2
    if locale_1.variant != locale_2.variant:
        return 3
    if locale_1.variant is None and locale_2.variant is None:
        return 3
    return 4


def sort(localizeds: Iterable[Localized], locale: Locale):
    return sorted(localizeds, key=lambda localized: _score(localized.locale, locale), reverse=True)


def open_translations(locale: Locale, directory_path: str) -> Optional[gettext.GNUTranslations]:
    try:
        with open(os.path.join(directory_path, 'locale', str(locale), 'LC_MESSAGES', 'betty.mo'), 'rb') as f:
            return gettext.GNUTranslations(f)
    except FileNotFoundError:
        return None


@total_ordering
class Date:
    def __init__(self, year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None):
        self._year = year
        self._month = month
        self._day = day

    @property
    def year(self) -> Optional[int]:
        return self._year

    @property
    def month(self) -> Optional[int]:
        return self._month

    @property
    def day(self) -> Optional[int]:
        return self._day

    @property
    def complete(self) -> bool:
        return self._year is not None and self._month is not None and self._day is not None

    @property
    def parts(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        return self._year, self._month, self._day

    def __eq__(self, other):
        if not isinstance(other, Date):
            return NotImplemented
        return self.parts == other.parts

    def __lt__(self, other):
        if not isinstance(other, Date):
            return NotImplemented
        if None in self.parts or None in other.parts:
            return NotImplemented
        return self.parts < other.parts


def format_date(date: Date, locale: Locale, translation: gettext.NullTranslations) -> str:
    DATE_FORMATS = {
        (True, True, True): translation.gettext('MMMM d, y'),
        (True, True, False): translation.gettext('MMMM, y'),
        (True, False, False): translation.gettext('y'),
        (False, True, True): translation.gettext('MMMM d'),
        (False, True, False): translation.gettext('MMMM'),
    }
    try:
        format = DATE_FORMATS[tuple(map(lambda x: x is not None, date.parts))]
    except KeyError:
        return translation.gettext('unknown date')
    parts = map(lambda x: 1 if x is None else x, date.parts)
    return dates.format_date(datetime.date(*parts), format, locale.info)
