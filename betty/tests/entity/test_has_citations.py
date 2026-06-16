from __future__ import annotations

from betty.entities.citation import Citation
from betty.entities.source import Source
from betty.test_utils.ancestry.has_citations import DummyHasCitations


class TestHasCitations:
    def test_citations(self) -> None:
        citation = Citation(source=Source())
        sut = DummyHasCitations(citations=[citation])
        assert list(sut.citations) == [citation]
