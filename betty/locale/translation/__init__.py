"""
Manage translations of built-in translatable strings.
"""

from __future__ import annotations

import gettext
from abc import ABC, abstractmethod
from contextlib import redirect_stdout, suppress
from io import BytesIO, StringIO
from pathlib import Path
from typing import TYPE_CHECKING, final

import aiofiles
from aiofiles.os import makedirs
from aiofiles.ospath import exists
from polib import pofile
from typing_extensions import override

import betty
import betty.dirs
from betty.hashid import hashid_file_meta
from betty.locale import DEFAULT_LOCALE, LocaleLike, get_data, to_locale
from betty.locale.babel import run_babel
from betty.locale.error import UnknownLocale
from betty.locale.localizable import _
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Mapping, MutableMapping

    from betty.asset import AssetRepository
    from betty.cache.file import BinaryFileCache
    from betty.user import User


async def _new_translation(
    locale: str, assets_directory_path: Path, *, user: User
) -> None:
    po_file_path = assets_directory_path / "locale" / locale / "betty.po"
    with redirect_stdout(StringIO()):
        if await exists(po_file_path):
            await user.message_information(
                _("Translations for {locale} already exist at {po_file_path}.").format(
                    locale=locale, po_file_path=str(po_file_path)
                )
            )
            return

        locale_data = get_data(locale)
        await run_babel(
            "",
            "init",
            "--no-wrap",
            "-i",
            str(assets_directory_path / "locale" / "betty.pot"),
            "-o",
            str(po_file_path),
            "-l",
            str(locale_data),
            "-D",
            "betty",
        )
        await user.message_information(
            _("Translations for {locale} initialized at {po_file_path}.").format(
                locale=locale, po_file_path=str(po_file_path)
            )
        )


async def update_dev_translations(
    *,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update the translations for Betty itself.
    """
    source_directory_path = betty.dirs.ROOT_DIRECTORY_PATH / "betty"
    test_directory_path = source_directory_path / "tests"
    await _update_translations(
        set(find_source_files(source_directory_path, test_directory_path)),
        betty.dirs.ASSETS_DIRECTORY_PATH,
        _output_assets_directory_path_override,
    )


async def _update_translations(
    source_file_paths: set[Path],
    assets_directory_path: Path,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update all existing translations based on changes in translatable strings.
    """
    # During production, the input and output paths are identical. During testing,
    # _output_assets_directory_path provides an alternative output, so the changes
    # to the translations can be tested in isolation.
    output_assets_directory_path = (
        _output_assets_directory_path_override or assets_directory_path
    )

    pot_file_path = output_assets_directory_path / "locale" / "betty.pot"
    await makedirs(pot_file_path.parent, exist_ok=True)

    await run_babel(
        "",
        "extract",
        "--no-location",
        "--width",
        # Weblate uses 77 characters.
        "77",
        "--sort-output",
        "-F",
        "babel.ini",
        "-o",
        str(pot_file_path),
        "--project",
        "Betty",
        "--copyright-holder",
        "Bart Feenstra & contributors",
        *map(str, {*source_file_paths, *find_source_files(assets_directory_path)}),
    )
    for input_po_file_path in Path(assets_directory_path).glob("locale/*/betty.po"):
        output_po_file_path = (
            output_assets_directory_path
            / input_po_file_path.relative_to(assets_directory_path)
        ).resolve()
        await makedirs(output_po_file_path.parent, exist_ok=True)
        output_po_file_path.touch()

        locale = output_po_file_path.parent.name
        locale_data = get_data(locale)
        await run_babel(
            "",
            "update",
            "--domain",
            "betty",
            "--input-file",
            str(pot_file_path),
            "--ignore-obsolete",
            "--locale",
            str(locale_data),
            "--no-fuzzy-matching",
            "--output-file",
            str(output_po_file_path),
        )


def find_source_files(
    source_directory_path: Path, *exclude_directory_paths: Path
) -> Iterable[Path]:
    """
    Find source files in a directory.
    """
    exclude_directory_paths = {
        exclude_directory_path.expanduser().resolve()
        for exclude_directory_path in exclude_directory_paths
    }
    for source_file_path in source_directory_path.expanduser().resolve().rglob("*"):
        source_file_path = source_directory_path / source_file_path
        if exclude_directory_paths & set(source_file_path.parents):
            continue
        if source_file_path.suffix in {".j2", ".py"}:
            yield source_file_path


class TranslationRepository(ABC):
    """
    Provide translations.
    """

    @property
    @abstractmethod
    def locales(self) -> Iterable[str]:
        """
        The available locales.
        """

    @abstractmethod
    def get(self, locale: LocaleLike) -> gettext.NullTranslations:
        """
        Get the translations for the given locale.
        """


@final
class NoOpTranslationRepository(TranslationRepository):
    """
    Provide no translations.
    """

    def __init__(self):
        self._translations = gettext.NullTranslations()

    @override
    @property
    def locales(self) -> Iterable[str]:
        return ()

    @override
    def get(self, locale: LocaleLike) -> gettext.NullTranslations:
        return self._translations


@final
class StaticTranslationRepository(TranslationRepository):
    """
    Provide static translations.
    """

    def __init__(self, translations: Mapping[str, gettext.NullTranslations]):
        self._translations = translations

    @override
    @property
    def locales(self) -> Iterable[str]:
        return self._translations.keys()

    @override
    def get(self, locale: LocaleLike) -> gettext.NullTranslations:
        locale = to_locale(locale)
        try:
            return self._translations[locale]
        except KeyError:
            raise UnknownLocale(locale) from None


@final
class ProxyTranslationRepository(TranslationRepository):
    """
    Provide translations from upstream repositories.
    """

    def __init__(self, *upstreams: TranslationRepository):
        self._upstreams = upstreams
        self._translations: MutableMapping[str, gettext.NullTranslations] = {}

    @override
    @property
    def locales(self) -> Iterable[str]:
        for upstream in self._upstreams:
            yield from upstream.locales

    @override
    def get(self, locale: LocaleLike) -> gettext.NullTranslations:
        locale = to_locale(locale)
        try:
            return self._translations[locale]
        except KeyError:
            translations: gettext.NullTranslations | None = None
            for upstream in self._upstreams:
                try:
                    upstream_translations = upstream.get(locale)
                except UnknownLocale:
                    pass
                else:
                    if translations is None:
                        translations = upstream_translations
                    else:
                        translations.add_fallback(upstream_translations)
            if translations is None:
                raise UnknownLocale(locale) from None
            self._translations[locale] = translations
            return translations


@final
@threadsafe
class AssetTranslationRepository(TranslationRepository):
    """
    Provide translations from assets.
    """

    def __init__(self, assets: AssetRepository, cache: BinaryFileCache):
        self._assets = assets
        self._cache = cache
        self._translations: MutableMapping[str, gettext.NullTranslations] = {}
        self._locales: set[str] = {DEFAULT_LOCALE}
        self._bootstrapped = False

    async def bootstrap(self) -> None:
        """
        Bootstrap the available translations.
        """
        assert not self._bootstrapped
        for assets_directory_path in reversed(self._assets.assets_directory_paths):
            for po_file_path in assets_directory_path.glob("locale/*/betty.po"):
                locale = po_file_path.parent.name
                self._locales.add(locale)
        for locale in self._locales:
            await self._build_translation(locale)
        self._bootstrapped = True

    @override
    @property
    def locales(self) -> Iterable[str]:
        assert self._bootstrapped
        return self._locales

    @override
    def get(self, locale: LocaleLike) -> gettext.NullTranslations:
        locale = to_locale(locale)
        try:
            return self._translations[locale]
        except KeyError:
            self._translations[locale] = gettext.NullTranslations()
            return self._translations[locale]

    async def _build_translation(self, locale: str) -> gettext.NullTranslations:
        translations = gettext.NullTranslations()
        for assets_directory_path in reversed(self._assets.assets_directory_paths):
            opened_translations = await self._open_translations(
                locale, assets_directory_path
            )
            if opened_translations:
                opened_translations.add_fallback(translations)
                translations = opened_translations
        self._translations[locale] = translations
        return self._translations[locale]

    async def _open_translations(
        self, locale: str, assets_directory_path: Path
    ) -> gettext.GNUTranslations | None:
        po_file_path = assets_directory_path / "locale" / locale / "betty.po"
        try:
            translation_version = await hashid_file_meta(po_file_path)
        except FileNotFoundError:
            return None
        cache_directory_path = self._cache.path / "locale" / translation_version
        mo_file_path = cache_directory_path / "betty.mo"

        with suppress(FileNotFoundError):
            async with aiofiles.open(mo_file_path, "rb") as f:
                return gettext.GNUTranslations(BytesIO(await f.read()))

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
        async with aiofiles.open(mo_file_path, "rb") as f:
            return gettext.GNUTranslations(BytesIO(await f.read()))

    async def coverage(self, locale: LocaleLike) -> tuple[int, int]:
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
