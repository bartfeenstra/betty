from __future__ import annotations

from betty.ancestry.name import Name
from betty.date import Date
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable import Plain
from betty.test_utils.json.linked_data import assert_dumps_linked_data


class TestName:
    async def test_date(self) -> None:
        date = Date()
        sut = Name(
            "Ikke",
            date=date,
        )
        assert sut.date is date

    async def test_name(self) -> None:
        name = Plain("Ikke")
        sut = Name(name)
        assert sut.name is name

    async def test_dump_linked_data(self) -> None:
        sut = Name("My First Name")
        actual = await assert_dumps_linked_data(sut)
        assert actual == {"name": {DEFAULT_LOCALE_TAG: "My First Name"}}
