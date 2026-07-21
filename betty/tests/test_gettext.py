from __future__ import annotations

from typing import TYPE_CHECKING, Final, override

import pytest
from babel import Locale

from betty.asset import StaticAssetRepository
from betty.babel import run_babel
from betty.dirs import builtin_asset_directory
from betty.file import read, write
from betty.gettext import (
    MoTranslations,
    Translations,
    TranslationsRepository,
    Translator,
    update_builtin_translations,
)
from betty.locale import default_locale
from betty.localized import LocalizedStr
from betty.stores.file import TransientBinaryFileStore
from betty.test_utils.gettext import UntranslatedTranslations
from betty.test_utils.locale import PotFileTestBase

if TYPE_CHECKING:
    from pathlib import Path

    from betty.pathlib import StrPath

_dummy_pot: Final[str] = """
# Translations template for Betty.
# Copyright (C) 2024 Bart Feenstra & contributors
# This file is distributed under the same license as the Betty project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2024.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: Betty VERSION\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2024-09-01 10:31+0100\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.16.0\n"

msgid "Subject"
msgstr ""
"""


_dummy_po: Final[str] = """
# Dutch translations for PROJECT.
# Copyright (C) 2019 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2019.
#
msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2024-09-01 10:31+0100\n"
"PO-Revision-Date: 2024-02-11 15:31+0000\n"
"Last-Translator: Bart Feenstra <bart@bartfeenstra.com>\n"
"Language: nl\n"
"Language-Team: nl <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.16.0\n"

#: betty/ancestry.py:457
msgid "Subject"
msgstr "Onderwerp"
"""


class TestPotFile(PotFileTestBase):
    @override
    def asset_directory(self) -> StrPath:
        return builtin_asset_directory

    @override
    def command(self) -> str:
        return "betty dev-update-translations"  # pragma: no cover

    @override
    async def update_translations(
        self, output_asset_directory_override: Path, /
    ) -> None:
        await update_builtin_translations(output_asset_directory_override)


class TestTranslationsRepository:
    async def test_get__without_translations(self, tmp_path: Path) -> None:
        sut = TranslationsRepository(
            assets=StaticAssetRepository(tmp_path / "asset"),
            cache=TransientBinaryFileStore(tmp_path / "cache"),
        )
        assert not list(await sut.get(Locale("nl")))

    async def test_get__with_translations(self, tmp_path: Path) -> None:
        asset_directory = tmp_path / "asset"
        po_file = asset_directory / "locale" / "nl" / "betty.po"
        po_file.parent.mkdir(parents=True)
        with open(po_file, "w", encoding="utf-8") as f:
            f.write(_dummy_po)
        # Do this multiple times so we hit the file caches.
        for _ in range(2):
            sut = TranslationsRepository(
                assets=StaticAssetRepository(asset_directory),
                cache=TransientBinaryFileStore(tmp_path / "cache"),
            )
            actual = await sut.get(Locale("nl"))
            assert next(iter(actual)).gettext("Subject") == "Onderwerp"


class TestMoTranslations:
    _mo_locale = Locale("nl", "NL")
    _mo_po_untranslated = r"""
    msgid ""
    msgstr ""
    "Plural-Forms: nplurals=2; plural=n != 1;\n"
    "Content-Type: text/plain; charset=utf-8\n"
    """
    _mo_po_translated = (
        _mo_po_untranslated
        + r"""
# _, gettext
msgid "Hello, world!"
msgstr "Hallo, wereld!"

# ngettext
msgid "Hello, singular world!"
msgid_plural "Hello, plural worlds!"
msgstr[0] "Hallo, enkelvoudige wereld!"
msgstr[1] "Hallo, meervoudige werelden!"

# npgettext
msgctxt "hello-contextual-world"
msgid "Hello, singular world!"
msgid_plural "Hello, plural worlds!"
msgstr[0] "Hallo, enkelvoudige contextuele wereld!"
msgstr[1] "Hallo, meervoudige contextuele werelden!"

# pgettext
msgctxt "hello-contextual-world"
msgid "Hello, world!"
msgstr "Hallo, contextuele wereld!"
    """
    )

    @pytest.fixture
    async def mo_untranslated(self, tmp_path: Path) -> MoTranslations:
        return await self._mo(tmp_path, self._mo_po_untranslated)

    @pytest.fixture
    async def mo_translated(self, tmp_path: Path) -> MoTranslations:
        return await self._mo(tmp_path, self._mo_po_translated)

    async def _mo(self, tmp_path: Path, po: str) -> MoTranslations:
        po_file = tmp_path / "mo.po"
        await write(po_file, po)
        mo_file = tmp_path / "mo.mo"
        await run_babel(
            "",
            "compile",
            "-i",
            str(po_file),
            "-o",
            str(mo_file),
            "-l",
            str(self._mo_locale),
        )
        return MoTranslations(self._mo_locale, await read(mo_file, mode="rb"))

    def test____without_translation(self, mo_untranslated: MoTranslations) -> None:
        assert mo_untranslated._("Hello, world!") is None

    def test____with_translation(self, mo_translated: MoTranslations) -> None:
        assert mo_translated._("Hello, world!") == LocalizedStr(
            "Hallo, wereld!", locale=self._mo_locale
        )

    def test_gettext__without_translation(
        self, mo_untranslated: MoTranslations
    ) -> None:
        assert mo_untranslated.gettext("Hello, world!") is None

    def test_gettext__with_translation(self, mo_translated: MoTranslations) -> None:
        assert mo_translated.gettext("Hello, world!") == LocalizedStr(
            "Hallo, wereld!", locale=self._mo_locale
        )

    def test_ngettext__without_translation(
        self, mo_untranslated: MoTranslations
    ) -> None:
        assert (
            mo_untranslated.ngettext(
                "Hello, singular world!", "Hello, plural worlds!", 1
            )
            is None
        )

    def test_ngettext__with_translation(self, mo_translated: MoTranslations) -> None:
        assert mo_translated.ngettext(
            "Hello, singular world!", "Hello, plural worlds!", 1
        ) == LocalizedStr("Hallo, enkelvoudige wereld!", locale=self._mo_locale)
        assert mo_translated.ngettext(
            "Hello, singular world!", "Hello, plural worlds!", 2
        ) == LocalizedStr("Hallo, meervoudige werelden!", locale=self._mo_locale)

    def test_npgettext__without_translation(
        self, mo_untranslated: MoTranslations
    ) -> None:
        assert (
            mo_untranslated.npgettext(
                "hello-contextual-world", "Hello, world!", "Hello, worlds!", 1
            )
            is None
        )

    def test_npgettext__with_translation(self, mo_translated: MoTranslations) -> None:
        assert mo_translated.npgettext(
            "hello-contextual-world",
            "Hello, singular world!",
            "Hello, plural worlds!",
            1,
        ) == LocalizedStr(
            "Hallo, enkelvoudige contextuele wereld!", locale=self._mo_locale
        )
        assert mo_translated.npgettext(
            "hello-contextual-world",
            "Hello, singular world!",
            "Hello, plural worlds!",
            2,
        ) == LocalizedStr(
            "Hallo, meervoudige contextuele werelden!", locale=self._mo_locale
        )

    def test_pgettext__without_translation(
        self, mo_untranslated: MoTranslations
    ) -> None:
        assert (
            mo_untranslated.pgettext("hello-contextual-world", "Hello, world!") is None
        )

    def test_pgettext__with_translation(self, mo_translated: MoTranslations) -> None:
        assert mo_translated.pgettext(
            "hello-contextual-world", "Hello, world!"
        ) == LocalizedStr("Hallo, contextuele wereld!", locale=self._mo_locale)


class TestTranslator:
    _locale = Locale("nl", "NL")

    class _Translated(Translations):
        @override
        def gettext(self, message: str, /) -> LocalizedStr | None:
            return LocalizedStr("Hallo, wereld!", locale=TestTranslator._locale)

        @override
        def ngettext(
            self, message_singular: str, message_plural: str, n: int, /
        ) -> LocalizedStr | None:
            return LocalizedStr(
                "Hallo, enkelvoudige wereld!"
                if n == 1
                else "Hallo, meervoudige werelden!",
                locale=TestTranslator._locale,
            )

        @override
        def pgettext(self, context: str, message: str, /) -> LocalizedStr | None:
            return LocalizedStr(
                "Hallo, contextuele wereld!", locale=TestTranslator._locale
            )

        @override
        def npgettext(
            self, context: str, message_singular: str, message_plural: str, n: int, /
        ) -> LocalizedStr | None:
            return LocalizedStr(
                "Hallo, enkelvoudige contextuele wereld!"
                if n == 1
                else "Hallo, meervoudige contextuele werelden!",
                locale=TestTranslator._locale,
            )

    def test____without_translations(self) -> None:
        assert Translator()._("Hello, world!") == LocalizedStr(
            "Hello, world!", locale=default_locale
        )

    def test____without_translation(self) -> None:
        assert Translator(UntranslatedTranslations())._(
            "Hello, world!"
        ) == LocalizedStr("Hello, world!", locale=default_locale)

    def test____with_translation(self) -> None:
        assert Translator(self._Translated())._("Hello, world!") == LocalizedStr(
            "Hallo, wereld!", locale=self._locale
        )

    def test_gettext__without_translations(self) -> None:
        assert Translator().gettext("Hello, world!") == LocalizedStr(
            "Hello, world!", locale=default_locale
        )

    def test_gettext__without_translation(self) -> None:
        assert Translator(UntranslatedTranslations()).gettext(
            "Hello, world!"
        ) == LocalizedStr("Hello, world!", locale=default_locale)

    def test_gettext__with_translation(self) -> None:
        assert Translator(self._Translated()).gettext("Hello, world!") == LocalizedStr(
            "Hallo, wereld!", locale=self._locale
        )

    def test_ngettext__without_translations(self) -> None:
        assert Translator().ngettext(
            "Hello, world!", "Hello, worlds!", 1
        ) == LocalizedStr("Hello, world!", locale=default_locale)
        assert Translator().ngettext(
            "Hello, world!", "Hello, worlds!", 9
        ) == LocalizedStr("Hello, worlds!", locale=default_locale)

    def test_ngettext__without_translation(self) -> None:
        assert Translator(UntranslatedTranslations()).ngettext(
            "Hello, world!", "Hello, worlds!", 1
        ) == LocalizedStr("Hello, world!", locale=default_locale)
        assert Translator(UntranslatedTranslations()).ngettext(
            "Hello, world!", "Hello, worlds!", 9
        ) == LocalizedStr("Hello, worlds!", locale=default_locale)

    def test_ngettext__with_translation(self) -> None:
        assert Translator(self._Translated()).ngettext(
            "Hello, world!", "Hello, worlds!", 1
        ) == LocalizedStr("Hallo, enkelvoudige wereld!", locale=default_locale)
        assert Translator(self._Translated()).ngettext(
            "Hello, world!", "Hello, worlds!", 9
        ) == LocalizedStr("Hallo, meervoudige werelden!", locale=default_locale)

    def test_npgettext__without_translations(self) -> None:
        assert Translator().npgettext(
            "hello-contextual-world", "Hello, world!", "Hello, worlds!", 1
        ) == LocalizedStr("Hello, world!", locale=default_locale)
        assert Translator().npgettext(
            "hello-contextual-world", "Hello, world!", "Hello, worlds!", 9
        ) == LocalizedStr("Hello, worlds!", locale=default_locale)

    def test_npgettext__without_translation(self) -> None:
        assert Translator(UntranslatedTranslations()).npgettext(
            "hello-contextual-world", "Hello, world!", "Hello, worlds!", 1
        ) == LocalizedStr("Hello, world!", locale=default_locale)
        assert Translator(UntranslatedTranslations()).npgettext(
            "hello-contextual-world", "Hello, world!", "Hello, worlds!", 9
        ) == LocalizedStr("Hello, worlds!", locale=default_locale)

    def test_npgettext__with_translation(self) -> None:
        assert Translator(self._Translated()).npgettext(
            "hello-contextual-world", "Hello, world!", "Hello, worlds!", 1
        ) == LocalizedStr(
            "Hallo, enkelvoudige contextuele wereld!", locale=default_locale
        )
        assert Translator(self._Translated()).npgettext(
            "hello-contextual-world", "Hello, world!", "Hello, worlds!", 9
        ) == LocalizedStr(
            "Hallo, meervoudige contextuele werelden!", locale=default_locale
        )

    def test_pgettext__without_translations(self) -> None:
        assert Translator().pgettext(
            "hello-contextual-world", "Hello, world!"
        ) == LocalizedStr("Hello, world!", locale=default_locale)

    def test_pgettext__without_translation(self) -> None:
        assert Translator(UntranslatedTranslations()).pgettext(
            "hello-contextual-world", "Hello, world!"
        ) == LocalizedStr("Hello, world!", locale=default_locale)

    def test_pgettext__with_translation(self) -> None:
        assert Translator(self._Translated()).pgettext(
            "hello-contextual-world", "Hello, world!"
        ) == LocalizedStr("Hallo, contextuele wereld!", locale=self._locale)
