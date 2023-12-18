from __future__ import annotations

import calendar
import contextlib
import datetime
import gettext
import glob
import logging
import operator
from contextlib import suppress
from functools import total_ordering, lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, Iterator, Sequence, Mapping, Callable, TypeAlias, cast

import babel
from aiofiles.os import makedirs
from aiofiles.ospath import exists
from babel import dates, Locale
from babel.messages.frontend import CommandLineInterface
from langcodes import Language
from polib import pofile

from betty import fs
from betty.fs import hashfile, FileSystem, ASSETS_DIRECTORY_PATH, ROOT_DIRECTORY_PATH
from betty.os import ChDir
from betty.pickle import Pickleable, State

DEFAULT_LOCALE = 'en-US'

_LOCALE_DIRECTORY_PATH = ASSETS_DIRECTORY_PATH / 'locale'


class LocaleNotFoundError(RuntimeError):
    def __init__(self, locale: str) -> None:
        super().__init__(f'Cannot find locale "{locale}"')
        self.locale = locale


def to_babel_identifier(locale: Localey) -> str:
    if isinstance(locale, Locale):
        return str(locale)
    language_data = Language.get(locale)
    return '_'.join(
        part
        for part
        in [
            language_data.language,
            language_data.script,
            language_data.territory,
        ]
        if part
    )


def to_locale(locale: Localey) -> str:
    if isinstance(locale, str):
        return locale
    return '-'.join(
        part
        for part
        in [
            locale.language,
            locale.script,
            locale.territory,
        ]
        if part
    )


Localey: TypeAlias = str | Locale


def get_data(locale: Localey) -> Locale:
    if isinstance(locale, Locale):
        return locale
    try:
        return Locale.parse(to_babel_identifier(locale))
    except BaseException as e:
        raise LocaleNotFoundError(locale) from e


def get_display_name(locale: Localey, display_locale: Localey | None = None) -> str | None:
    locale_data = get_data(locale)
    return locale_data.get_display_name(
        get_data(display_locale) if display_locale else locale_data
    )


class Localized(Pickleable):
    locale: str | None

    def __init__(
        self,
        *args: Any,
        locale: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.locale = locale

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['locale'] = self.locale
        return dict_state, slots_state


class IncompleteDateError(ValueError):
    pass


@total_ordering
class Date:
    year: int | None
    month: int | None
    day: int | None
    fuzzy: bool

    def __init__(
        self,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        fuzzy: bool = False,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.fuzzy = fuzzy

    def __repr__(self) -> str:
        return '<%s.%s(%s, %s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.year, self.month, self.day)

    @property
    def comparable(self) -> bool:
        return self.year is not None

    @property
    def complete(self) -> bool:
        return self.year is not None and self.month is not None and self.day is not None

    @property
    def parts(self) -> tuple[int | None, int | None, int | None]:
        return self.year, self.month, self.day

    def to_range(self) -> DateRange:
        if not self.comparable:
            raise ValueError('Cannot convert non-comparable date %s to a date range.' % self)
        if self.month is None:
            month_start = 1
            month_end = 12
        else:
            month_start = month_end = self.month
        if self.day is None:
            day_start = 1
            day_end = calendar.monthrange(
                self.year,  # type: ignore[arg-type]
                month_end,
            )[1]
        else:
            day_start = day_end = self.day
        return DateRange(Date(self.year, month_start, day_start), Date(self.year, month_end, day_end))

    def _compare(self, other: Any, comparator: Callable[[Any, Any], bool]) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        selfish = self
        if not selfish.comparable or not other.comparable:
            return NotImplemented
        if selfish.complete and other.complete:
            return comparator(selfish.parts, other.parts)
        if not other.complete:
            other = other.to_range()
        if not selfish.complete:
            selfish = selfish.to_range()  # type: ignore[assignment]
        return comparator(selfish, other)

    def __contains__(self, other: Any) -> bool:
        if isinstance(other, Date):
            return self == other
        if isinstance(other, DateRange):
            return self in other
        raise TypeError('Expected to check a %s, but a %s was given' % (type(Datey), type(other)))

    def __lt__(self, other: Any) -> bool:
        return self._compare(other, operator.lt)

    def __le__(self, other: Any) -> bool:
        return self._compare(other, operator.le)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.parts == other.parts

    def __ge__(self, other: Any) -> bool:
        return self._compare(other, operator.ge)

    def __gt__(self, other: Any) -> bool:
        return self._compare(other, operator.gt)


@total_ordering
class DateRange:
    start: Date | None
    start_is_boundary: bool
    end: Date | None
    end_is_boundary: bool

    def __init__(
        self,
        start: Date | None = None,
        end: Date | None = None,
        start_is_boundary: bool = False,
        end_is_boundary: bool = False,
    ):
        self.start = start
        self.start_is_boundary = start_is_boundary
        self.end = end
        self.end_is_boundary = end_is_boundary

    def __repr__(self) -> str:
        return '%s.%s(%s, %s, start_is_boundary=%s, end_is_boundary=%s)' % (self.__class__.__module__, self.__class__.__name__, repr(self.start), repr(self.end), repr(self.start_is_boundary), repr(self.end_is_boundary))

    @property
    def comparable(self) -> bool:
        return self.start is not None and self.start.comparable or self.end is not None and self.end.comparable

    def __contains__(self, other: Any) -> bool:
        if not self.comparable:
            return False

        if isinstance(other, Date):
            others = [other]
        elif isinstance(other, DateRange):
            if not other.comparable:
                return False
            others = []
            if other.start is not None and other.start.comparable:
                others.append(other.start)
            if other.end is not None and other.end.comparable:
                others.append(other.end)
        else:
            raise TypeError('Expected to check a %s, but a %s was given' % (type(Datey), type(other)))

        if self.start is not None and self.end is not None:
            if isinstance(other, DateRange) and (other.start is None or other.end is None):
                if other.start is None:
                    return self.start <= other.end or self.end <= other.end
                if other.end is None:
                    return self.start >= other.start or self.end >= other.start
            for another in others:
                if self.start <= another <= self.end:
                    return True
            if isinstance(other, DateRange):
                for selfdate in [self.start, self.end]:
                    if other.start <= selfdate <= other.end:
                        return True

        elif self.start is not None:
            # Two date ranges with start dates only always overlap.
            if isinstance(other, DateRange) and other.end is None:
                return True

            for other in others:
                if self.start <= other:
                    return True
        elif self.end is not None:
            # Two date ranges with end dates only always overlap.
            if isinstance(other, DateRange) and other.start is None:
                return True

            for other in others:
                if other <= self.end:
                    return True
        return False

    def _get_comparable_date(self, date: Date | None) -> Date | None:
        if date and date.comparable:
            return date
        return None

    _LT_DATE_RANGE_COMPARATORS = {
        (True, True, True, True): lambda self_start, self_end, other_start, other_end: self_start < other_start,
        (True, True, True, False): lambda self_start, self_end, other_start, other_end: self_start <= other_start,
        (True, True, False, True): lambda self_start, self_end, other_start, other_end: self_start < other_end or self_end <= other_end,
        (True, True, False, False): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (True, False, True, True): lambda self_start, self_end, other_start, other_end: self_start < other_start,
        (True, False, True, False): lambda self_start, self_end, other_start, other_end: self_start < other_start,
        (True, False, False, True): lambda self_start, self_end, other_start, other_end: self_start < other_end,
        (True, False, False, False): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (False, True, True, True): lambda self_start, self_end, other_start, other_end: self_end <= other_start,
        (False, True, True, False): lambda self_start, self_end, other_start, other_end: self_end <= other_start,
        (False, True, False, True): lambda self_start, self_end, other_start, other_end: self_end < other_end,
        (False, True, False, False): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (False, False, True, True): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (False, False, True, False): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (False, False, False, True): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (False, False, False, False): lambda self_start, self_end, other_start, other_end: NotImplemented,
    }

    _LT_DATE_COMPARATORS = {
        (True, True): lambda self_start, self_end, other: self_start < other,
        (True, False): lambda self_start, self_end, other: self_start < other,
        (False, True): lambda self_start, self_end, other: self_end <= other,
        (False, False): lambda self_start, self_end, other: NotImplemented,
    }

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, (Date, DateRange)):
            return NotImplemented

        self_start = self._get_comparable_date(self.start)
        self_end = self._get_comparable_date(self.end)
        signature = (
            self_start is not None,
            self_end is not None,
        )
        if isinstance(other, DateRange):
            other_start = self._get_comparable_date(other.start)
            other_end = self._get_comparable_date(other.end)
            return self._LT_DATE_RANGE_COMPARATORS[(
                *signature,
                other_start is not None,
                other_end is not None,
            )](self_start, self_end, other_start, other_end)
        else:
            return self._LT_DATE_COMPARATORS[signature](self_start, self_end, other)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Date):
            return False

        if not isinstance(other, DateRange):
            return NotImplemented
        return (self.start, self.end, self.start_is_boundary, self.end_is_boundary) == (other.start, other.end, other.start_is_boundary, other.end_is_boundary)


Datey: TypeAlias = Date | DateRange
DatePartsFormatters: TypeAlias = Mapping[tuple[bool, bool, bool], str]
DateFormatters: TypeAlias = Mapping[tuple[bool | None], str]
DateRangeFormatters: TypeAlias = Mapping[tuple[bool | None, bool | None, bool | None, bool | None], str]


class Localizer:
    def __init__(self, locale: str, translations: gettext.NullTranslations):
        self._locale = locale
        self._locale_data = get_data(locale)
        self._translations = translations
        self.__date_parts_formatters: DatePartsFormatters | None = None
        self.__date_formatters: DateFormatters | None = None
        self.__date_range_formatters: DateRangeFormatters | None = None

    @property
    def locale(self) -> str:
        return self._locale

    def _(self, message: str) -> str:
        return self._translations.gettext(message)

    def gettext(self, message: str) -> str:
        return self._translations.gettext(message)

    def ngettext(self, message_singular: str, message_plural: str, n: int) -> str:
        return self._translations.ngettext(message_singular, message_plural, n)

    def pgettext(self, context: str, message: str) -> str:
        return self._translations.pgettext(context, message)

    def npgettext(self, context: str, message_singular: str, message_plural: str, n: int) -> str:
        return self._translations.npgettext(context, message_singular, message_plural, n)

    @property
    def _date_parts_formatters(self) -> DatePartsFormatters:
        if self.__date_parts_formatters is None:
            self.__date_parts_formatters = {
                (True, True, True): self._('MMMM d, y'),
                (True, True, False): self._('MMMM, y'),
                (True, False, False): self._('y'),
                (False, True, True): self._('MMMM d'),
                (False, True, False): self._('MMMM'),
            }
        return self.__date_parts_formatters

    @property
    def _date_formatters(self) -> DateFormatters:
        if self.__date_formatters is None:
            self.__date_formatters = {
                (True,): self._('around {date}'),
                (False,): self._('{date}'),
            }
        return self.__date_formatters

    @property
    def _date_range_formatters(self) -> DateRangeFormatters:
        if self.__date_range_formatters is None:
            self.__date_range_formatters = {
                (False, False, False, False): self._('from {start_date} until {end_date}'),
                (False, False, False, True): self._('from {start_date} until sometime before {end_date}'),
                (False, False, True, False): self._('from {start_date} until around {end_date}'),
                (False, False, True, True): self._('from {start_date} until sometime before around {end_date}'),
                (False, True, False, False): self._('from sometime after {start_date} until {end_date}'),
                (False, True, False, True): self._('sometime between {start_date} and {end_date}'),
                (False, True, True, False): self._('from sometime after {start_date} until around {end_date}'),
                (False, True, True, True): self._('sometime between {start_date} and around {end_date}'),
                (True, False, False, False): self._('from around {start_date} until {end_date}'),
                (True, False, False, True): self._('from around {start_date} until sometime before {end_date}'),
                (True, False, True, False): self._('from around {start_date} until around {end_date}'),
                (True, False, True, True): self._('from around {start_date} until sometime before around {end_date}'),
                (True, True, False, False): self._('from sometime after around {start_date} until {end_date}'),
                (True, True, False, True): self._('sometime between around {start_date} and {end_date}'),
                (True, True, True, False): self._('from sometime after around {start_date} until around {end_date}'),
                (True, True, True, True): self._('sometime between around {start_date} and around {end_date}'),
                (False, False, None, None): self._('from {start_date}'),
                (False, True, None, None): self._('sometime after {start_date}'),
                (True, False, None, None): self._('from around {start_date}'),
                (True, True, None, None): self._('sometime after around {start_date}'),
                (None, None, False, False): self._('until {end_date}'),
                (None, None, False, True): self. _('sometime before {end_date}'),
                (None, None, True, False): self._('until around {end_date}'),
                (None, None, True, True): self._('sometime before around {end_date}'),
            }
        return self.__date_range_formatters

    def format_datey(self, date: Datey) -> str:
        """
        Formats a datey value into a human-readable string.
        """
        if isinstance(date, Date):
            return self.format_date(date)
        return self.format_date_range(date)

    def format_date(self, date: Date) -> str:
        try:
            return self._date_formatters[(date.fuzzy,)].format(
                date=self._format_date_parts(date),
            )
        except IncompleteDateError:
            return self._('unknown date')

    def _format_date_parts(self, date: Date | None) -> str:
        if date is None:
            raise IncompleteDateError('This date is None.')
        try:
            date_parts_format = self._date_parts_formatters[tuple(
                map(lambda x: x is not None, date.parts),  # type: ignore[index]
            )]
        except KeyError:
            raise IncompleteDateError('This date does not have enough parts to be rendered.')
        parts = map(lambda x: 1 if x is None else x, date.parts)
        return dates.format_date(datetime.date(*parts), date_parts_format, self._locale_data)

    def format_date_range(self, date_range: DateRange) -> str:
        formatter_configuration: tuple[bool | None, bool | None, bool | None, bool | None] = (None, None, None, None)
        formatter_arguments = {}

        with suppress(IncompleteDateError):
            formatter_arguments['start_date'] = self._format_date_parts(date_range.start)
            formatter_configuration = (
                None if date_range.start is None else date_range.start.fuzzy,
                date_range.start_is_boundary,
                formatter_configuration[2],
                formatter_configuration[3],
            )

        with suppress(IncompleteDateError):
            formatter_arguments['end_date'] = self._format_date_parts(date_range.end)
            formatter_configuration = (
                formatter_configuration[0],
                formatter_configuration[1],
                None if date_range.end is None else date_range.end.fuzzy,
                date_range.end_is_boundary,
            )

        if not formatter_arguments:
            raise IncompleteDateError('This date range does not have enough parts to be rendered.')

        return self._date_range_formatters[formatter_configuration].format(**formatter_arguments)


DEFAULT_LOCALIZER = Localizer(DEFAULT_LOCALE, gettext.NullTranslations())


class LocalizerRepository:
    def __init__(self, assets: FileSystem):
        self._assets = assets
        self._localizers: dict[str, Localizer] = {}

    @property
    def locales(self) -> Iterator[str]:
        yield DEFAULT_LOCALE
        for assets_directory_path, __ in reversed(self._assets.paths):
            for po_file_path in glob.glob(str(assets_directory_path / 'locale' / '*' / 'betty.po')):
                yield Path(po_file_path).parent.name

    def get(self, locale: Localey) -> Localizer:
        return self[to_locale(locale)]

    @lru_cache
    def get_negotiated(self, *preferred_locales: str) -> Localizer:
        preferred_locales = (*preferred_locales, DEFAULT_LOCALE)
        negotiated_locale = negotiate_locale(
            preferred_locales,
            {
                str(get_data(locale))
                for locale
                in self.locales
            },
        )
        return self[negotiated_locale or DEFAULT_LOCALE]

    def __getitem__(self, locale: Localey) -> Localizer:
        locale = to_locale(locale)
        try:
            return self._localizers[locale]
        except KeyError:
            return self._build_translation(locale)

    def _build_translation(self, locale: str) -> Localizer:
        translations = gettext.NullTranslations()
        for assets_directory_path, __ in reversed(self._assets.paths):
            opened_translations = self._open_translations(locale, assets_directory_path)
            if opened_translations:
                opened_translations.add_fallback(translations)
                translations = opened_translations
        self._localizers[locale] = Localizer(locale, translations)
        return self._localizers[locale]

    def _open_translations(self, locale: str, assets_directory_path: Path) -> gettext.GNUTranslations | None:
        po_file_path = assets_directory_path / 'locale' / locale / 'betty.po'
        try:
            translation_version = hashfile(po_file_path)
        except FileNotFoundError:
            return None
        cache_directory_path = fs.CACHE_DIRECTORY_PATH / 'locale' / translation_version
        mo_file_path = cache_directory_path / 'betty.mo'

        with suppress(FileNotFoundError):
            with open(mo_file_path, 'rb') as f:
                return gettext.GNUTranslations(f)

        cache_directory_path.mkdir(exist_ok=True, parents=True)

        with contextlib.redirect_stdout(StringIO()):
            CommandLineInterface().run([
                '',
                'compile',
                '-i',
                str(po_file_path),
                '-o',
                str(mo_file_path),
                '-l',
                str(get_data(locale)),
                '-D',
                'betty',
            ])
        with open(mo_file_path, 'rb') as f:
            return gettext.GNUTranslations(f)

    def coverage(self, locale: Localey) -> tuple[int, int]:
        translatables = set(self._get_translatables())
        locale = to_locale(locale)
        if locale == DEFAULT_LOCALE:
            return len(translatables), len(translatables)
        translations = set(self._get_translations(locale))
        return len(translations), len(translatables)

    def _get_translatables(self) -> Iterator[str]:
        for assets_directory_path, __ in self._assets.paths:
            with suppress(FileNotFoundError):
                with open(assets_directory_path / 'betty.pot') as f:
                    for entry in pofile(f.read()):
                        yield entry.msgid_with_context

    def _get_translations(self, locale: str) -> Iterator[str]:
        for assets_directory_path, __ in reversed(self._assets.paths):
            with suppress(FileNotFoundError):
                with open(assets_directory_path / 'locale' / locale / 'betty.po') as f:
                    for entry in pofile(f.read()):
                        if entry.translated():
                            yield entry.msgid_with_context


class Localizable:
    def localize(self, localizer: Localizer) -> str:
        raise NotImplementedError


class Str(Localizable):
    def _localize_format_kwargs(self, localizer: Localizer, **format_kwargs: str | Localizable) -> dict[str, str]:
        return {
            key: value.localize(localizer) if isinstance(value, Localizable) else value
            for key, value
            in format_kwargs.items()
        }

    @classmethod
    def plain(cls, plain: Any, **format_kwargs: str | Localizable) -> Str:
        return _PlainStr(str(plain), **format_kwargs)

    @classmethod
    def call(cls, call: Callable[[Localizer], str]) -> Str:
        return _CallStr(call)

    @classmethod
    def _(cls, message: str, **format_kwargs: str | Localizable) -> Str:
        return cls.gettext(message, **format_kwargs)

    @classmethod
    def gettext(cls, message: str, **format_kwargs: str | Localizable) -> Str:
        return _GettextStr('gettext', message, **format_kwargs)

    @classmethod
    def ngettext(cls, message_singular: str, message_plural: str, n: int, **format_kwargs: str | Localizable) -> Str:
        return _GettextStr('ngettext', message_singular, message_plural, n, **format_kwargs)

    @classmethod
    def pgettext(cls, context: str, message: str, **format_kwargs: str | Localizable) -> Str:
        return _GettextStr('pgettext', context, message, **format_kwargs)

    @classmethod
    def npgettext(cls, context: str, message_singular: str, message_plural: str, n: int, **format_kwargs: str | Localizable) -> Str:
        return _GettextStr('npgettext', context, message_singular, message_plural, n, **format_kwargs)


class _PlainStr(Str):
    def __init__(self, plain: str, **format_kwargs: str | Localizable):
        self._plain = plain
        self._format_kwargs = format_kwargs

    def localize(self, localizer: Localizer) -> str:
        return self._plain.format(**self._localize_format_kwargs(localizer, **self._format_kwargs))


class _CallStr(Str):
    def __init__(self, call: Callable[[Localizer], str]):
        self._call = call

    def localize(self, localizer: Localizer) -> str:
        return self._call(localizer)


class _GettextStr(Str):
    def __init__(self, gettext_method_name: str, *gettext_args: Any, **format_kwargs: str | Localizable) -> None:
        self._gettext_method_name = gettext_method_name
        self._gettext_args = gettext_args
        self._format_kwargs = format_kwargs

    def localize(self, localizer: Localizer) -> str:
        return cast(str, getattr(localizer, self._gettext_method_name)(*self._gettext_args)).format(**self._localize_format_kwargs(localizer, **self._format_kwargs))


def negotiate_locale(preferred_locales: Localey | Sequence[Localey], available_locales: set[Localey]) -> Locale | None:
    if isinstance(preferred_locales, (str, Locale)):
        preferred_locales = [preferred_locales]
    return _negotiate_locale(
        [
            to_babel_identifier(locale)
            for locale
            in preferred_locales
        ],
        {
            to_babel_identifier(locale)
            for locale
            in available_locales
        },
        False,
    )


def _negotiate_locale(preferred_locale_babel_identifiers: Sequence[str], available_locale_babel_identifiers: set[str], root: bool) -> Locale | None:
    negotiated_locale = babel.negotiate_locale(preferred_locale_babel_identifiers, available_locale_babel_identifiers)
    if negotiated_locale is not None:
        return Locale.parse(negotiated_locale)
    if not root:
        return _negotiate_locale(
            [
                babel_identifier.split('_')[0] if '_' in babel_identifier else babel_identifier
                for babel_identifier
                in preferred_locale_babel_identifiers
            ],
            available_locale_babel_identifiers,
            True,
        )
    return None


def negotiate_localizeds(preferred_locales: Localey | Sequence[Localey], localizeds: Sequence[Localized]) -> Localized | None:
    negotiated_locale_data = negotiate_locale(
        preferred_locales,
        {
            localized.locale
            for localized
            in localizeds
            if localized.locale is not None
        },
    )
    if negotiated_locale_data is not None:
        negotiated_locale = to_locale(negotiated_locale_data)
        for localized in localizeds:
            if localized.locale == negotiated_locale:
                return localized
    for localized in localizeds:
        if localized.locale is None:
            return localized
    with suppress(IndexError):
        return localizeds[0]
    return None


async def init_translation(locale: str) -> None:
    po_file_path = _LOCALE_DIRECTORY_PATH / locale / 'betty.po'
    with contextlib.redirect_stdout(StringIO()):
        if await exists(po_file_path):
            logging.getLogger().info(f'Translations for {locale} already exist at {po_file_path}.')
            return

        locale_data = get_data(locale)
        CommandLineInterface().run([
            '',
            'init',
            '--no-wrap',
            '-i',
            str(ASSETS_DIRECTORY_PATH / 'betty.pot'),
            '-o',
            str(po_file_path),
            '-l',
            str(locale_data),
            '-D',
            'betty',
        ])
        logging.getLogger().info(f'Translations for {locale} initialized at {po_file_path}.')


async def update_translations(_output_assets_directory_path: Path = ASSETS_DIRECTORY_PATH) -> None:
    source_paths = glob.glob('betty/*')
    # Remove the tests directory from the extraction,
    # or we'll be seeing some unusual additions to the translations.
    source_paths.remove(str(Path('betty') / 'tests'))
    pot_file_path = _output_assets_directory_path / 'betty.pot'
    with contextlib.redirect_stdout(StringIO()):
        async with ChDir(ROOT_DIRECTORY_PATH):
            CommandLineInterface().run([
                '',
                'extract',
                '--no-location',
                '--no-wrap',
                '--sort-output',
                '-F',
                'babel.ini',
                '-o',
                str(pot_file_path),
                '--project',
                'Betty',
                '--copyright-holder',
                'Bart Feenstra & contributors',
                *source_paths,
            ])
            for po_file_path_str in glob.glob('betty/assets/locale/*/betty.po'):
                po_file_path = (_output_assets_directory_path / (ROOT_DIRECTORY_PATH / po_file_path_str).relative_to(ASSETS_DIRECTORY_PATH)).resolve()
                await makedirs(po_file_path.parent, exist_ok=True)
                po_file_path.touch()
                locale = po_file_path.parent.name
                locale_data = get_data(locale)
                CommandLineInterface().run([
                    '',
                    'update',
                    '-i',
                    str(pot_file_path),
                    '-o',
                    str(po_file_path),
                    '-l',
                    str(locale_data),
                    '-D',
                    'betty',
                ])
