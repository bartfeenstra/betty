from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.model import Entity
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.event import Event
from betty.plugins.entity.source import Source
from betty.plugins.event_type.birth import Birth
from betty.privacy import Privacy
from betty.test_utils.ancestry.has_citations import DummyHasCitations
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
import pytest


class TestCitation(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            Citation(source=Source()),
            Citation(source=Source(), location="My First Location"),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test___init____with_facts(self) -> None:
        fact = DummyHasCitations()
        sut = Citation(source=Source(), facts=[fact])
        assert list(sut.facts) == [fact]

    def test___init____with_location(self) -> None:
        location = "Somewhere"
        sut = Citation(source=Source(), location=location)
        assert sut.location is not None
        assert sut.location.localize(DEFAULT_LOCALIZER) == location

    def test_id(self) -> None:
        citation_id = "C1"
        sut = Citation(
            id=citation_id,
            source=Source(),
        )
        assert sut.id == citation_id

    def test_facts(self) -> None:
        fact = DummyHasCitations()
        sut = Citation(source=Source())
        assert list(sut.facts) == []
        sut.facts = [fact]
        assert list(sut.facts) == [fact]

    def test_source(self) -> None:
        source = Source()
        sut = Citation(source=source)
        assert sut.source is source

    def test_location(self) -> None:
        sut = Citation(source=Source())
        assert not sut.location
        location = "Somewhere"
        sut.location = location
        assert sut.location is not None
        assert sut.location.localize(DEFAULT_LOCALIZER) == location

    def test_date(self) -> None:
        sut = Citation(source=Source())
        assert sut.date is None

    def test_file_references(self) -> None:
        sut = Citation(source=Source())
        assert list(sut.file_references) == []

    def test_private(self) -> None:
        sut = Citation(source=Source())
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data__should_dump_minimal(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(name="The Source"),
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "facts": [],
            "links": [],
            "fileReferences": [],
            "source": None,
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(
                id="the_source",
                name="The Source",
            ),
            location="My First Location",
        )
        citation.facts.add(
            Event(
                id="the_event",
                event_type=Birth(),
            )
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "location": {DEFAULT_LOCALE_TAG: "My First Location"},
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [],
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(
                id="the_source",
                name="The Source",
            ),
            privacy=Privacy.PRIVATE,
        )
        citation.facts.add(
            Event(
                id="the_event",
                event_type=Birth(),
            )
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": True,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [],
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected
