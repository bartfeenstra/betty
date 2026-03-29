import pytest

from betty.date import Date, DateRange
from betty.date.linked_data import (
    dump_linked_data_for_date,
    dump_linked_data_for_date_range,
)
from betty.date.schema import DateRangeSchema, DateSchema
from betty.portable import PortableMapping
from betty.test_utils.conftest import AssertLinkedDataDump


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
            Date(1970, 1, 1, fuzzy=True),
        ),
        (
            {
                "fuzzy": True,
            },
            Date(None, None, None, fuzzy=True),
        ),
    ],
)
async def test_dump_linked_data_for_date(
    assert_linked_data_dump: AssertLinkedDataDump, expected: PortableMapping, sut: Date
) -> None:
    actual = await assert_linked_data_dump(DateSchema(), dump_linked_data_for_date(sut))
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
async def test_dump_linked_data_for_date_range(
    assert_linked_data_dump: AssertLinkedDataDump,
    expected: PortableMapping,
    sut: DateRange,
) -> None:
    actual = await assert_linked_data_dump(
        DateRangeSchema(), dump_linked_data_for_date_range(sut)
    )
    assert actual == expected
