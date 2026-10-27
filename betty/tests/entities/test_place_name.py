from __future__ import annotations

from betty.date import Date
from betty.entities.place_name import PlaceName
from betty.localizables.plain import Plain


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
