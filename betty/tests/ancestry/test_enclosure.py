from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.date import Date
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity

import pytest


class TestEnclosure(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Enclosure(Place(), Place())

    def test_enclosee(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        assert sut.enclosee is enclosee

    def test_encloser(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        assert sut.encloser is encloser

    def test_date(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert sut.date is date

    def test_citations(self) -> None:
        enclosee = Place()
        encloser = Place()
        sut = Enclosure(enclosee, encloser)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert list(sut.citations) == [citation]
