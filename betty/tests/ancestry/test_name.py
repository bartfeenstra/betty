from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.name import Name
from betty.date import Date
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestName:
    def test_date(self) -> None:
        date = Date()
        sut = Name(
            "Ikke",
            date=date,
        )
        assert sut.date is date

    def test_name(self) -> None:
        name = Plain("Ikke")
        sut = Name(name)
        assert sut.name is name

    async def test_dump_linked_data(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        sut = Name("My First Name")
        actual = await assert_dumps_linked_data(sut)
        assert actual == {"name": {DEFAULT_LOCALE_TAG: "My First Name"}}
