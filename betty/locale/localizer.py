"""
Localizers provide a wide range of localization utilities through a single entry point.
"""

from __future__ import annotations

import datetime
import gettext
from collections import defaultdict
from contextlib import suppress
from typing import TYPE_CHECKING, final

import aiofiles
from babel import dates
from babel.dates import format_date
from polib import pofile

from betty import fs
from betty.concurrent import AsynchronizedLock, Lock
from betty.date import (
    Date,
    DateFormatters,
    DatePartsFormatters,
    DateRange,
    DateRangeFormatters,
    Datey,
    IncompleteDateError,
)
from betty.hashid import hashid_file_meta
from betty.locale import (
    DEFAULT_LOCALE,
    Localey,
    get_data,
    negotiate_locale,
    to_babel_identifier,
    to_locale,
)
from betty.locale.babel import run_babel
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, Mapping, MutableMapping
    from pathlib import Path

    from betty.assets import AssetRepository


class Localizer:
    """
    Provide localization functionality for a specific locale.
    """

    def __init__(self, locale: str, translations: gettext.NullTranslations):
        self._locale = locale
        self._locale_data = get_data(locale)
        self._translations = translations
        self.__date_parts_formatters: DatePartsFormatters | None = None
        self.__date_formatters: DateFormatters | None = None
        self.__date_range_formatters: DateRangeFormatters | None = None

    @property
    def locale(self) -> str:
        """
        The locale.
        """
        return self._locale

    def _(self, message: str) -> str:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return self._translations.gettext(message)

    def gettext(self, message: str) -> str:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return self._translations.gettext(message)

    def ngettext(self, message_singular: str, message_plural: str, n: int) -> str:
        """
        Like :py:meth:`gettext.ngettext`.

        Arguments are identical to those of :py:meth:`gettext.ngettext`.
        """
        return self._translations.ngettext(message_singular, message_plural, n)

    def pgettext(self, context: str, message: str) -> str:
        """
        Like :py:meth:`gettext.pgettext`.

        Arguments are identical to those of :py:meth:`gettext.pgettext`.
        """
        return self._translations.pgettext(context, message)

    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int
    ) -> str:
        """
        Like :py:meth:`gettext.npgettext`.

        Arguments are identical to those of :py:meth:`gettext.npgettext`.
        """
        return self._translations.npgettext(
            context, message_singular, message_plural, n
        )

    @property
    def _date_parts_formatters(self) -> DatePartsFormatters:
        if self.__date_parts_formatters is None:
            self.__date_parts_formatters = {
                (True, True, True): self._("MMMM d, y"),
                (True, True, False): self._("MMMM, y"),
                (True, False, False): self._("y"),
                (False, True, True): self._("MMMM d"),
                (False, True, False): self._("MMMM"),
            }
        return self.__date_parts_formatters

    @property
    def _date_formatters(self) -> DateFormatters:
        if self.__date_formatters is None:
            self.__date_formatters = {
                (True,): self._("around {date}"),
                (False,): self._("{date}"),
            }
        return self.__date_formatters

    @property
    def _date_range_formatters(self) -> DateRangeFormatters:
        if self.__date_range_formatters is None:
            self.__date_range_formatters = {
                (False, False, False, False): self._(
                    "from {start_date} until {end_date}"
                ),
                (False, False, False, True): self._(
                    "from {start_date} until sometime before {end_date}"
                ),
                (False, False, True, False): self._(
                    "from {start_date} until around {end_date}"
                ),
                (False, False, True, True): self._(
                    "from {start_date} until sometime before around {end_date}"
                ),
                (False, True, False, False): self._(
                    "from sometime after {start_date} until {end_date}"
                ),
                (False, True, False, True): self._(
                    "sometime between {start_date} and {end_date}"
                ),
                (False, True, True, False): self._(
                    "from sometime after {start_date} until around {end_date}"
                ),
                (False, True, True, True): self._(
                    "sometime between {start_date} and around {end_date}"
                ),
                (True, False, False, False): self._(
                    "from around {start_date} until {end_date}"
                ),
                (True, False, False, True): self._(
                    "from around {start_date} until sometime before {end_date}"
                ),
                (True, False, True, False): self._(
                    "from around {start_date} until around {end_date}"
                ),
                (True, False, True, True): self._(
                    "from around {start_date} until sometime before around {end_date}"
                ),
                (True, True, False, False): self._(
                    "from sometime after around {start_date} until {end_date}"
                ),
                (True, True, False, True): self._(
                    "sometime between around {start_date} and {end_date}"
                ),
                (True, True, True, False): self._(
                    "from sometime after around {start_date} until around {end_date}"
                ),
                (True, True, True, True): self._(
                    "sometime between around {start_date} and around {end_date}"
                ),
                (False, False, None, None): self._("from {start_date}"),
                (False, True, None, None): self._("sometime after {start_date}"),
                (True, False, None, None): self._("from around {start_date}"),
                (True, True, None, None): self._("sometime after around {start_date}"),
                (None, None, False, False): self._("until {end_date}"),
                (None, None, False, True): self._("sometime before {end_date}"),
                (None, None, True, False): self._("until around {end_date}"),
                (None, None, True, True): self._("sometime before around {end_date}"),
            }
        return self.__date_range_formatters

    def format_datey(self, date: Datey) -> str:
        """
        Format a datey value into a human-readable string.
        """
        if isinstance(date, Date):
            return self.format_date(date)
        return self.format_date_range(date)

    def format_date(self, date: Date) -> str:
        """
        Format a date to a human-readable string.
        """
        try:
            return self._date_formatters[(date.fuzzy,)].format(
                date=self._format_date_parts(date),
            )
        except IncompleteDateError:
            return self._("unknown date")

    def _format_date_parts(self, date: Date | None) -> str:
        if date is None:
            raise IncompleteDateError("This date is None.")
        try:
            date_parts_format = self._date_parts_formatters[
                tuple(
                    (x is not None for x in date.parts),  # type: ignore[index]
                )
            ]
        except KeyError:
            raise IncompleteDateError(
                "This date does not have enough parts to be rendered."
            ) from None
        parts = (1 if x is None else x for x in date.parts)
        return dates.format_date(
            datetime.date(*parts), date_parts_format, self._locale_data
        )

    def format_date_range(self, date_range: DateRange) -> str:
        """
        Format a date range to a human-readable string.
        """
        formatter_configuration: tuple[
            bool | None, bool | None, bool | None, bool | None
        ] = (None, None, None, None)
        formatter_arguments = {}

        with suppress(IncompleteDateError):
            formatter_arguments["start_date"] = self._format_date_parts(
                date_range.start
            )
            formatter_configuration = (
                None if date_range.start is None else date_range.start.fuzzy,
                date_range.start_is_boundary,
                formatter_configuration[2],
                formatter_configuration[3],
            )

        with suppress(IncompleteDateError):
            formatter_arguments["end_date"] = self._format_date_parts(date_range.end)
            formatter_configuration = (
                formatter_configuration[0],
                formatter_configuration[1],
                None if date_range.end is None else date_range.end.fuzzy,
                date_range.end_is_boundary,
            )

        if not formatter_arguments:
            raise IncompleteDateError(
                "This date range does not have enough parts to be rendered."
            )

        return self._date_range_formatters[formatter_configuration].format(
            **formatter_arguments
        )

    def format_datetime_datetime(self, datetime_datetime: datetime.datetime) -> str:
        """
        Format a datetime date to a human-readable string.
        """
        return format_date(
            datetime_datetime, "long", locale=to_babel_identifier(self.locale)
        )


DEFAULT_LOCALIZER = Localizer(DEFAULT_LOCALE, gettext.NullTranslations())


@final
@threadsafe
class LocalizerRepository:
    """
    Exposes the available localizers.
    """

    def __init__(self, assets: AssetRepository):
        self._assets = assets
        self._localizers: MutableMapping[str, Localizer] = {}
        self._locks: Mapping[str, Lock] = defaultdict(AsynchronizedLock.threading)
        self._locales: set[str] | None = None

    @property
    def locales(self) -> Iterator[str]:
        """
        The available locales.
        """
        if self._locales is None:
            self._locales = set()
            self._locales.add(DEFAULT_LOCALE)
            for assets_directory_path in reversed(self._assets.assets_directory_paths):
                for po_file_path in assets_directory_path.glob("locale/*/betty.po"):
                    self._locales.add(po_file_path.parent.name)
        yield from self._locales

    async def get(self, locale: Localey) -> Localizer:
        """
        Get the localizer for the given locale.
        """
        locale = to_locale(locale)
        async with self._locks[locale]:
            try:
                return self._localizers[locale]
            except KeyError:
                return await self._build_translation(locale)

    async def get_negotiated(self, *preferred_locales: str) -> Localizer:
        """
        Get the best matching available locale for the given preferred locales.
        """
        preferred_locales = (*preferred_locales, DEFAULT_LOCALE)
        negotiated_locale = negotiate_locale(preferred_locales, list(self.locales))
        return await self.get(negotiated_locale or DEFAULT_LOCALE)

    async def _build_translation(self, locale: str) -> Localizer:
        translations = gettext.NullTranslations()
        for assets_directory_path in reversed(self._assets.assets_directory_paths):
            opened_translations = await self._open_translations(
                locale, assets_directory_path
            )
            if opened_translations:
                opened_translations.add_fallback(translations)
                translations = opened_translations
        self._localizers[locale] = Localizer(locale, translations)
        return self._localizers[locale]

    async def _open_translations(
        self, locale: str, assets_directory_path: Path
    ) -> gettext.GNUTranslations | None:
        po_file_path = assets_directory_path / "locale" / locale / "betty.po"
        try:
            translation_version = await hashid_file_meta(po_file_path)
        except FileNotFoundError:
            return None
        cache_directory_path = (
            fs.HOME_DIRECTORY_PATH / "cache" / "locale" / translation_version
        )
        mo_file_path = cache_directory_path / "betty.mo"

        with suppress(FileNotFoundError), open(mo_file_path, "rb") as f:
            return gettext.GNUTranslations(f)

        cache_directory_path.mkdir(exist_ok=True, parents=True)

        await run_babel(
            "",
            "compile",
            "-i",
            str(po_file_path),
            "-o",
            str(mo_file_path),
            "-l",
            str(get_data(locale)),
            "-D",
            "betty",
        )
        with open(mo_file_path, "rb") as f:
            return gettext.GNUTranslations(f)

    async def coverage(self, locale: Localey) -> tuple[int, int]:
        """
        Get the translation coverage for the given locale.

        :return: A 2-tuple of the number of available translations and the
            number of translatable source strings.
        """
        translatables = {
            translatable async for translatable in self._get_translatables()
        }
        locale = to_locale(locale)
        if locale == DEFAULT_LOCALE:
            return len(translatables), len(translatables)
        translations = {
            translation async for translation in self._get_translations(locale)
        }
        return len(translations), len(translatables)

    async def _get_translatables(self) -> AsyncIterator[str]:
        for assets_directory_path in self._assets.assets_directory_paths:
            with suppress(FileNotFoundError):
                async with aiofiles.open(
                    assets_directory_path / "locale" / "betty.pot"
                ) as pot_data_f:
                    pot_data = await pot_data_f.read()
                    for entry in pofile(pot_data):
                        yield entry.msgid_with_context

    async def _get_translations(self, locale: str) -> AsyncIterator[str]:
        for assets_directory_path in reversed(self._assets.assets_directory_paths):
            with suppress(FileNotFoundError):
                async with aiofiles.open(
                    assets_directory_path / "locale" / locale / "betty.po",
                    encoding="utf-8",
                ) as po_data_f:
                    po_data = await po_data_f.read()
                for entry in pofile(po_data):
                    if entry.translated():
                        yield entry.msgid_with_context
