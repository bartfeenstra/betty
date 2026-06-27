from __future__ import annotations

from typing import TYPE_CHECKING, Final, cast

import pytest

from betty.attrs.date import (
    _dump_linked_data_for_date,
    _dump_linked_data_for_date_range,
)
from betty.date import Date, DateExpression, DateRange
from betty.json_schemas.date import DateRangeSchema, DateSchema
from betty.localizer import default_localizer
from betty.portable import PortableMapping

if TYPE_CHECKING:
    from collections.abc import Sequence

    from _pytest.mark.structures import MarkDecorator

    from betty.test_utils.conftest import AssertLinkedDataDump


type Pairs = Sequence[tuple[DateExpression, DateExpression]]
lt: Final[Pairs] = (
    # Both dates are full.
    (Date(1970, 1, 1), Date(1970, 1, 2)),
    (Date(1970, 1, 1), Date(1970, 2, 1)),
    (Date(1970, 1, 1), Date(1971, 1, 1)),
    # Left date is not full.
    # @todo
    # Right date is not full.
    # @todo
    # @todo
    # Date dates
    # Start date only.
    (DateRange(Date(1970, 2, 2)), Date(1970, 2, 3)),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
    (DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 3))),
    # End date only.
    (DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 2)),
    (DateRange(None, Date(1970, 2, 2)), Date(1970, 2, 3)),
    (DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
    (DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 3))),
    (
        DateRange(None, Date(1970, 2, 2)),
        DateRange(None, Date(1970, 2, 3)),
    ),
    (
        DateRange(None, Date(1970, 2, 2)),
        DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
    ),
    # Both dates.
    (DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 2)),
    (DateRange(Date(1970, 2, 1), Date(1970, 2, 3)), Date(1970, 2, 3)),
    (
        DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
        DateRange(Date(1970, 2, 1)),
    ),
    (
        DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
        DateRange(Date(1970, 2, 2)),
    ),
    (
        DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
        DateRange(Date(1970, 2, 3)),
    ),
    (
        DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
        DateRange(None, Date(1970, 2, 2)),
    ),
    (
        DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
        DateRange(None, Date(1970, 2, 3)),
    ),
    (
        DateRange(Date(1970, 2, 1), Date(1970, 2, 3)),
        DateRange(Date(1970, 2, 2), Date(1970, 2, 3)),
    ),
)

eq: Final[Pairs] = (
    (Date(1970, 1, 1), Date(1970, 1, 1)),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
)
neq: Final[Pairs] = (
    (Date(1970, 1, 1), Date(1970, 1, None)),
    (Date(1970, 1, 1), Date(1970, None, 1)),
    (Date(1970, 1, 1), Date(None, 1, 1)),
    (Date(1970, 1, 1), Date(1970, None, None)),
    (Date(1970, 1, 1), Date(None, 1, None)),
    (Date(1970, 1, 1), Date(None, None, 1)),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, None))),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(1970, None, 2))),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(None, 2, 2))),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(1970, None, None))),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(None, 2, None))),
    (DateRange(Date(1970, 2, 2)), DateRange(Date(None, None, 2))),
)

le: Final[Pairs] = (
    *lt,
    *eq,
)

gt: Final[Pairs] = ()

ge: Final[Pairs] = (
    *gt,
    *eq,
)


def parameterize_pairs[DateExpressionT: DateExpression](
    date: type[DateExpressionT], _pass: Pairs, fail: Pairs
) -> MarkDecorator:
    return pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            *((True, sut, other) for sut, other in _pass if isinstance(sut, date)),
            *((False, sut, other) for sut, other in fail if isinstance(sut, date)),
        ],
    )


date_dumps: Final[
    tuple[
        Sequence[PortableMapping],
        Sequence[PortableMapping],
    ]
] = (
    [
        {
            "year": 1970,
            "imprecise": False,
        },
        {
            "month": 1,
            "imprecise": False,
        },
        {
            "day": 1,
            "imprecise": False,
        },
        {
            "year": 1970,
            "month": 1,
            "imprecise": False,
        },
        {
            "year": 1970,
            "day": 1,
            "imprecise": False,
        },
        {
            "month": 1,
            "day": 1,
            "imprecise": False,
        },
        {
            "year": 1970,
            "month": 1,
            "day": 1,
            "imprecise": False,
        },
        {
            "year": 1970,
            "month": 1,
            "day": 1,
            "imprecise": True,
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
            "imprecise": "true",
        },
    ],
)

dummy_date_range_dumps: Final[
    tuple[
        Sequence[PortableMapping],
        Sequence[PortableMapping],
    ]
] = (
    [
        *[
            cast(PortableMapping, {"start": start, "end": None})
            for start in date_dumps[0]
        ],
        *[cast(PortableMapping, {"start": None, "end": end}) for end in date_dumps[0]],
        *[
            cast(PortableMapping, {"start": start, "end": end})
            for start in date_dumps[0]
            for end in date_dumps[0]
        ],
    ],
    [],
)

dummy_date_expression_dumps: Final[
    tuple[
        Sequence[PortableMapping],
        Sequence[PortableMapping],
    ]
] = (
    [*date_dumps[0], *dummy_date_range_dumps[0]],
    [*date_dumps[1], *dummy_date_range_dumps[1]],
)


class TestDate:
    def test_year(self) -> None:
        year = 1970
        sut = Date(year)
        assert sut.year == year

    def test_month(self) -> None:
        month = 1
        sut = Date(None, month)
        assert sut.month == month

    def test_day(self) -> None:
        day = 1
        sut = Date(None, None, day)
        assert sut.day == day

    def test_imprecise(self) -> None:
        assert Date(1, imprecise=True).imprecise
        assert not Date(1, imprecise=False).imprecise

    @parameterize_pairs(Date, lt, ge)
    def test___lt__(self, expected: bool, sut: Date, other: DateExpression) -> None:
        assert (sut < other) is expected

    @parameterize_pairs(Date, le, gt)
    def test___le__(self, expected: bool, sut: Date, other: DateExpression) -> None:
        assert (sut <= other) is expected

    @parameterize_pairs(Date, eq, neq)
    def test___eq__(self, expected: bool, sut: Date, other: DateExpression) -> None:
        assert (sut == other) is expected

    @parameterize_pairs(Date, ge, lt)
    def test___ge__(self, expected: bool, sut: Date, other: DateExpression) -> None:
        assert (sut >= other) is expected

    @parameterize_pairs(Date, gt, le)
    def test___gt__(self, expected: bool, sut: Date, other: DateExpression) -> None:
        assert (sut > other) is expected

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            # Dates that cannot be formatted.
            ("day 1 of the month", Date(None, None, 1)),
            # Single dates.
            ("January", Date(None, 1, None)),
            ("around January", Date(None, 1, None, imprecise=True)),
            ("1970", Date(1970, None, None)),
            ("around 1970", Date(1970, None, None, imprecise=True)),
            ("January, 1970", Date(1970, 1, None)),
            ("around January, 1970", Date(1970, 1, None, imprecise=True)),
            ("January 1, 1970", Date(1970, 1, 1)),
            ("around January 1, 1970", Date(1970, 1, 1, imprecise=True)),
            ("January 1", Date(None, 1, 1)),
            ("around January 1", Date(None, 1, 1, imprecise=True)),
        ],
    )
    async def test_localize(self, expected: str, sut: Date) -> None:
        assert sut.localize(default_localizer) == expected

    def test_load__with_year(self) -> None:
        assert Date.data().porter.load({"year": 9}).year == 9

    def test_load__with_month(self) -> None:
        assert Date.data().porter.load({"month": 9}).month == 9

    def test_load__with_day(self) -> None:
        assert Date.data().porter.load({"day": 9}).day == 9

    def test_load__with_imprecise(self) -> None:
        assert Date.data().porter.load({"imprecise": True, "year": 9}).imprecise

    def test_dump__with_year(self) -> None:
        assert Date.data().porter.dump(Date(9)) == {"year": 9}

    def test_dump__with_month(self) -> None:
        assert Date.data().porter.dump(Date(None, 9)) == {"month": 9}

    def test_dump__with_day(self) -> None:
        assert Date.data().porter.dump(Date(None, None, 9)) == {"day": 9}

    def test_dump__with_imprecise(self) -> None:
        assert Date.data().porter.dump(Date(9, imprecise=True)) == {
            "imprecise": True,
            "year": 9,
        }


class TestDateRange:
    @parameterize_pairs(DateRange, lt, ge)
    def test___lt__(
        self, expected: bool, sut: DateRange, other: DateExpression
    ) -> None:
        assert (sut < other) is expected

    @parameterize_pairs(DateRange, le, gt)
    def test___le__(
        self, expected: bool, sut: DateRange, other: DateExpression
    ) -> None:
        assert (sut <= other) is expected

    @parameterize_pairs(DateRange, eq, neq)
    def test___eq__(
        self, expected: bool, sut: DateRange, other: DateExpression
    ) -> None:
        assert (sut == other) is expected

    @parameterize_pairs(DateRange, ge, lt)
    def test___ge__(
        self, expected: bool, sut: DateRange, other: DateExpression
    ) -> None:
        assert (sut >= other) is expected

    @parameterize_pairs(DateRange, gt, le)
    def test___gt__(
        self, expected: bool, sut: DateRange, other: DateExpression
    ) -> None:
        assert (DateRange(Date(1970, 2, 2)) > other) is expected

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
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31, imprecise=True)),
        ),
        (
            "from January 1, 1970 until sometime before around December 31, 1999",
            DateRange(
                Date(1970, 1, 1),
                Date(1999, 12, 31, imprecise=True),
                end_is_boundary=True,
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
                Date(1970, 1, 1),
                Date(1999, 12, 31, imprecise=True),
                start_is_boundary=True,
            ),
        ),
        (
            "sometime between January 1, 1970 and around December 31, 1999",
            DateRange(
                Date(1970, 1, 1),
                Date(1999, 12, 31, imprecise=True),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        (
            "from around January 1, 1970 until December 31, 1999",
            DateRange(Date(1970, 1, 1, imprecise=True), Date(1999, 12, 31)),
        ),
        (
            "from around January 1, 1970 until sometime before December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True),
                Date(1999, 12, 31),
                end_is_boundary=True,
            ),
        ),
        (
            "from around January 1, 1970 until around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True), Date(1999, 12, 31, imprecise=True)
            ),
        ),
        (
            "from around January 1, 1970 until sometime before around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True),
                Date(1999, 12, 31, imprecise=True),
                end_is_boundary=True,
            ),
        ),
        (
            "from sometime after around January 1, 1970 until December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True),
                Date(1999, 12, 31),
                start_is_boundary=True,
            ),
        ),
        (
            "sometime between around January 1, 1970 and December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True),
                Date(1999, 12, 31),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        (
            "from sometime after around January 1, 1970 until around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True),
                Date(1999, 12, 31, imprecise=True),
                start_is_boundary=True,
            ),
        ),
        (
            "sometime between around January 1, 1970 and around December 31, 1999",
            DateRange(
                Date(1970, 1, 1, imprecise=True),
                Date(1999, 12, 31, imprecise=True),
                start_is_boundary=True,
                end_is_boundary=True,
            ),
        ),
        ("from January 1, 1970", DateRange(Date(1970, 1, 1))),
        (
            "sometime after January 1, 1970",
            DateRange(Date(1970, 1, 1), start_is_boundary=True),
        ),
        ("from around January 1, 1970", DateRange(Date(1970, 1, 1, imprecise=True))),
        (
            "sometime after around January 1, 1970",
            DateRange(Date(1970, 1, 1, imprecise=True), start_is_boundary=True),
        ),
        ("until December 31, 1999", DateRange(None, Date(1999, 12, 31))),
        (
            "sometime before December 31, 1999",
            DateRange(None, Date(1999, 12, 31), end_is_boundary=True),
        ),
        (
            "until around December 31, 1999",
            DateRange(None, Date(1999, 12, 31, imprecise=True)),
        ),
        (
            "sometime before around December 31, 1999",
            DateRange(None, Date(1999, 12, 31, imprecise=True), end_is_boundary=True),
        ),
    ]

    @pytest.mark.parametrize(("expected", "sut"), _FORMAT_DATE_RANGE_TEST_PARAMETERS)
    async def test_localize(self, expected: str, sut: DateRange) -> None:
        assert sut.localize(default_localizer) == expected


@pytest.mark.parametrize(
    ("expected", "sut"),
    [
        (
            {
                "year": 1970,
                "month": 1,
                "day": 1,
                "date": "1970-01-01",
                "imprecise": True,
            },
            Date(1970, 1, 1, imprecise=True),
        ),
        (
            {
                "year": 1970,
                "imprecise": True,
            },
            Date(1, None, None, imprecise=True),
        ),
    ],
)
async def test__dump_linked_data_for_date(
    assert_linked_data_dump: AssertLinkedDataDump, expected: PortableMapping, sut: Date
) -> None:
    actual = await assert_linked_data_dump(
        DateSchema(), _dump_linked_data_for_date(sut)
    )
    assert actual == expected


@pytest.mark.parametrize(
    ("expected", "sut"),
    [
        (
            {
                "start": {
                    "year": 1970,
                    "month": 1,
                    "day": 1,
                    "date": "1970-01-01",
                    "imprecise": False,
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
                    "date": "2000-12-31",
                    "imprecise": False,
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
                    "date": "1970-01-01",
                    "imprecise": False,
                },
                "end": {
                    "year": 2000,
                    "month": 12,
                    "day": 31,
                    "date": "2000-12-31",
                    "imprecise": False,
                },
            },
            DateRange(Date(1970, 1, 1), Date(2000, 12, 31)),
        ),
    ],
)
async def test__dump_linked_data_for_date_range(
    assert_linked_data_dump: AssertLinkedDataDump,
    expected: PortableMapping,
    sut: DateRange,
) -> None:
    actual = await assert_linked_data_dump(
        DateRangeSchema(), _dump_linked_data_for_date_range(sut)
    )
    assert actual == expected
