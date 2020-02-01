import datetime
import gettext
import os
from functools import total_ordering
from typing import Optional, Tuple, Iterable, Union

from babel import dates, Locale, parse_locale, negotiate_locale


class Localized:
    def __init__(self, locale: Optional[str] = None):
        self._locale = locale

    @property
    def locale(self) -> Optional[str]:
        return self._locale

    @locale.setter
    def locale(self, locale: Optional[str]) -> None:
        self._locale = locale


@total_ordering
class Date:
    def __init__(self, year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None):
        self._year = year
        self._month = month
        self._day = day
        self._fuzzy = False

    def __repr__(self):
        return '%s.%s(%s, %s, %s)' % (self.__class__.__module__, self.__class__.__name__, self.year, self.month, self.day)

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
    def fuzzy(self) -> bool:
        return self._fuzzy

    @fuzzy.setter
    def fuzzy(self, fuzzy: bool) -> None:
        self._fuzzy = fuzzy

    @property
    def complete(self) -> bool:
        return self.year is not None and self.month is not None and self.day is not None

    @property
    def parts(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        return self.year, self.month, self.day

    def __lt__(self, other):
        if not isinstance(other, Date):
            return NotImplemented
        if None in self.parts or None in other.parts:
            return NotImplemented
        return self.parts < other.parts

    def __eq__(self, other):
        if not isinstance(other, Date):
            return NotImplemented
        return self.parts == other.parts


@total_ordering
class Period:
    def __init__(self, start: Optional[Date] = None, end: Optional[Date] = None):
        self._start = start
        self._end = end

    def __repr__(self):
        return '%s.%s(%s, %s)' % (self.__class__.__module__, self.__class__.__name__, repr(self.start), repr(self.end))

    @property
    def complete(self) -> bool:
        return self.start is not None and self.start.complete or self.end is not None and self.end.complete

    def __lt__(self, other):
        if not self.complete:
            return NotImplemented

        if not (isinstance(other, Date) or isinstance(other, Period)):
            return NotImplemented

        if not other.complete:
            return NotImplemented

        self_has_start = self.start is not None and self.start.complete
        self_has_end = self.end is not None and self.end.complete

        if isinstance(other, Period):
            other_has_start = other.start is not None and other.start.complete
            other_has_end = other.end is not None and other.end.complete

            if self_has_start and other_has_start:
                if self.start == other.start:
                    # If both end dates are missing or incomplete, and therefore incomparable, we consider them equal.
                    if (self.end is None or not self.end.complete) and (other.end is None or other.end.complete):
                        return False
                    if self_has_end and other_has_end:
                        return self.end < other.end
                    return other.end is None
                return self.start < other.start

            if self_has_start:
                return self.start < other.end

            if other_has_start:
                return self.end <= other.start

            return self.end < other.end

        if not self_has_start:
            return self.end < other
        return self.start < other

    def __eq__(self, other):
        if isinstance(other, Date):
            return False

        if not isinstance(other, Period):
            return NotImplemented

        return (self.start, self.end) == (other.start, other.end)

    @property
    def start(self) -> Optional[Date]:
        return self._start

    @property
    def end(self) -> Optional[Date]:
        return self._end


Datey = Union[Date, Period]


class Translations(gettext.NullTranslations):
    _KEYS = ('_', 'gettext', 'ngettext', 'lgettext', 'lngettext')

    def __init__(self, fallback: gettext.NullTranslations):
        gettext.NullTranslations.__init__(self)
        self._fallback = fallback
        self._previous_context = {}

    def __enter__(self):
        import builtins
        self._previous_context = {
            key: value for key, value in builtins.__dict__.items() if key in self._KEYS}
        self.install()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninstall()

    def uninstall(self):
        import builtins
        for key in self._KEYS:
            try:
                del builtins.__dict__[key]
            except KeyError:
                # The function may not have been installed.
                pass
        builtins.__dict__.update(self._previous_context)


def validate_locale(locale: str) -> str:
    parse_locale(locale, '-')
    return locale


def negotiate_localizeds(preferred_locale: str, localizeds: Iterable[Localized]) -> Localized:
    localizeds = list(localizeds)
    negotiated_locale = negotiate_locale([preferred_locale], map(
        lambda localized: localized.locale, localizeds), '-')
    if negotiated_locale is None:
        if len(localizeds) > 0:
            return localizeds[0]
        else:
            raise ValueError(
                'Cannot negotiate if there are no localized values.')
    for localized in localizeds:
        if localized.locale == negotiated_locale:
            return localized


def open_translations(locale: str, directory_path: str) -> Optional[gettext.GNUTranslations]:
    try:
        with open(os.path.join(directory_path, 'locale', locale.replace('-', '_'), 'LC_MESSAGES', 'betty.mo'), 'rb') as f:
            return gettext.GNUTranslations(f)
    except FileNotFoundError:
        return None


class IncompleteDateError(ValueError):
    pass


def format_datey(date: Datey, locale: str, translation: gettext.NullTranslations) -> str:
    try:
        if isinstance(date, Date):
            return _format_date(date, locale, translation)
        return _format_period(date, locale, translation)
    except IncompleteDateError:
        return translation.gettext('unknown date')


def _format_date(date: Date, locale: str, translation: gettext.NullTranslations) -> str:
    formatted = _format_date_parts(date, locale, translation)
    if date.fuzzy:
        formatted = translation.gettext('Around %(date)s') % {
            'date': formatted,
        }
    return formatted


def _format_date_parts(date: Date, locale: str, translation: gettext.NullTranslations) -> str:
    if date is None:
        raise IncompleteDateError('This date is None.')
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
        raise IncompleteDateError('This date does not have enough parts to be rendered.')
    parts = map(lambda x: 1 if x is None else x, date.parts)
    return dates.format_date(datetime.date(*parts), format, Locale.parse(locale, '-'))


def _format_period(period: Period, locale: str, translation: gettext.NullTranslations) -> str:
    try:
        formatted_start = _format_date_parts(period.start, locale, translation)
    except IncompleteDateError:
        formatted_start = None
    try:
        formatted_end = _format_date_parts(period.end, locale, translation)
    except IncompleteDateError:
        formatted_end = None
    if formatted_start is not None and formatted_end is not None:
        return translation.gettext('Between %(start)s and %(end)s') % {
            'start': formatted_start,
            'end': formatted_end,
        }
    if formatted_start is not None:
        return translation.gettext('After %(start)s') % {
            'start': formatted_start,
        }
    if formatted_end is not None:
        return translation.gettext('Before %(end)s') % {
            'end': formatted_end,
        }
    raise IncompleteDateError('This period does not have enough parts to be rendered.')
