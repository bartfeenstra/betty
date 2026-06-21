from __future__ import annotations

import gettext
from typing import TYPE_CHECKING, Final, override

import pytest
from babel import Locale

from betty.asset import StaticAssetRepository
from betty.caches.file import BinaryFileCache
from betty.dirs import builtin_asset_directory
from betty.gettext import (
    AssetTranslationRepository,
    StaticTranslationRepository,
    UntranslatedLocale,
    update_app_translations,
)
from betty.locale import default_locale
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
        await update_app_translations(output_asset_directory_override)


class TestAssetTranslationRepository:
    async def test_get__with_known_translations(self, tmp_path: Path) -> None:
        locale = "nl"
        asset_directory = tmp_path / "asset"
        po_file = asset_directory / "locale" / locale / "betty.po"
        po_file.parent.mkdir(parents=True)
        with open(po_file, "w", encoding="utf-8") as f:
            f.write(_dummy_po)
        # Do this multiple times so we hit the file caches.
        for _ in range(2):
            sut = AssetTranslationRepository(
                StaticAssetRepository(asset_directory),
                BinaryFileCache(tmp_path / "cache"),
            )
            await sut.bootstrap()
            translation = sut.get(locale)
            actual = translation.gettext("Subject")
            assert actual == "Onderwerp"

    async def test_get__with_unknown_translations(self, tmp_path: Path) -> None:
        locale = "nl"
        sut = AssetTranslationRepository(
            StaticAssetRepository(tmp_path / "asset"),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translation = sut.get(locale)
        assert translation.gettext("Subject") == "Subject"

    async def test_coverage__with_default_locale(self, tmp_path: Path) -> None:
        asset_directory = tmp_path / "asset"
        pot_file = asset_directory / "locale" / "betty.pot"
        pot_file.parent.mkdir(parents=True)
        with open(pot_file, "w", encoding="utf-8") as f:
            f.write(_dummy_pot)
        sut = AssetTranslationRepository(
            StaticAssetRepository(asset_directory),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translated_count, translatable_count = await sut.coverage(default_locale)
        assert translatable_count == 1
        assert translated_count == translatable_count

    async def test_coverage__with_untranslated_locale(self, tmp_path: Path) -> None:
        locale = "nl"
        asset_directory = tmp_path / "asset"
        pot_file = asset_directory / "locale" / "betty.pot"
        pot_file.parent.mkdir(parents=True)
        with open(pot_file, "w", encoding="utf-8") as f:
            f.write(_dummy_pot)
        sut = AssetTranslationRepository(
            StaticAssetRepository(asset_directory),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translated_count, translatable_count = await sut.coverage(locale)
        assert translatable_count == 1
        assert translated_count == 0

    async def test_coverage__with_translated_locale(self, tmp_path: Path) -> None:
        locale = "nl"
        asset_directory = tmp_path / "asset"
        pot_file = asset_directory / "locale" / "betty.pot"
        pot_file.parent.mkdir(parents=True)
        with open(pot_file, "w", encoding="utf-8") as f:
            f.write(_dummy_pot)
        po_file = asset_directory / "locale" / locale / "betty.po"
        po_file.parent.mkdir(parents=True)
        with open(po_file, "w", encoding="utf-8") as f:
            f.write(_dummy_po)
        sut = AssetTranslationRepository(
            StaticAssetRepository(asset_directory),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translated_count, translatable_count = await sut.coverage(locale)
        assert translatable_count == 1
        assert translated_count == 1

    async def test_locales__without_assets_directories(self, tmp_path: Path) -> None:
        sut = AssetTranslationRepository(
            StaticAssetRepository(),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        assert set(sut.locales) == {default_locale}

    async def test_locales__with_empty_asset_directory(self, tmp_path: Path) -> None:
        sut = AssetTranslationRepository(
            StaticAssetRepository(tmp_path / "asset"),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        assert set(sut.locales) == {default_locale}

    async def test_locales__with_available_translation(self, tmp_path: Path) -> None:
        locale = "nl"
        asset_directory = tmp_path / "asset"
        lc_messages_directory = asset_directory / "locale" / locale
        lc_messages_directory.mkdir(parents=True)
        with open(lc_messages_directory / "betty.po", "w", encoding="utf-8") as f:
            f.write(_dummy_po)

        sut = AssetTranslationRepository(
            StaticAssetRepository(asset_directory),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        assert set(sut.locales) == {default_locale, Locale(locale)}


class TestStaticTranslationRepository:
    def test_locales(self) -> None:
        locale = Locale("nl")
        sut = StaticTranslationRepository({locale: gettext.NullTranslations()})
        assert list(sut.locales) == [locale]

    def test_get(self) -> None:
        translation = gettext.NullTranslations()
        locale = "nl"
        sut = StaticTranslationRepository({Locale(locale): translation})
        assert sut.get(locale) is translation

    def test_get__with_unknown_locale(self) -> None:
        sut = StaticTranslationRepository({})
        with pytest.raises(UntranslatedLocale):
            sut.get("nl")


class TestUntranslatedLocale:
    def test(self) -> None:
        locale = "nl"
        sut = UntranslatedLocale(Locale(locale))
        assert locale in str(sut)
