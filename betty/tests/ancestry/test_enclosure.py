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
            Enclosure(),
        ]

    async def test_encloses(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.encloses is encloses

    async def test_enclosed_by(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.enclosed_by is enclosed_by

    async def test_date(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert sut.date is date

    async def test_citations(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert list(sut.citations) == [citation]
