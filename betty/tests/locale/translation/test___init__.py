from __future__ import annotations

import gettext
from typing import TYPE_CHECKING

import aiofiles
import pytest
from babel import Locale
from typing_extensions import override

from betty.asset import StaticAssetRepository
from betty.cache.file import BinaryFileCache
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE
from betty.locale.translation import (
    AssetTranslationRepository,
    NoOpTranslationRepository,
    ProxyTranslationRepository,
    StaticTranslationRepository,
    UntranslatedLocale,
    update_dev_translations,
)
from betty.test_utils.locale import PotFileTestBase

if TYPE_CHECKING:
    from pathlib import Path

_DUMMY_POT = """
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


_DUMMY_PO = """
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
    def assets_directory_path(self) -> Path:
        return ASSETS_DIRECTORY_PATH

    @override
    def command(self) -> str:
        return "betty dev-update-translations"  # pragma: no cover

    @override
    async def update_translations(
        self, output_assets_directory_path_override: Path
    ) -> None:
        await update_dev_translations(
            _output_assets_directory_path_override=output_assets_directory_path_override
        )


class TestAssetTranslationRepository:
    async def test_get__with_known_translations(self, tmp_path: Path) -> None:
        locale = "nl"
        assets_directory_path = tmp_path / "assets"
        po_file_path = assets_directory_path / "locale" / locale / "betty.po"
        po_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(po_file_path, "w") as f:
            await f.write(_DUMMY_PO)
        # Do this multiple times so we hit the file caches.
        for _ in range(2):
            sut = AssetTranslationRepository(
                StaticAssetRepository(assets_directory_path),
                BinaryFileCache(tmp_path / "cache"),
            )
            await sut.bootstrap()
            translation = sut.get(locale)
            actual = translation.gettext("Subject")
            assert actual == "Onderwerp"

    async def test_get__with_unknown_translations(self, tmp_path: Path) -> None:
        locale = "nl"
        sut = AssetTranslationRepository(
            StaticAssetRepository(tmp_path / "assets"),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translation = sut.get(locale)
        assert translation.gettext("Subject") == "Subject"

    async def test_coverage__with_default_locale(self, tmp_path: Path) -> None:
        assets_directory_path = tmp_path / "assets"
        pot_file_path = assets_directory_path / "locale" / "betty.pot"
        pot_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(pot_file_path, "w") as f:
            await f.write(_DUMMY_POT)
        sut = AssetTranslationRepository(
            StaticAssetRepository(assets_directory_path),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translated_count, translatable_count = await sut.coverage(DEFAULT_LOCALE)
        assert translatable_count == 1
        assert translated_count == translatable_count

    async def test_coverage__with_untranslated_locale(self, tmp_path: Path) -> None:
        locale = "nl"
        assets_directory_path = tmp_path / "assets"
        pot_file_path = assets_directory_path / "locale" / "betty.pot"
        pot_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(pot_file_path, "w") as f:
            await f.write(_DUMMY_POT)
        sut = AssetTranslationRepository(
            StaticAssetRepository(assets_directory_path),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        translated_count, translatable_count = await sut.coverage(locale)
        assert translatable_count == 1
        assert translated_count == 0

    async def test_coverage__with_translated_locale(self, tmp_path: Path) -> None:
        locale = "nl"
        assets_directory_path = tmp_path / "assets"
        pot_file_path = assets_directory_path / "locale" / "betty.pot"
        pot_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(pot_file_path, "w") as f:
            await f.write(_DUMMY_POT)
        po_file_path = assets_directory_path / "locale" / locale / "betty.po"
        po_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(po_file_path, "w") as f:
            await f.write(_DUMMY_PO)
        sut = AssetTranslationRepository(
            StaticAssetRepository(assets_directory_path),
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
        assert set(sut.locales) == {DEFAULT_LOCALE}

    async def test_locales__with_empty_assets_directory(self, tmp_path: Path) -> None:
        sut = AssetTranslationRepository(
            StaticAssetRepository(tmp_path / "assets"),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        assert set(sut.locales) == {DEFAULT_LOCALE}

    async def test_locales__with_available_translation(self, tmp_path: Path) -> None:
        locale = "nl"
        assets_directory_path = tmp_path / "assets"
        lc_messages_directory_path = assets_directory_path / "locale" / locale
        lc_messages_directory_path.mkdir(parents=True)
        async with aiofiles.open(lc_messages_directory_path / "betty.po", "w") as f:
            await f.write(_DUMMY_PO)

        sut = AssetTranslationRepository(
            StaticAssetRepository(assets_directory_path),
            BinaryFileCache(tmp_path / "cache"),
        )
        await sut.bootstrap()
        assert set(sut.locales) == {DEFAULT_LOCALE, Locale(locale)}


class TestNoOpTranslationRepository:
    def test_locales(self) -> None:
        sut = NoOpTranslationRepository()
        assert not list(sut.locales)

    def test_get(self) -> None:
        sut = NoOpTranslationRepository()
        sut.get("nl")


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


class TestProxyTranslationRepository:
    def test_locales(self) -> None:
        locale_one = Locale("nl")
        locale_two = Locale("uk")
        upstream_one = StaticTranslationRepository(
            {locale_one: gettext.NullTranslations()}
        )
        upstream_two = StaticTranslationRepository(
            {locale_two: gettext.NullTranslations()}
        )
        sut = ProxyTranslationRepository(upstream_one, upstream_two)
        assert list(sut.locales) == [locale_one, locale_two]

    def test_locales__without_upstreams(self) -> None:
        sut = ProxyTranslationRepository()
        assert not list(sut.locales)

    def test_get(self) -> None:
        locale_one = Locale("nl")
        locale_two = Locale("uk")
        translation_one = gettext.NullTranslations()
        translation_two = gettext.NullTranslations()
        upstream_one = StaticTranslationRepository({locale_one: translation_one})
        upstream_two = StaticTranslationRepository({locale_two: translation_two})
        sut = ProxyTranslationRepository(upstream_one, upstream_two)
        assert sut.get(locale_one) is translation_one
        assert sut.get(locale_two) is translation_two

    def test_get__without_upstreams(self) -> None:
        sut = ProxyTranslationRepository()
        with pytest.raises(UntranslatedLocale):
            sut.get("nl")


class TestUntranslatedLocale:
    def test(self) -> None:
        locale = "nl"
        sut = UntranslatedLocale(Locale(locale))
        assert locale in str(sut)
