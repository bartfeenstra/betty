from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.attrs.date import HasAnyDate
from betty.date import Date, DateRange

if TYPE_CHECKING:
    from betty.associations.has_links import HasLinks
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestHasAnyDate:
    def test_date(self) -> None:
        sut = HasAnyDate()
        assert sut.date is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            # No date information.
            (
                {},
                HasAnyDate(),
            ),
            # A single date.
            (
                {
                    "fuzzy": True,
                },
                HasAnyDate(date=Date(None, None, None, fuzzy=True)),
            ),
            (
                {
                    "date": {
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
                    }
                },
                HasAnyDate(date=Date(1970, 1, 1)),
            ),
            # A date range with only a start date.
            (
                {
                    "date": {
                        "start": {
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": None,
                    },
                },
                HasAnyDate(date=DateRange(Date(1970, 1, 1))),
            ),
            # A date range with only an end date.
            (
                {
                    "date": {
                        "start": None,
                        "end": {
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
                        },
                    },
                },
                HasAnyDate(date=DateRange(None, Date(2000, 12, 31))),
            ),
            # A date range with both a start and an end date.
            (
                {
                    "date": {
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
                },
                HasAnyDate(date=DateRange(Date(1970, 1, 1), Date(2000, 12, 31))),
            ),
        ],
    )
    async def test_dump_linked_data(
        self,
        assert_dumps_linked_data: AssertDumpsLinkedData,
        expected: PortableMapping,
        sut: HasLinks,
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
