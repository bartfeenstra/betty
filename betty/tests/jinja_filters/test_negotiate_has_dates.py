from collections.abc import MutableMapping
from typing import Any, override

import pytest

from betty.attrs.date import HasDate
from betty.date import Date, DateExpression, DateRange
from betty.test_utils.conftest import AssertTemplateString


class _DummyHasDate(HasDate):
    def __init__(self, value: str, date: DateExpression | None = None):
        super().__init__(date=date)
        self.value = value

    @override
    def __str__(self) -> str:
        return self.value


class TestNegotiateHasDates:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": None,
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": None,
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1971, 1, 1)),
                        _DummyHasDate("Strawberry", Date(1970, 1, 1)),
                        _DummyHasDate("Banana", Date(1969, 1, 1)),
                        _DummyHasDate("Orange", Date(1972, 12, 31)),
                    ],
                    "date": DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
                },
            ),
        ],
    )
    async def test___call__(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        data: MutableMapping[str, Any],
    ) -> None:
        template = '{{ has_dates | negotiate_has_dates(date=date) or "" }}'
        async with assert_template_string(template=template, data=data) as (
            actual,
            _,
        ):
            assert actual == expected
