from __future__ import annotations

from betty.ancestry.name import Name
from betty.date import Date
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.json.linked_data import assert_dumps_linked_data


class TestName:
    async def test_date(self) -> None:
        date = Date()
        sut = Name(
            plain("Ikke"),
            date=date,
        )
        assert sut.date is date

    async def test_name(self) -> None:
        name = "Ikke"
        sut = Name(plain(name))
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    async def test_dump_linked_data(self) -> None:
        sut = Name(plain("My First Name"))
        actual = await assert_dumps_linked_data(sut)
        assert actual == {"name": {DEFAULT_LOCALE: "My First Name"}}
