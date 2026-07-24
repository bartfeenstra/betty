from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.attrs.date import HasDate
from betty.date import Date, DateRange

if TYPE_CHECKING:
    from betty.associations.has_links import HasLinks
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class DummyHasDateWithContextDefinitions(HasDate):
    @override
    def has_date_linked_data_contexts(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        return "single-date", "start-date", "end-date"


class TestHasDate:
    def test_date(self) -> None:
        sut = HasDate()
        assert sut.date is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            # No date information.
            (
                {},
                HasDate(),
            ),
            (
                {},
                DummyHasDateWithContextDefinitions(),
            ),
            # A single date.
            (
                {
                    "date": {
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "date": "1970-01-01",
                        "imprecise": False,
                    }
                },
                HasDate(date=Date(1970, 1, 1)),
            ),
            (
                {
                    "date": {
                        "@context": {"date": "single-date"},
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "date": "1970-01-01",
                        "imprecise": False,
                    }
                },
                DummyHasDateWithContextDefinitions(date=Date(1970, 1, 1)),
            ),
            # A date range with only a start date.
            (
                {
                    "date": {
                        "start": {
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "date": "1970-01-01",
                            "imprecise": False,
                        },
                        "end": None,
                    },
                },
                HasDate(date=DateRange(Date(1970, 1, 1))),
            ),
            (
                {
                    "date": {
                        "start": {
                            "@context": {"date": "start-date"},
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "date": "1970-01-01",
                            "imprecise": False,
                        },
                        "end": None,
                    },
                },
                DummyHasDateWithContextDefinitions(date=DateRange(Date(1970, 1, 1))),
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
                            "date": "2000-12-31",
                            "imprecise": False,
                        },
                    },
                },
                HasDate(date=DateRange(None, Date(2000, 12, 31))),
            ),
            (
                {
                    "date": {
                        "start": None,
                        "end": {
                            "@context": {"date": "end-date"},
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "date": "2000-12-31",
                            "imprecise": False,
                        },
                    },
                },
                DummyHasDateWithContextDefinitions(
                    date=DateRange(None, Date(2000, 12, 31))
                ),
            ),
            # A date range with both a start and an end date.
            (
                {
                    "date": {
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
                },
                HasDate(date=DateRange(Date(1970, 1, 1), Date(2000, 12, 31))),
            ),
            (
                {
                    "date": {
                        "start": {
                            "@context": {"date": "start-date"},
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "date": "1970-01-01",
                            "imprecise": False,
                        },
                        "end": {
                            "@context": {"date": "end-date"},
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "date": "2000-12-31",
                            "imprecise": False,
                        },
                    },
                },
                DummyHasDateWithContextDefinitions(
                    date=DateRange(Date(1970, 1, 1), Date(2000, 12, 31))
                ),
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
