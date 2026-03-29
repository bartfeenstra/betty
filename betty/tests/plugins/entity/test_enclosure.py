from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.date import Date
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from betty.entity import Entity

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
