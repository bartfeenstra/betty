"""
Manage translations of built-in translatable strings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather, to_thread
from contextlib import redirect_stdout
from gettext import GNUTranslations
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, final, override

from betty import dirs
from betty.babel import run_babel
from betty.concurrent import Ledger, ThreadSafeLock
from betty.file import read
from betty.hashid import hashid_file_meta
from betty.locale import (
    ResolvableLocale,
    default_locale,
    resolve_locale,
    to_language_tag,
)
from betty.localized import LocalizedStr
from betty.pathlib import resolve_path
from betty.user import Severity

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping
    from pathlib import Path

    from babel import Locale

    from betty.asset import AssetDirectoryDefinition, AssetRepository
    from betty.pathlib import StrPath
    from betty.stores.file import TransientBinaryFileStore
    from betty.user import User


async def _new_translation(
    output: AssetDirectoryDefinition, locale: Locale, *, user: User
) -> None:
    from betty.localizables.gettext import _

    po_file = output.assets / "locale" / str(locale) / "betty.po"
    with redirect_stdout(StringIO()):
        if po_file.exists():
            await user.message(
                _("Translations for {locale} already exist at {po_file_path}.").format(
                    locale=to_language_tag(locale), po_file_path=str(po_file)
                ),
                Severity.INFO,
            )
            return

        await run_babel(
            "",
            "init",
            "--no-wrap",
            "-i",
            str(output.assets / "locale" / "betty.pot"),
            "-o",
            str(po_file),
            "-l",
            str(locale),
            "-D",
            "betty",
        )
        await user.message(
            _("Translations for {locale} initialized at {po_file_path}.").format(
                locale=to_language_tag(locale), po_file_path=str(po_file)
            ),
            Severity.CONFIRM,
        )


async def update_builtin_translations(override_output: Path | None = None, /) -> None:
    """
    Update the translations for Betty itself.
    """
    from betty.asset_directories.builtin import builtin

    source_directory = dirs.root_directory / "betty"
    test_directory = source_directory / "tests"
    await _update_translations(
        builtin.assets if override_output is None else override_output,
        _find_source_files({source_directory, dirs.asset_directory}, {test_directory}),
    )


async def _update_translations(output: StrPath, inputs: Iterable[StrPath]) -> None:
    """
    Update all existing translations based on changes in translatable strings.
    """
    output = resolve_path(output)
    pot_file = output / "locale" / "betty.pot"
    await to_thread(pot_file.parent.mkdir, exist_ok=True, parents=True)

    await run_babel(
        "",
        "extract",
        "--no-wrap",
        "--no-location",
        "--sort-output",
        "-F",
        "babel.ini",
        "-o",
        str(pot_file),
        "--project",
        "Betty",
        "--copyright-holder",
        "Bart Feenstra & contributors",
        *map(str, inputs),
    )
    for output_po_file in output.glob("locale/*/betty.po"):
        await run_babel(
            "",
            "update",
            "--no-wrap",
            "--domain",
            "betty",
            "--input-file",
            str(pot_file),
            "--ignore-obsolete",
            "--locale",
            output_po_file.parent.name,
            "--no-fuzzy-matching",
            "--output-file",
            str(output_po_file),
        )


async def new_translation(
    output: AssetDirectoryDefinition, locale: Locale, *, user: User
) -> None:
    """
    Create a new translation.
    """
    await _new_translation(output, locale, user=user)


async def update_translations(
    output: StrPath, inputs: Iterable[StrPath], excludes: Iterable[StrPath], user: User
) -> None:
    """
    Update translations.
    """
    await _update_translations(output, _find_source_files(inputs, excludes))


def _find_source_files(
    inputs: Iterable[StrPath], excludes: Iterable[StrPath], /
) -> Iterable[Path]:
    """
    Find source files in a directory.
    """
    excludes = {resolve_path(exclude).expanduser().resolve() for exclude in excludes}
    for _input in inputs:
        for relative_input_file in (
            resolve_path(_input).expanduser().resolve().rglob("*")
        ):
            input_file = _input / relative_input_file
            if excludes & set(input_file.parents):
                continue
            if input_file.suffix in {".j2", ".py"}:
                yield input_file


class Translations(ABC):
    """
    A set of translations.
    """

    def _(self, message: str, /) -> LocalizedStr | None:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return self.gettext(message)

    @abstractmethod
    def gettext(self, message: str, /) -> LocalizedStr | None:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """

    @abstractmethod
    def ngettext(
        self, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr | None:
        """
        Like :py:meth:`gettext.ngettext`.

        Arguments are identical to those of :py:meth:`gettext.ngettext`.
        """

    @abstractmethod
    def pgettext(self, context: str, message: str, /) -> LocalizedStr | None:
        """
        Like :py:meth:`gettext.pgettext`.

        Arguments are identical to those of :py:meth:`gettext.pgettext`.
        """

    @abstractmethod
    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr | None:
        """
        Like :py:meth:`gettext.npgettext`.

        Arguments are identical to those of :py:meth:`gettext.npgettext`.
        """


@final
class MoTranslations(Translations):
    """
    Translations from ``*.mo`` file data.
    """

    def __init__(self, locale: Locale, mo: bytes, /):
        gnu = GNUTranslations(BytesIO(mo))
        self._catalog = gnu._catalog  # ty:ignore[unresolved-attribute]
        self._plural = gnu.plural  # ty:ignore[unresolved-attribute]
        self._context = gnu.CONTEXT
        self._locale = locale

    def _ls(self, translation: str | None, /) -> LocalizedStr | None:
        if translation is None:
            return None
        return LocalizedStr(translation, locale=self._locale)

    @override
    def gettext(self, message: str, /) -> LocalizedStr | None:
        translation = self._catalog.get(message, None)
        if translation is None:
            translation = self._catalog.get((message, self._plural(1)), None)
        return self._ls(translation)

    @override
    def ngettext(
        self, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr | None:
        return self._ls(self._catalog.get((message_singular, self._plural(n)), None))

    @override
    def pgettext(self, context: str, message: str, /) -> LocalizedStr | None:
        context_msg_id = self._context % (context, message)
        translation = self._catalog.get(context_msg_id, None)
        if translation is None:
            translation = self._catalog.get((context_msg_id, self._plural(1)), None)
        return self._ls(translation)

    @override
    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr | None:
        return self._ls(
            self._catalog.get(
                (self._context % (context, message_singular), self._plural(n)), None
            )
        )


@final
class Translator(Translations):
    """
    Translate strings.

    The translator always reliably returns strings. If no translations can be found, the original source strings are
    returned with the correct locale information.
    """

    def __init__(self, *translations: Translations):
        self._translations = translations

    @override
    def _(self, message: str, /) -> LocalizedStr:
        return self.gettext(message)

    @override
    def gettext(self, message: str, /) -> LocalizedStr:
        for translations in self._translations:
            if translation := translations.gettext(message):
                return translation
        return LocalizedStr(message, locale=default_locale)

    @override
    def ngettext(
        self, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr:
        for translations in self._translations:
            if translation := translations.ngettext(
                message_singular, message_plural, n
            ):
                return translation
        return LocalizedStr(
            message_singular if n == 1 else message_plural, locale=default_locale
        )

    @override
    def pgettext(self, context: str, message: str, /) -> LocalizedStr:
        for translations in self._translations:
            if translation := translations.pgettext(context, message):
                return translation
        return LocalizedStr(message, locale=default_locale)

    @override
    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr:
        for translations in self._translations:
            if translation := translations.npgettext(
                context, message_singular, message_plural, n
            ):
                return translation
        return LocalizedStr(
            message_singular if n == 1 else message_plural, locale=default_locale
        )


@final
class TranslationsRepository:
    """
    Expose translations.
    """

    def __init__(self, *, assets: AssetRepository, cache: TransientBinaryFileStore):
        self._assets = assets
        self._cache_directory = cache.with_scope("gettext").directory
        self._ledger = Ledger(ThreadSafeLock())
        self._translations: MutableMapping[Locale, tuple[Translations, ...]] = {}

    async def get(self, locale: ResolvableLocale, /) -> Iterable[Translations]:
        """
        Get the translations for the given locale.
        """
        locale = resolve_locale(locale)
        translations = self._translations.get(locale, None)
        if translations is not None:
            return translations
        async with self._ledger.ledger(str(locale)):
            translations = self._translations.get(locale, None)
            if translations is not None:
                return translations
            translations = self._translations[locale] = tuple(
                filter(
                    None,
                    await gather(*[
                        self._get_po_file(locale, asset_directory)
                        for asset_directory in reversed(self._assets.directories)
                    ]),
                )
            )
            return translations

    async def _get_po_file(
        self, locale: Locale, asset_directory: Path
    ) -> Translations | None:
        po_file = asset_directory / "locale" / str(locale) / "betty.po"
        try:
            po_file_version = await hashid_file_meta(po_file)
        except FileNotFoundError:
            return None
        mo_file = self._cache_directory / po_file_version / "betty.mo"

        try:
            mo = await read(mo_file, mode="rb")
        except FileNotFoundError:
            pass
        else:
            return MoTranslations(locale, mo)

        mo_file.parent.mkdir(exist_ok=True, parents=True)

        await run_babel(
            "",
            "compile",
            "-i",
            str(po_file),
            "-o",
            str(mo_file),
            "-l",
            str(locale),
            "-D",
            "betty",
        )
        return MoTranslations(locale, await read(mo_file, mode="rb"))
