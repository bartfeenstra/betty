from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from betty.date import AnyDate, Date, DateRange, IncompleteDateError
from betty.localizer import default_localizer
from betty.portable import PortableMapping

if TYPE_CHECKING:
    from collections.abc import Sequence


_DUMMY_DATE_DUMPS: tuple[
    Sequence[PortableMapping],
    Sequence[PortableMapping],
] = (
    [
        {
            "year": 1970,
            "fuzzy": False,
        },
        {
            "month": 1,
            "fuzzy": False,
        },
        {
            "day": 1,
            "fuzzy": False,
        },
        {
            "year": 1970,
            "month": 1,
            "fuzzy": False,
        },
        {
            "year": 1970,
            "day": 1,
            "fuzzy": False,
        },
        {
            "month": 1,
            "day": 1,
            "fuzzy": False,
        },
        {
            "year": 1970,
            "month": 1,
            "day": 1,
            "fuzzy": False,
        },
        {
            "year": 1970,
            "month": 1,
            "day": 1,
            "fuzzy": True,
        },
    ],
    [
        {
            "year": 1970,
        },
        {
            "month": 1,
        },
        {
            "day": 1,
        },
        {
            "fuzzy": "true",
        },
    ],
)

_DUMMY_DATE_RANGE_DUMPS: tuple[
    Sequence[PortableMapping],
    Sequence[PortableMapping],
] = (
    [
        *[
            cast(PortableMapping, {"start": start, "end": None})
            for start in _DUMMY_DATE_DUMPS[0]
        ],
        *[
            cast(PortableMapping, {"start": None, "end": end})
            for end in _DUMMY_DATE_DUMPS[0]
        ],
        *[
            cast(PortableMapping, {"start": start, "end": end})
            for start in _DUMMY_DATE_DUMPS[0]
            for end in _DUMMY_DATE_DUMPS[0]
        ],
    ],
    [],
)

_DUMMY_ANY_DATE_DUMPS: tuple[
    Sequence[PortableMapping],
    Sequence[PortableMapping],
] = (
    [*_DUMMY_DATE_DUMPS[0], *_DUMMY_DATE_RANGE_DUMPS[0]],
    [*_DUMMY_DATE_DUMPS[1], *_DUMMY_DATE_RANGE_DUMPS[1]],
)


class TestDate:
    def test_year(self) -> None:
        year = 1970
        sut = Date(year=year)
        assert sut.year == year

    def test_month(self) -> None:
        month = 1
        sut = Date(month=month)
        assert sut.month == month

    def test_day(self) -> None:
        day = 1
        sut = Date(day=day)
        assert sut.day == day

    def test_fuzzy(self) -> None:
        fuzzy = True
        sut = Date()
        sut.fuzzy = fuzzy
        assert sut.fuzzy == fuzzy

    @pytest.mark.parametrize(
        ("expected", "year", "month", "day"),
        [
            (True, 1970, 1, 1),
            (False, None, 1, 1),
            (True, 1970, None, 1),
            (True, 1970, 1, None),
            (False, None, None, 1),
            (True, 1970, None, None),
            (False, None, None, None),
        ],
    )
    def test_comparable(
        self, expected: bool, year: int | None, month: int | None, day: int | None
    ) -> None:
        sut = Date(year, month, day)
        assert sut.comparable == expected

    @pytest.mark.parametrize(
        ("expected", "year", "month", "day"),
        [
            (True, 1970, 1, 1),
            (False, None, 1, 1),
            (False, 1970, None, 1),
            (False, 1970, 1, None),
            (False, None, None, 1),
            (False, 1970, None, None),
            (False, None, None, None),
        ],
    )
    def test_complete(
        self, expected: bool, year: int | None, month: int | None, day: int | None
    ) -> None:
        sut = Date(year, month, day)
        assert sut.complete == expected

    def test_to_range__when_incomparable_should_raise(self) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            Date(None, 1, 1).to_range()

    @pytest.mark.parametrize(
        ("year", "month", "day"),
        [
            (1970, 1, 1),
            (None, None, None),
        ],
    )
    def test_parts(self, year: int | None, month: int | None, day: int | None) -> None:
        assert (year, month, day) == Date(year, month, day).parts

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (False, Date(1970, 2, 1)),
            (True, Date(1970, 2, 2)),
            (False, Date(1970, 2, 3)),
            (False, DateRange()),
        ],
    )
    def test___contains__(self, expected: bool, other: AnyDate) -> None:
        assert (other in Date(1970, 2, 2)) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            (False, Date(1970, 2, 2), Date(1970, 2, 1)),
            (False, Date(1970, 2, 2), Date(1970, 2, 2)),
            (True, Date(1970, 2, 2), Date(1970, 2, 3)),
            (False, Date(1970, 2, 2), Date(1970)),
            (False, Date(1970, 2, 2), Date(1970, 2)),
            (True, Date(1970, 2, 2), Date(1971)),
            (True, Date(1970, 2, 2), Date(1970, 3)),
        ],
    )
    def test___lt__(self, expected: bool, sut: Date, other: AnyDate) -> None:
        assert (sut < other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            (False, Date(1970, 2, 2), Date(1970, 2, 1)),
            (True, Date(1970, 2, 2), Date(1970, 2, 2)),
            (True, Date(1970, 2, 2), Date(1970, 2, 3)),
            (False, Date(1970, 2, 2), Date(1970)),
            (False, Date(1970, 2, 2), Date(1970, 2)),
            (True, Date(1970, 2, 2), Date(1971)),
            (True, Date(1970, 2, 2), Date(1970, 3)),
        ],
    )
    def test___le__(self, expected: bool, sut: Date, other: AnyDate) -> None:
        assert (sut <= other) == expected

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (True, Date(1970, 1, 1)),
            (False, Date(1970, 1, None)),
            (False, Date(1970, None, 1)),
            (False, Date(None, 1, 1)),
            (False, Date(1970, None, None)),
            (False, Date(None, 1, None)),
            (False, Date(None, None, 1)),
            (False, None),
        ],
    )
    def test___eq__(self, expected: bool, other: AnyDate) -> None:
        assert (Date(1970, 1, 1) == other) == expected
        assert (other == Date(1970, 1, 1)) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            (True, Date(1970, 2, 2), Date(1970, 2, 1)),
            (True, Date(1970, 2, 2), Date(1970, 2, 2)),
            (False, Date(1970, 2, 2), Date(1970, 2, 3)),
            (True, Date(1970, 2, 2), Date(1970)),
            (True, Date(1970, 2, 2), Date(1970, 2)),
            (False, Date(1970, 2, 2), Date(1971)),
            (False, Date(1970, 2, 2), Date(1970, 3)),
        ],
    )
    def test___ge__(self, expected: bool, sut: Date, other: AnyDate) -> None:
        assert (sut >= other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            (True, Date(1970, 2, 2), Date(1970, 2, 1)),
            (False, Date(1970, 2, 2), Date(1970, 2, 2)),
            (False, Date(1970, 2, 2), Date(1970, 2, 3)),
            (True, Date(1970, 2, 2), Date(1970)),
            (True, Date(1970, 2, 2), Date(1970, 2)),
            (False, Date(1970, 2, 2), Date(1971)),
            (False, Date(1970, 2, 2), Date(1970, 3)),
        ],
    )
    def test___gt__(self, expected: bool, sut: Date, other: AnyDate) -> None:
        assert (sut > other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
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
        ],
    )
    async def test_localize(self, expected: str, sut: Date) -> None:
        assert sut.localize(default_localizer) == expected

    def test_load__minimal(self) -> None:
        Date.data().porter.load({})

    def test_load__with_year(self) -> None:
        assert Date.data().porter.load({"year": 9}).year == 9

    def test_load__with_month(self) -> None:
        assert Date.data().porter.load({"month": 9}).month == 9

    def test_load__with_day(self) -> None:
        assert Date.data().porter.load({"day": 9}).day == 9

    def test_load__with_fuzzy(self) -> None:
        assert Date.data().porter.load({"fuzzy": True}).fuzzy

    def test_dump__minimal(self) -> None:
        assert Date.data().porter.dump(Date()) == {}

    def test_dump__with_year(self) -> None:
        assert Date.data().porter.dump(Date(year=9)) == {"year": 9}

    def test_dump__with_month(self) -> None:
        assert Date.data().porter.dump(Date(month=9)) == {"month": 9}

    def test_dump__with_day(self) -> None:
        assert Date.data().porter.dump(Date(day=9)) == {"day": 9}

    def test_dump__with_fuzzy(self) -> None:
        assert Date.data().porter.dump(Date(fuzzy=True)) == {"fuzzy": True}


class TestDateRange:
    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (False, DateRange()),
            (False, DateRange(Date(), None)),
            (True, DateRange(Date(1970), None)),
            (False, DateRange(Date(None, 1), None)),
            (False, DateRange(Date(None, None, 1), None)),
            (False, DateRange(None, Date())),
            (True, DateRange(None, Date(1970))),
            (False, DateRange(None, Date(None, 1))),
            (False, DateRange(None, Date(None, None, 1))),
            (False, DateRange(Date(), Date())),
            (True, DateRange(Date(1970), Date())),
            (True, DateRange(Date(), Date(1970))),
        ],
    )
    def test_comparable(self, expected: bool, sut: DateRange) -> None:
        assert sut.comparable == expected

    _TEST_CONTAINS_PARAMETERS: Sequence[tuple[bool, AnyDate, AnyDate]] = [
        (False, Date(1970, 2, 2), DateRange()),
        (False, Date(1970, 2), DateRange()),
        (False, Date(1970), DateRange()),
        (False, Date(1970, 2, 1), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 2), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 3), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 1), DateRange(None, Date(1970, 2, 2))),
        (True, Date(1970, 2, 2), DateRange(None, Date(1970, 2, 2))),
        (False, Date(1970, 2, 3), DateRange(None, Date(1970, 2, 2))),
        (False, Date(1969, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, Date(1970, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, Date(1971, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3)), DateRange(Date(1970, 2, 2))),
        (False, DateRange(None, Date(1970, 2, 1)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 3)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 1)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3)), DateRange(None, Date(1970, 2, 2))),
        (
            True,
            DateRange(Date(1969, 2, 1)),
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
        ),
        (
            True,
            DateRange(Date(1970, 2, 1)),
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
        ),
        (
            False,
            DateRange(Date(1971, 2, 1)),
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
        ),
        (
            False,
            DateRange(None, Date(1969, 2, 1)),
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
        ),
        (
            True,
            DateRange(None, Date(1970, 2, 1)),
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
        ),
        (
            True,
            DateRange(None, Date(1971, 2, 1)),
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
        ),
        (
            False,
            DateRange(Date(1969, 2, 2), Date(1970, 2, 2)),
            DateRange(Date(1971, 2, 2), Date(1972, 2, 2)),
        ),
        (
            True,
            DateRange(Date(1969, 2, 2), Date(1971, 2, 2)),
            DateRange(Date(1970, 2, 2), Date(1972, 2, 2)),
        ),
        (
            True,
            DateRange(Date(1970, 2, 2), Date(1971, 2, 2)),
            DateRange(Date(1969, 2, 2), Date(1972, 2, 2)),
        ),
    ]

    # Mirror the arguments because we want the containment check to work in either direction.
    @pytest.mark.parametrize(
        ("expected", "other", "sut"),
        _TEST_CONTAINS_PARAMETERS
        + [(x[0], x[2], x[1]) for x in _TEST_CONTAINS_PARAMETERS],
    )
    def test___contains__(self, expected: bool, other: AnyDate, sut: AnyDate) -> None:
        assert (other in sut) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            # Start date only.
            (False, DateRange(Date(1970, 2, 2)), Date(1970, 2, 1)),
            (False, DateRange(Date(1970, 2, 2)), Date(1970, 2, 2)),
            (True, DateRange(Date(1970, 2, 2)), Date(1970, 2, 3)),
            (False, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 1))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 1))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 3))),
            (
                False,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
            # End date only.
            (False, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 1)),
            (True, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 2)),
            (True, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 3)),
            (False, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 1))),
            (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
            (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 1)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
            # Both dates.
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 1)),
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 2)),
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 3)),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 1, 1)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 1)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
        ],
    )
    def test___lt____with_both_dates(
        self, expected: bool, sut: DateRange, other: AnyDate
    ) -> None:
        assert (sut < other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            # Start date only.
            (False, DateRange(Date(1970, 2, 2)), Date(1970, 2, 1)),
            (False, DateRange(Date(1970, 2, 2)), Date(1970, 2, 2)),
            (True, DateRange(Date(1970, 2, 2)), Date(1970, 2, 3)),
            (False, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 1))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 1))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 3))),
            (
                False,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
            # End date only.
            (False, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 1)),
            (True, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 2)),
            (True, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 3)),
            (False, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 1))),
            (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
            (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 1)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
            # Both dates.
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 1)),
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 2)),
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 3)),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 1, 1)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 1)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 3)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
        ],
    )
    def test___le__(self, expected: bool, sut: DateRange, other: AnyDate) -> None:
        assert (sut <= other) == expected

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (True, DateRange(Date(1970, 2, 2))),
            (False, DateRange(Date(1970, 2, None))),
            (False, DateRange(Date(1970, None, 2))),
            (False, DateRange(Date(None, 2, 2))),
            (False, DateRange(Date(1970, None, None))),
            (False, DateRange(Date(None, 2, None))),
            (False, DateRange(Date(None, None, 2))),
            (False, None),
        ],
    )
    def test___eq__(self, expected: bool, other: AnyDate) -> None:
        assert (DateRange(Date(1970, 2, 2)) == other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            # Start date only.
            (True, DateRange(Date(1970, 2, 2)), Date(1970, 2, 1)),
            (True, DateRange(Date(1970, 2, 2)), Date(1970, 2, 2)),
            (False, DateRange(Date(1970, 2, 2)), Date(1970, 2, 3)),
            (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 1))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 1))),
            (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
            (False, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 3))),
            (
                True,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
            # End date only.
            (True, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 1)),
            (False, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 2)),
            (False, DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 3)),
            (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 1))),
            (False, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
            (False, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 1)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(None, Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(None, Date(1970, 2, 2)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
            # Both dates.
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 1)),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 2)),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 3)),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 1, 1)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 1)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(None, Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 2)),
            ),
            (
                False,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
            ),
            (
                True,
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
                DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
            ),
        ],
    )
    def test___ge__(self, expected: bool, sut: DateRange, other: AnyDate) -> None:
        assert (sut >= other) == expected

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (True, Date(1970, 2, 1)),
            (True, Date(1970, 2, 2)),
            (False, Date(1970, 2, 3)),
            (True, DateRange(Date(1970, 2, 1))),
            (False, DateRange(Date(1970, 2, 2))),
            (False, DateRange(Date(1970, 2, 3))),
            (True, DateRange(None, Date(1970, 2, 1))),
            (True, DateRange(None, Date(1970, 2, 2))),
            (False, DateRange(None, Date(1970, 2, 3))),
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
            (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
        ],
    )
    def test___gt__(self, expected: bool, other: AnyDate) -> None:
        assert (DateRange(Date(1970, 2, 2)) > other) == expected

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

    @pytest.mark.parametrize(("expected", "sut"), _FORMAT_DATE_RANGE_TEST_PARAMETERS)
    async def test_localize(self, expected: str, sut: DateRange) -> None:
        assert sut.localize(default_localizer) == expected

    @pytest.mark.parametrize(
        "sut",
        [
            DateRange(),
            DateRange(Date()),
            DateRange(None, Date()),
            DateRange(Date(), Date()),
        ],
    )
    async def test_localize__with_incomplete_date_range(self, sut: DateRange) -> None:
        with pytest.raises(IncompleteDateError):
            assert sut.localize(default_localizer)
