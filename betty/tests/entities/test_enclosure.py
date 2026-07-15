from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.date import Date
from betty.entities.citation import Citation
from betty.entities.enclosure import Enclosure
from betty.entities.place import Place
from betty.entities.source import Source
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from betty.entity import Entity

import pytest


class TestEnclosure(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Enclosure(encloses=Place(), enclosed_by=Place())

    def test_encloses(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.encloses is encloses

    def test_enclosed_by(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.enclosed_by is enclosed_by

    def test_date(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert sut.date is date

    def test_citations(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert list(sut.citations) == [citation]
