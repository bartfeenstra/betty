from __future__ import annotations

from typing import Sequence, TYPE_CHECKING, cast

import pytest
from typing_extensions import override

from betty.date import Date, DateRange, Datey, DateySchema, DateSchema, DateRangeSchema
from betty.serde.dump import Dump, DumpMapping
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from betty.json.schema import Schema


_DUMMY_DATE_DUMPS: tuple[Sequence[DumpMapping[Dump]], Sequence[DumpMapping[Dump]]] = (
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
    Sequence[DumpMapping[Dump]], Sequence[DumpMapping[Dump]]
] = (
    [
        *[
            cast(DumpMapping[Dump], {"start": start, "end": None})
            for start in _DUMMY_DATE_DUMPS[0]
        ],
        *[
            cast(DumpMapping[Dump], {"start": None, "end": end})
            for end in _DUMMY_DATE_DUMPS[0]
        ],
        *[
            cast(DumpMapping[Dump], {"start": start, "end": end})
            for start in _DUMMY_DATE_DUMPS[0]
            for end in _DUMMY_DATE_DUMPS[0]
        ],
    ],
    [],
)

_DUMMY_DATEY_DUMPS: tuple[Sequence[DumpMapping[Dump]], Sequence[DumpMapping[Dump]]] = (
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

    def test_to_range_when_incomparable_should_raise(self) -> None:
        with pytest.raises(ValueError):  # noqa PT011
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
    def test___contains__(self, expected: bool, other: Datey) -> None:
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
    def test___lt__(self, expected: bool, sut: Date, other: Datey) -> None:
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
    def test___le__(self, expected: bool, sut: Date, other: Datey) -> None:
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
    def test___eq__(self, expected: bool, other: Datey) -> None:
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
    def test___ge__(self, expected: bool, sut: Date, other: Datey) -> None:
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
    def test___gt__(self, expected: bool, sut: Date, other: Datey) -> None:
        assert (sut > other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "year": 1970,
                    "month": 1,
                    "day": 1,
                    "iso8601": "1970-01-01",
                    "fuzzy": True,
                },
                Date(1970, 1, 1, True),
            ),
            (
                {
                    "fuzzy": True,
                },
                Date(None, None, None, True),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: Date
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


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

    _TEST_CONTAINS_PARAMETERS: Sequence[tuple[bool, Datey, Datey]] = [
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
    def test___contains__(self, expected: bool, other: Datey, sut: Datey) -> None:
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
    def test___lt___with_both_dates(
        self, expected: bool, sut: DateRange, other: Datey
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
    def test___le__(self, expected: bool, sut: DateRange, other: Datey) -> None:
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
    def test___eq__(self, expected: bool, other: Datey) -> None:
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
    def test___ge__(self, expected: bool, sut: DateRange, other: Datey) -> None:
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
    def test___gt__(self, expected: bool, other: Datey) -> None:
        assert (DateRange(Date(1970, 2, 2)) > other) == expected

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "start": {
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
                    },
                    "end": None,
                },
                DateRange(Date(1970, 1, 1)),
            ),
            (
                {
                    "start": None,
                    "end": {
                        "year": 2000,
                        "month": 12,
                        "day": 31,
                        "iso8601": "2000-12-31",
                        "fuzzy": False,
                    },
                },
                DateRange(None, Date(2000, 12, 31)),
            ),
            (
                {
                    "start": {
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
                    },
                    "end": {
                        "year": 2000,
                        "month": 12,
                        "day": 31,
                        "iso8601": "2000-12-31",
                        "fuzzy": False,
                    },
                },
                DateRange(Date(1970, 1, 1), Date(2000, 12, 31)),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: DateRange
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestDateSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(await DateSchema.new(), *_DUMMY_DATE_DUMPS)]


class TestDateRangeSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(await DateRangeSchema.new(), *_DUMMY_DATE_RANGE_DUMPS)]


class TestDateySchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(await DateySchema.new(), *_DUMMY_DATEY_DUMPS)]
