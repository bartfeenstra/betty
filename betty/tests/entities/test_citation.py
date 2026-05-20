from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.source import Source
from betty.entity import Entity
from betty.event_types.birth import Birth
from betty.locale import default_locale_tag
from betty.localizer import default_localizer
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase
from betty.test_utils.entity.associations.has_citations import DummyHasCitations

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.test_utils.conftest import AssertDumpsLinkedData
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
        assert sut.location.localize(default_localizer) == location

    def test_id(self) -> None:
        sut = Citation(
            id="my-first-citation",
            source=Source(),
        )
        assert sut.id == "my-first-citation"

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
        assert sut.location.localize(default_localizer) == location

    def test_date(self) -> None:
        sut = Citation(source=Source())
        assert sut.date is None

    def test_file_references(self) -> None:
        sut = Citation(source=Source())
        assert list(sut.files) == []

    def test_private(self) -> None:
        sut = Citation(source=Source())
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        citation = Citation(
            id="my-first-citation",
            source=Source(name="The Source", id="my-first-source"),
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/my-first-citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "my-first-citation",
            "privacy": False,
            "facts": [],
            "links": [],
            "files": [],
            "source": "/source/my-first-source/index.json",
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        citation = Citation(
            id="my-first-citation",
            source=Source(
                id="my-first-source",
                name="The Source",
            ),
            location="My First Location",
        )
        citation.facts.add(
            Event(
                id="my-first-event",
                event_type=Birth(),
            )
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/my-first-citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "my-first-citation",
            "privacy": False,
            "location": {default_locale_tag: "My First Location"},
            "source": "/source/my-first-source/index.json",
            "facts": ["/event/my-first-event/index.json"],
            "links": [],
            "files": [],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        citation = Citation(
            id="my-first-citation",
            source=Source(
                id="my-first-source",
                name="The Source",
            ),
            privacy=Privacy.PRIVATE,
        )
        citation.facts.add(
            Event(
                id="my-first-event",
                event_type=Birth(),
            )
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/my-first-citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "my-first-citation",
            "privacy": True,
            "source": "/source/my-first-source/index.json",
            "facts": ["/event/my-first-event/index.json"],
            "links": [],
            "files": [],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected
