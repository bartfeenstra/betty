from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.locale.date import (
    Date,
    DateRange,
    Datey,
    DateySchema,
    DateSchema,
    DateRangeSchema,
)
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping
    from betty.json.schema import Schema


_DUMMY_DATE_DUMPS: Sequence[DumpMapping[Dump]] = (
    {},
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
        "year": 1970,
        "month": 1,
    },
    {
        "year": 1970,
        "day": 1,
    },
    {
        "month": 1,
        "day": 1,
    },
    {
        "year": 1970,
        "month": 1,
        "day": 1,
    },
    {
        "year": 1970,
        "month": 1,
        "day": 1,
        "fuzzy": True,
    },
)

_DUMMY_DATE_RANGE_DUMPS: Sequence[DumpMapping[Dump]] = tuple(
    {"start": start, "end": end}
    for start in _DUMMY_DATE_DUMPS
    for end in _DUMMY_DATE_DUMPS
)

_DUMMY_DATEY_DUMPS: Sequence[DumpMapping[Dump]] = (
    *_DUMMY_DATE_DUMPS,
    *_DUMMY_DATE_RANGE_DUMPS,
)


class TestDate:
    async def test_year(self) -> None:
        year = 1970
        sut = Date(year=year)
        assert year == sut.year

    async def test_month(self) -> None:
        month = 1
        sut = Date(month=month)
        assert month == sut.month

    async def test_day(self) -> None:
        day = 1
        sut = Date(day=day)
        assert day == sut.day

    async def test_fuzzy(self) -> None:
        fuzzy = True
        sut = Date()
        sut.fuzzy = fuzzy
        assert fuzzy == sut.fuzzy

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
    async def test_comparable(
        self, expected: bool, year: int | None, month: int | None, day: int | None
    ) -> None:
        sut = Date(year, month, day)
        assert expected == sut.comparable

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
    async def test_complete(
        self, expected: bool, year: int | None, month: int | None, day: int | None
    ) -> None:
        sut = Date(year, month, day)
        assert expected == sut.complete

    async def test_to_range_when_incomparable_should_raise(self) -> None:
        with pytest.raises(ValueError):  # noqa PT011
            Date(None, 1, 1).to_range()

    @pytest.mark.parametrize(
        ("year", "month", "day"),
        [
            (1970, 1, 1),
            (None, None, None),
        ],
    )
    async def test_parts(
        self, year: int | None, month: int | None, day: int | None
    ) -> None:
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
    async def test_in(self, expected: bool, other: Datey) -> None:
        assert expected == (other in Date(1970, 2, 2))

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (False, Date(1970, 2, 1)),
            (False, Date(1970, 2, 2)),
            (True, Date(1970, 2, 3)),
            (False, Date(1970)),
            (False, Date(1970, 2)),
            (True, Date(1971)),
            (True, Date(1970, 3)),
        ],
    )
    async def test___lt__(self, expected: bool, other: Datey) -> None:
        assert expected == (Date(1970, 2, 2) < other)

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
    async def test___eq__(self, expected: bool, other: Datey) -> None:
        assert expected == (Date(1970, 1, 1) == other)
        assert expected == (other == Date(1970, 1, 1))

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (True, Date(1970, 2, 1)),
            (False, Date(1970, 2, 2)),
            (False, Date(1970, 2, 3)),
        ],
    )
    async def test___gt__(self, expected: bool, other: Datey) -> None:
        assert expected == (Date(1970, 2, 2) > other)


class TestDateRange:
    _TEST_IN_PARAMETERS: list[tuple[bool, Datey, Datey]] = [
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
        _TEST_IN_PARAMETERS + [(x[0], x[2], x[1]) for x in _TEST_IN_PARAMETERS],
    )
    async def test_in(self, expected: bool, other: Datey, sut: Datey) -> None:
        assert expected == (other in sut)

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (False, Date(1970, 2, 1)),
            (False, Date(1970, 2, 2)),
            (True, Date(1970, 2, 3)),
            (False, DateRange(Date(1970, 2, 1))),
            (False, DateRange(Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 3))),
            (False, DateRange(None, Date(1970, 2, 1))),
            (False, DateRange(None, Date(1970, 2, 2))),
            (True, DateRange(None, Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
            (False, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
        ],
    )
    async def test___lt___with_start_date(self, expected: bool, other: Datey) -> None:
        assert expected == (DateRange(Date(1970, 2, 2)) < other)

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (False, Date(1970, 2, 1)),
            (True, Date(1970, 2, 2)),
            (True, Date(1970, 2, 3)),
            (False, DateRange(Date(1970, 2, 1))),
            (True, DateRange(Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 3))),
            (False, DateRange(None, Date(1970, 2, 1))),
            (False, DateRange(None, Date(1970, 2, 2))),
            (True, DateRange(None, Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
        ],
    )
    async def test___lt___with_end_date(self, expected: bool, other: Datey) -> None:
        assert expected == (DateRange(None, Date(1970, 2, 2)) < other)

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (False, Date(1970, 2, 1)),
            (True, Date(1970, 2, 2)),
            (True, Date(1970, 2, 3)),
            (False, DateRange(Date(1970, 1, 1))),
            (True, DateRange(Date(1970, 2, 1))),
            (True, DateRange(Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 3))),
            (False, DateRange(None, Date(1970, 2, 1))),
            (True, DateRange(None, Date(1970, 2, 2))),
            (True, DateRange(None, Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
            (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
            (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
        ],
    )
    async def test___lt___with_both_dates(self, expected: bool, other: Datey) -> None:
        assert expected == (DateRange(Date(1970, 2, 1), Date(1970, 2, 3)) < other)

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
    async def test___eq__(self, expected: bool, other: Datey) -> None:
        assert expected == (DateRange(Date(1970, 2, 2)) == other)

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
    async def test___gt__(self, expected: bool, other: Datey) -> None:
        assert expected == (DateRange(Date(1970, 2, 2)) > other)


class TestDateSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [(DateSchema(), _DUMMY_DATE_DUMPS)]


class TestDateRangeSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [(DateRangeSchema(), _DUMMY_DATE_RANGE_DUMPS)]


class TestDateySchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [(DateySchema(), _DUMMY_DATEY_DUMPS)]
