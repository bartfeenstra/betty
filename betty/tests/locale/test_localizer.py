from __future__ import annotations

from pathlib import Path
from typing import cast

import aiofiles
import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.assets import AssetRepository
from betty.locale.date import Date, DateRange, Datey
from betty.locale.localizer import DEFAULT_LOCALIZER, LocalizerRepository


class TestDefaultLocalizer:
    _FORMAT_DATE_TEST_PARAMETERS: list[tuple[str, Date]] = [
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
        assert expected == sut.format_date(date)

    _FORMAT_DATE_RANGE_TEST_PARAMETERS: list[tuple[str, DateRange]] = [
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
        assert expected == sut.format_date_range(date_range)

    _FORMAT_DATEY_TEST_PARAMETERS = cast(
        list[tuple[str, Datey]], _FORMAT_DATE_TEST_PARAMETERS
    ) + cast(list[tuple[str, Datey]], _FORMAT_DATE_RANGE_TEST_PARAMETERS)

    @pytest.mark.parametrize(("expected", "datey"), _FORMAT_DATEY_TEST_PARAMETERS)
    async def test_format_datey(self, expected: str, datey: Datey) -> None:
        sut = DEFAULT_LOCALIZER
        assert expected == sut.format_datey(datey)


class TestLocalizerRepository:
    async def test_get(self) -> None:
        locale = "nl-NL"
        async with TemporaryDirectory() as assets_directory_path_str:
            assets_directory_path = Path(assets_directory_path_str)
            assets = AssetRepository(assets_directory_path)
            lc_messages_directory_path = assets_directory_path / "locale" / locale
            lc_messages_directory_path.mkdir(parents=True)
            po = """
# Dutch translations for PROJECT.
# Copyright (C) 2019 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2019.
#
msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2020-11-18 23:28+0000\n"
"PO-Revision-Date: 2019-10-05 11:38+0100\n"
"Last-Translator: \n"
"Language: nl\n"
"Language-Team: nl <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.7.0\n"95

#: betty/ancestry.py:457
msgid "Subject"
msgstr "Onderwerp"
"""
            async with aiofiles.open(lc_messages_directory_path / "betty.po", "w") as f:
                await f.write(po)
            sut = LocalizerRepository(assets)
            actual = (await sut.get(locale))._("Subject")
            assert actual == "Onderwerp"
