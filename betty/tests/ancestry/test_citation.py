from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.source import Source
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import CountablePlain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity, EntityPlugin
from betty.privacy import Privacy
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityPluginTestBase, EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.plugin import PluginDefinition
import pytest


class TestCitationDefinition(EntityPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Citation.plugin


@EntityPlugin(
    "dummy-has-citations",
    label="",
    label_plural="",
    label_countable=CountablePlain("", ""),
)
class DummyHasCitations(HasCitations):
    pass


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

    async def test___init____with_facts(self) -> None:
        fact = DummyHasCitations()
        sut = Citation(source=Source(), facts=[fact])
        assert list(sut.facts) == [fact]

    async def test___init____with_location(self) -> None:
        location = "Somewhere"
        sut = Citation(source=Source(), location=location)
        assert sut.location is not None
        assert sut.location.localize(DEFAULT_LOCALIZER) == location

    async def test_id(self) -> None:
        citation_id = "C1"
        sut = Citation(
            id=citation_id,
            source=Source(),
        )
        assert sut.id == citation_id

    async def test_facts(self) -> None:
        fact = DummyHasCitations()
        sut = Citation(source=Source())
        assert list(sut.facts) == []
        sut.facts = [fact]
        assert list(sut.facts) == [fact]

    async def test_source(self) -> None:
        source = Source()
        sut = Citation(source=source)
        assert sut.source is source

    async def test_location(self) -> None:
        sut = Citation(source=Source())
        assert not sut.location
        location = "Somewhere"
        sut.location = location
        assert sut.location is not None
        assert sut.location.localize(DEFAULT_LOCALIZER) == location

    async def test_date(self) -> None:
        sut = Citation(source=Source())
        assert sut.date is None

    async def test_file_references(self) -> None:
        sut = Citation(source=Source())
        assert list(sut.file_references) == []

    async def test_private(self) -> None:
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
            "location": {DEFAULT_LOCALE: "My First Location"},
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
            private=True,
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
