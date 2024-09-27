from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.date import Date
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity


class TestEnclosure(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Enclosure]:
        return Enclosure

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Enclosure(Place(), Place()),
        ]

    async def test_enclosee(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        assert sut.enclosee is enclosee

    async def test_encloser(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        assert sut.encloser is encloser

    async def test_date(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert sut.date is date

    async def test_citations(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert list(sut.citations) == [citation]
