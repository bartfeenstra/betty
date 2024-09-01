from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import aiofiles
import pytest

from betty.assets import AssetRepository
from betty.locale import DEFAULT_LOCALE
from betty.locale.date import Date, DateRange, Datey, IncompleteDateError
from betty.locale.localizer import DEFAULT_LOCALIZER, LocalizerRepository

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Sequence


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


class TestLocalizer:
    _FORMAT_DATE_TEST_PARAMETERS: Sequence[tuple[str, Date]] = [
        # Dates that cannot be formatted.
        ("unknown date", Date()),
        ("unknown date", Date(None, None, 1)),
        # Single dates.
        ("January", Date(None, 1, None)),
        ("around January", Date(None, 1, None, fuzzy=True)),
        ("1970", Date(1970, None, None)),
        ("around 1970", Date(1970, None, None, fuzzy=True)),
        ("January, 1970", Date(1970, 1, None)),
        ("around January, 1970", Date(1970, 1, None, fuzzy=True)),
        ("January 1, 1970", Date(1970, 1, 1)),
        ("around January 1, 1970", Date(1970, 1, 1, fuzzy=True)),
        ("January 1", Date(None, 1, 1)),
        ("around January 1", Date(None, 1, 1, fuzzy=True)),
    ]

    @pytest.mark.parametrize(("expected", "date"), _FORMAT_DATE_TEST_PARAMETERS)
    async def test_format_date(self, expected: str, date: Date) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.format_date(date) == expected

    _FORMAT_DATE_RANGE_TEST_PARAMETERS: Sequence[tuple[str, DateRange]] = [
        (
            "from January 1, 1970 until December 31, 1999",
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
        ),
        (
            "from January 1, 1970 until sometime before December 31, 1999",
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True),
        ),
        (
            "from January 1, 1970 until around December 31, 1999",
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True)),
        ),
        (
            "from January 1, 1970 until sometime before around December 31, 1999",
            DateRange(
                Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), end_is_boundary=True
            ),
        ),
        (
            "from sometime after January 1, 1970 until December 31, 1999",
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31), start_is_boundary=True),
        ),
        (
            "sometime between January 1, 1970 and December 31, 1999",
            DateRange(
                Date(1970, 1, 1),
                Date(1999, 12, 31),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        (
            "from sometime after January 1, 1970 until around December 31, 1999",
            DateRange(
                Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True
            ),
        ),
        (
            "sometime between January 1, 1970 and around December 31, 1999",
            DateRange(
                Date(1970, 1, 1),
                Date(1999, 12, 31, fuzzy=True),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        (
            "from around January 1, 1970 until December 31, 1999",
            DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31)),
        ),
        (
            "from around January 1, 1970 until sometime before December 31, 1999",
            DateRange(
                Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), end_is_boundary=True
            ),
        ),
        (
            "from around January 1, 1970 until around December 31, 1999",
            DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True)),
        ),
        (
            "from around January 1, 1970 until sometime before around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, fuzzy=True),
                Date(1999, 12, 31, fuzzy=True),
                end_is_boundary=True,
            ),
        ),
        (
            "from sometime after around January 1, 1970 until December 31, 1999",
            DateRange(
                Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), start_is_boundary=True
            ),
        ),
        (
            "sometime between around January 1, 1970 and December 31, 1999",
            DateRange(
                Date(1970, 1, 1, fuzzy=True),
                Date(1999, 12, 31),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        (
            "from sometime after around January 1, 1970 until around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, fuzzy=True),
                Date(1999, 12, 31, fuzzy=True),
                start_is_boundary=True,
            ),
        ),
        (
            "sometime between around January 1, 1970 and around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, fuzzy=True),
                Date(1999, 12, 31, fuzzy=True),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        ("from January 1, 1970", DateRange(Date(1970, 1, 1))),
        (
            "sometime after January 1, 1970",
            DateRange(Date(1970, 1, 1), start_is_boundary=True),
        ),
        ("from around January 1, 1970", DateRange(Date(1970, 1, 1, fuzzy=True))),
        (
            "sometime after around January 1, 1970",
            DateRange(Date(1970, 1, 1, fuzzy=True), start_is_boundary=True),
        ),
        ("until December 31, 1999", DateRange(None, Date(1999, 12, 31))),
        (
            "sometime before December 31, 1999",
            DateRange(None, Date(1999, 12, 31), end_is_boundary=True),
        ),
        (
            "until around December 31, 1999",
            DateRange(None, Date(1999, 12, 31, fuzzy=True)),
        ),
        (
            "sometime before around December 31, 1999",
            DateRange(None, Date(1999, 12, 31, fuzzy=True), end_is_boundary=True),
        ),
    ]

    @pytest.mark.parametrize(
        ("expected", "date_range"), _FORMAT_DATE_RANGE_TEST_PARAMETERS
    )
    async def test_format_date_range(
        self, expected: str, date_range: DateRange
    ) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.format_date_range(date_range) == expected

    @pytest.mark.parametrize(
        "date_range",
        [
            DateRange(),
            DateRange(Date()),
            DateRange(None, Date()),
            DateRange(Date(), Date()),
        ],
    )
    async def test_format_date_range_with_incomplete_date_range(
        self, date_range: DateRange
    ) -> None:
        sut = DEFAULT_LOCALIZER
        with pytest.raises(IncompleteDateError):
            assert sut.format_date_range(date_range)

    _FORMAT_DATEY_TEST_PARAMETERS = (
        *_FORMAT_DATE_TEST_PARAMETERS,
        *_FORMAT_DATE_RANGE_TEST_PARAMETERS,
    )

    @pytest.mark.parametrize(("expected", "datey"), _FORMAT_DATEY_TEST_PARAMETERS)
    async def test_format_datey(self, expected: str, datey: Datey) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.format_datey(datey) == expected

    async def test_format_datetime_datetime(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.format_datetime_datetime(datetime.datetime(1970, 1, 1))
            == "January 1, 1970"
        )

    async def test_locale(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.locale == DEFAULT_LOCALE

    async def test__(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut._("My First Translatable String") == "My First Translatable String"

    async def test_gettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.gettext("My First Translatable String")
            == "My First Translatable String"
        )

    async def test_ngettext_with_singular(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 1
            )
            == "My First Translatable String"
        )

    async def test_ngettext_with_plural(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 9
            )
            == "My First Translatable Strings"
        )

    async def test_npgettext_with_singular(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.npgettext(
                "My First Context",
                "My First Translatable String",
                "My First Translatable Strings",
                1,
            )
            == "My First Translatable String"
        )

    async def test_npgettext_with_plural(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.npgettext(
                "My First Context",
                "My First Translatable String",
                "My First Translatable Strings",
                9,
            )
            == "My First Translatable Strings"
        )

    async def test_pgettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.pgettext("My First Context", "My First Translatable String")
            == "My First Translatable String"
        )


class TestLocalizerRepository:
    async def test_get_with_known_translations(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        assets_directory_path = tmp_path / "assets"
        po_file_path = assets_directory_path / "locale" / locale / "betty.po"
        po_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(po_file_path, "w") as f:
            await f.write(_DUMMY_PO)
        # Do this multiple times so we hit the file caches.
        for _ in range(0, 2):
            sut = LocalizerRepository(AssetRepository(assets_directory_path))
            actual = (await sut.get(locale))._("Subject")
            assert actual == "Onderwerp"

    async def test_get_with_unknown_translations(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        sut = LocalizerRepository(AssetRepository(tmp_path / "assets"))
        actual = (await sut.get(locale))._("Subject")
        assert actual == "Subject"

    async def test_coverage_with_default_locale(self, tmp_path: Path) -> None:
        assets_directory_path = tmp_path / "assets"
        pot_file_path = assets_directory_path / "locale" / "betty.pot"
        pot_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(pot_file_path, "w") as f:
            await f.write(_DUMMY_POT)
        sut = LocalizerRepository(AssetRepository(assets_directory_path))
        translated_count, translatable_count = await sut.coverage(DEFAULT_LOCALE)
        assert translatable_count == 1
        assert translated_count == translatable_count

    async def test_coverage_with_untranslated_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        assets_directory_path = tmp_path / "assets"
        pot_file_path = assets_directory_path / "locale" / "betty.pot"
        pot_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(pot_file_path, "w") as f:
            await f.write(_DUMMY_POT)
        sut = LocalizerRepository(AssetRepository(assets_directory_path))
        translated_count, translatable_count = await sut.coverage(locale)
        assert translatable_count == 1
        assert translated_count == 0

    async def test_coverage_with_translated_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        assets_directory_path = tmp_path / "assets"
        pot_file_path = assets_directory_path / "locale" / "betty.pot"
        pot_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(pot_file_path, "w") as f:
            await f.write(_DUMMY_POT)
        po_file_path = assets_directory_path / "locale" / locale / "betty.po"
        po_file_path.parent.mkdir(parents=True)
        async with aiofiles.open(po_file_path, "w") as f:
            await f.write(_DUMMY_PO)
        sut = LocalizerRepository(AssetRepository(assets_directory_path))
        translated_count, translatable_count = await sut.coverage(locale)
        assert translatable_count == 1
        assert translated_count == 1

    async def test_get_negotiated_without_preferred_locales(self) -> None:
        sut = LocalizerRepository(AssetRepository())
        assert (await sut.get_negotiated()).locale == DEFAULT_LOCALE

    async def test_locales_without_assets_directories(self) -> None:
        sut = LocalizerRepository(AssetRepository())
        assert set(sut.locales) == {DEFAULT_LOCALE}

    async def test_locales_with_empty_assets_directory(self, tmp_path: Path) -> None:
        sut = LocalizerRepository(AssetRepository(tmp_path / "assets"))
        assert set(sut.locales) == {DEFAULT_LOCALE}

    async def test_locales_with_available_translation(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        assets_directory_path = tmp_path / "assets"
        lc_messages_directory_path = assets_directory_path / "locale" / locale
        lc_messages_directory_path.mkdir(parents=True)
        async with aiofiles.open(lc_messages_directory_path / "betty.po", "w") as f:
            await f.write(_DUMMY_PO)

        sut = LocalizerRepository(AssetRepository(assets_directory_path))
        assert set(sut.locales) == {DEFAULT_LOCALE, locale}
