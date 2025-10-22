from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest

from betty.date import Date, DateLike, DateRange, IncompleteDateError
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER, LocalizerRepository
from betty.locale.translation import TranslationRepository

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from pytest_mock import MockerFixture


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
    async def test_format_date_range__with_incomplete_date_range(
        self, date_range: DateRange
    ) -> None:
        sut = DEFAULT_LOCALIZER
        with pytest.raises(IncompleteDateError):
            assert sut.format_date_range(date_range)

    _FORMAT_DATE_LIKE_TEST_PARAMETERS = (
        *_FORMAT_DATE_TEST_PARAMETERS,
        *_FORMAT_DATE_RANGE_TEST_PARAMETERS,
    )

    @pytest.mark.parametrize(
        ("expected", "date_like"), _FORMAT_DATE_LIKE_TEST_PARAMETERS
    )
    async def test_format_date_like(self, expected: str, date_like: DateLike) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.format_date_like(date_like) == expected

    async def test_format_datetime_datetime(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.format_datetime_datetime(datetime.datetime(1970, 1, 1))
            == "January 1, 1970"
        )

    async def test_locale(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.locale == DEFAULT_LOCALE

    async def test_locale_data(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.locale_data.language == "en"

    async def test__(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut._("My First Translatable String") == "My First Translatable String"

    async def test_gettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.gettext("My First Translatable String")
            == "My First Translatable String"
        )

    async def test_ngettext__with_singular(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 1
            )
            == "My First Translatable String"
        )

    async def test_ngettext__with_plural(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 9
            )
            == "My First Translatable Strings"
        )

    async def test_npgettext__with_singular(self) -> None:
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

    async def test_npgettext__with_plural(self) -> None:
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
    async def test_get(self, mocker: MockerFixture, tmp_path: Path) -> None:
        locale = "nl-NL"
        m_translations = mocker.MagicMock(spec=TranslationRepository)
        sut = LocalizerRepository(m_translations)
        localizer = sut.get(locale)
        assert localizer.locale == locale
        assert sut.get(locale) is localizer
