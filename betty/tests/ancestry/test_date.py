from __future__ import annotations

import pytest

from betty.date import Date, DateRange
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.tests.ancestry.test___init__ import DummyHasDateWithContextDefinitions
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.ancestry.link import HasLinks


class TestHasDate:
    async def test_date(self) -> None:
        sut = DummyHasDate()
        assert sut.date is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            # No date information.
            (
                {},
                DummyHasDate(),
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
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
                    }
                },
                DummyHasDate(date=Date(1970, 1, 1)),
            ),
            (
                {
                    "date": {
                        "@context": {"iso8601": "single-date"},
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
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
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": None,
                    },
                },
                DummyHasDate(date=DateRange(Date(1970, 1, 1))),
            ),
            (
                {
                    "date": {
                        "start": {
                            "@context": {"iso8601": "start-date"},
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
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
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
                        },
                    },
                },
                DummyHasDate(date=DateRange(None, Date(2000, 12, 31))),
            ),
            (
                {
                    "date": {
                        "start": None,
                        "end": {
                            "@context": {"iso8601": "end-date"},
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
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
                DummyHasDate(date=DateRange(Date(1970, 1, 1), Date(2000, 12, 31))),
            ),
            (
                {
                    "date": {
                        "start": {
                            "@context": {"iso8601": "start-date"},
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": {
                            "@context": {"iso8601": "end-date"},
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
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
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
