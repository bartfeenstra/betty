"""
Manage translations of built-in translatable strings.
"""

from __future__ import annotations

import gettext
from abc import ABC, abstractmethod
from asyncio import to_thread
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, final, override

from polib import pofile

import betty.dirs
from betty.file import read
from betty.hashid import hashid_file_meta
from betty.life_cycle import Bootstrappable
from betty.locale import (
    DEFAULT_LOCALE,
    ResolvableLocale,
    from_language_tag,
    resolve_locale,
    to_language_tag,
)
from betty.locale.babel import run_babel
from betty.locale.error import LocaleError
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.app import APP
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Iterable,
        Mapping,
        MutableMapping,
    )
    from pathlib import Path

    from babel import Locale

    from betty.asset import AssetDirectoryDefinition, AssetRepository
    from betty.cache.file import BinaryFileCache
    from betty.user import User


async def _new_translation(
    output: AssetDirectoryDefinition, locale: Locale, *, user: User
) -> None:
    po_file_path = output.assets / "locale" / to_language_tag(locale) / "betty.po"
    with redirect_stdout(StringIO()):
        if po_file_path.exists():
            await user.message_information(
                _("Translations for {locale} already exist at {po_file_path}.").format(
                    locale=to_language_tag(locale), po_file_path=str(po_file_path)
                )
            )
            return

        await run_babel(
            "",
            "init",
            "--no-wrap",
            "-i",
            str(output.assets / "locale" / "betty.pot"),
            "-o",
            str(po_file_path),
            "-l",
            str(locale),
            "-D",
            "betty",
        )
        await user.message_information(
            _("Translations for {locale} initialized at {po_file_path}.").format(
                locale=to_language_tag(locale), po_file_path=str(po_file_path)
            )
        )


async def update_app_translations(override_output: Path | None = None, /) -> None:
    """
    Update the translations for Betty itself.
    """
    source_directory_path = betty.dirs.ROOT_DIRECTORY / "betty"
    test_directory_path = source_directory_path / "tests"
    await _update_translations(
        APP.assets if override_output is None else override_output,
        _find_source_files(
            {source_directory_path, betty.dirs.ASSETS_DIRECTORY_PATH},
            {test_directory_path},
        ),
    )


async def _update_translations(output: Path, inputs: Iterable[Path]) -> None:
    """
    Update all existing translations based on changes in translatable strings.
    """
    pot_file_path = output / "locale" / "betty.pot"
    await to_thread(pot_file_path.parent.mkdir, exist_ok=True, parents=True)

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
        *map(str, inputs),
    )
    for output_po_file_path in output.glob("locale/*/betty.po"):
        locale = resolve_locale(output_po_file_path.parent.name)
        await run_babel(
            "",
            "update",
            "--domain",
            "betty",
            "--input-file",
            str(pot_file_path),
            "--ignore-obsolete",
            "--locale",
            str(locale),
            "--no-fuzzy-matching",
            "--output-file",
            str(output_po_file_path),
        )


async def new_translation(
    output: AssetDirectoryDefinition, locale: Locale, *, user: User
) -> None:
    """
    Create a new translation.
    """
    await _new_translation(output, locale, user=user)


async def update_translations(
    output: Path, inputs: Iterable[Path], excludes: Iterable[Path], user: User
) -> None:
    """
    Update translations.
    """
    await _update_translations(output, _find_source_files(inputs, excludes))


def _find_source_files(
    inputs: Iterable[Path], excludes: Iterable[Path], /
) -> Iterable[Path]:
    """
    Find source files in a directory.
    """
    excludes = {exclude.expanduser().resolve() for exclude in excludes}
    for input_path in inputs:
        for relative_input_file_path in input_path.expanduser().resolve().rglob("*"):
            input_file_path = input_path / relative_input_file_path
            if excludes & set(input_file_path.parents):
                continue
            if input_file_path.suffix in {".j2", ".py"}:
                yield input_file_path


class TranslationRepository(ABC):
    """
    Provide translations.
    """

    @property
    @abstractmethod
    def locales(self) -> Iterable[Locale]:
        """
        The available locales.
        """

    @abstractmethod
    def get(self, locale: ResolvableLocale) -> gettext.NullTranslations:
        """
        Get the translations for the given locale.
        """


@final
class StaticTranslationRepository(TranslationRepository):
    """
    Provide static translations.
    """

    def __init__(self, translations: Mapping[Locale, gettext.NullTranslations]):
        self._translations = translations

    @override
    @property
    def locales(self) -> Iterable[Locale]:
        return self._translations.keys()

    @override
    def get(self, locale: ResolvableLocale) -> gettext.NullTranslations:
        locale = resolve_locale(locale)
        try:
            return self._translations[locale]
        except KeyError:
            raise UntranslatedLocale(locale) from None


DEFAULT_TRANSLATION_REPOSITORY = StaticTranslationRepository({
    DEFAULT_LOCALE: gettext.NullTranslations()
})
"""
The translation repository for the default locale.
"""


@final
@threadsafe
class AssetTranslationRepository(TranslationRepository, Bootstrappable):
    """
    Provide translations from assets.
    """

    def __init__(self, assets: AssetRepository, cache: BinaryFileCache):
        super().__init__()
        self._assets = assets
        self._cache = cache
        self._translations: MutableMapping[Locale, gettext.NullTranslations] = {}
        self._locales: set[Locale] = {DEFAULT_LOCALE}
        self._bootstrapped = False

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        for assets_directory_path in reversed(self._assets.directories):
            for po_file_path in assets_directory_path.glob("locale/*/betty.po"):
                self._locales.add(from_language_tag(po_file_path.parent.name))
        for locale in self._locales:
            await self._build_translation(locale)
        self._bootstrapped = True

    @override
    @property
    def locales(self) -> Iterable[Locale]:
        assert self._bootstrapped
        return self._locales

    @override
    def get(self, locale: ResolvableLocale) -> gettext.NullTranslations:
        locale = resolve_locale(locale)
        try:
            return self._translations[locale]
        except KeyError:
            self._translations[locale] = gettext.NullTranslations()
            return self._translations[locale]

    async def _build_translation(self, locale: Locale) -> gettext.NullTranslations:
        translations = gettext.NullTranslations()
        for assets_directory_path in reversed(self._assets.directories):
            opened_translations = await self._open_translations(
                locale, assets_directory_path
            )
            if opened_translations:
                opened_translations.add_fallback(translations)
                translations = opened_translations
        self._translations[locale] = translations
        return self._translations[locale]

    async def _open_translations(
        self, locale: Locale, assets_directory_path: Path
    ) -> gettext.GNUTranslations | None:
        po_file_path = (
            assets_directory_path / "locale" / to_language_tag(locale) / "betty.po"
        )
        try:
            translation_version = await hashid_file_meta(po_file_path)
        except FileNotFoundError:
            return None
        cache_directory_path = self._cache.path / "locale" / translation_version
        mo_file_path = cache_directory_path / "betty.mo"

        try:
            mo = await read(mo_file_path, mode="rb")
        except FileNotFoundError:
            pass
        else:
            return gettext.GNUTranslations(BytesIO(mo))

        cache_directory_path.mkdir(exist_ok=True, parents=True)

        await run_babel(
            "",
            "compile",
            "-i",
            str(po_file_path),
            "-o",
            str(mo_file_path),
            "-l",
            str(resolve_locale(locale)),
            "-D",
            "betty",
        )
        return gettext.GNUTranslations(BytesIO(await read(mo_file_path, mode="rb")))

    async def coverage(self, locale: ResolvableLocale) -> tuple[int, int]:
        """
        Get the translation coverage for the given locale.

        :return: A 2-tuple of the number of available translations and the
            number of translatable source strings.
        """
        translatables = {
            translatable async for translatable in self._get_translatables()
        }
        locale = resolve_locale(locale)
        if locale == DEFAULT_LOCALE:
            return len(translatables), len(translatables)
        translations = {
            translation async for translation in self._get_translations(locale)
        }
        return len(translations), len(translatables)

    async def _get_translatables(self) -> AsyncIterator[str]:
        for assets_directory_path in self._assets.directories:
            try:
                pot = await read(assets_directory_path / "locale" / "betty.pot")
            except FileNotFoundError:
                pass
            else:
                for entry in pofile(pot):
                    yield entry.msgid_with_context

    async def _get_translations(self, locale: Locale) -> AsyncIterator[str]:
        for assets_directory_path in reversed(self._assets.directories):
            try:
                po = await read(
                    assets_directory_path
                    / "locale"
                    / to_language_tag(locale)
                    / "betty.po"
                )
            except FileNotFoundError:
                pass
            else:
                for entry in pofile(po):
                    if entry.translated():
                        yield entry.msgid_with_context


@final
class UntranslatedLocale(LocaleError):
    """
    Raised when no translations exist for a locale.
    """

    def __init__(self, locale: Locale, /):
        super().__init__(
            _("Untranslated locale {locale}.").format(locale=to_language_tag(locale))
        )
