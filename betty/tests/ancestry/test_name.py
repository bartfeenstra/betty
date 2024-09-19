from __future__ import annotations

from betty.ancestry.name import Name
from betty.date import Date


class TestName:
    async def test_date(self) -> None:
        date = Date()
        sut = Name(
            "Ikke",
            date=date,
        )
        assert sut.date is date
