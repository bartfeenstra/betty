from __future__ import annotations

from typing import TYPE_CHECKING

from betty.date import Date
from betty.entities.place_name import PlaceName
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestPlaceName:
    def test_date(self) -> None:
        date = Date()
        sut = PlaceName(
            "Ikke",
            date=date,
        )
        assert sut.date is date

    def test_name(self) -> None:
        name = Plain("Ikke")
        sut = PlaceName(name)
        assert sut.name is name

    async def test_dump_linked_data(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        sut = PlaceName("My First Name")
        actual = await assert_dumps_linked_data(sut)
        assert actual == {
            "id": sut.id,
            "name": {DEFAULT_LOCALE_TAG: "My First Name"},
        }
