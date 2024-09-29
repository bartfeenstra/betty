from __future__ import annotations

from betty.ancestry.name import Name
from betty.date import Date
from betty.locale.localizer import DEFAULT_LOCALIZER


class TestName:
    async def test_date(self) -> None:
        date = Date()
        sut = Name(
            "Ikke",
            date=date,
        )
        assert sut.date is date

    async def test_name(self) -> None:
        name = "Ikke"
        sut = Name(name)
        assert sut.name.localize(DEFAULT_LOCALIZER) == name
