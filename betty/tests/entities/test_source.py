from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, cast, override

import pytest

from betty.date import Date
from betty.entities.citation import Citation
from betty.entities.link import Link
from betty.entities.source import Source
from betty.entity import Entity
from betty.locale import default_locale_tag
from betty.locale.localizable.plain import Plain
from betty.locale.localize import default_localizer
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestSource(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            Source(),
            Source(name="My First Source"),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test___init____with_name(self) -> None:
        name = "The Source"
        sut = Source(name=name)
        assert sut.name is not None
        assert sut.name.localize(default_localizer) == name

    def test___init____with_author(self) -> None:
        author = "Me"
        sut = Source(author=author)
        assert sut.author is not None
        assert sut.author.localize(default_localizer) == author

    def test___init____with_publisher(self) -> None:
        publisher = "Me"
        sut = Source(publisher=publisher)
        assert sut.publisher is not None
        assert sut.publisher.localize(default_localizer) == publisher

    def test___init____with_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source(contained_by=contained_by_source)
        assert sut.contained_by is contained_by_source

    def test___init____with_contains(self) -> None:
        contains_source = Source()
        sut = Source(contains=[contains_source])
        assert list(sut.contains) == [contains_source]
        assert contains_source.contained_by is sut

    def test_id(self) -> None:
        sut = Source(id="my-first-source")
        assert sut.id == "my-first-source"

    def test_name(self) -> None:
        sut = Source()
        assert sut.name is None
        name = Plain("The Source")
        sut.name = name
        assert sut.name is name

    def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert sut.contained_by is contained_by_source

    def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        assert list(sut.contains) == []
        sut.contains = [contains_source]
        assert list(sut.contains) == [contains_source]

    def test_citations(self) -> None:
        sut = Source()
        assert list(sut.citations) == []

    def test_author(self) -> None:
        sut = Source()
        assert not sut.author
        author = Plain("Me")
        sut.author = author
        assert sut.author is author

    def test_publisher(self) -> None:
        sut = Source()
        assert not sut.publisher
        publisher = Plain("Me")
        sut.publisher = publisher
        assert sut.publisher is publisher

    def test_date(self) -> None:
        sut = Source()
        assert sut.date is None

    def test_file_references(self) -> None:
        sut = Source()
        assert list(sut.files) == []

    def test_links(self) -> None:
        sut = Source()
        assert list(sut.links) == []

    def test_private(self) -> None:
        sut = Source()
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        source = Source(
            id="my-first-source",
            name="The Source",
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/my-first-source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "my-first-source",
            "privacy": False,
            "name": {default_locale_tag: "The Source"},
            "files": [],
            "contains": [],
            "containedBy": None,
            "citations": [],
            "notes": [],
            "links": [],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        link = Link("https://example.com/the-source", id="my-first-link")
        link.label = "The Source Online"
        source = Source(
            id="my-first-source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the-containing-source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the-contained-source",
                    name="The Contained Source",
                )
            ],
            links=[link],
        )
        Citation(
            id="my-first-citation",
            source=source,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/my-first-source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "my-first-source",
            "privacy": False,
            "name": {default_locale_tag: "The Source"},
            "author": {default_locale_tag: "The Author"},
            "publisher": {default_locale_tag: "The Publisher"},
            "files": [],
            "contains": [
                "/source/the-contained-source/index.json",
            ],
            "citations": [
                "/citation/my-first-citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the-containing-source/index.json",
            "date": {
                "year": 2000,
                "month": 1,
                "day": 1,
                "iso8601": "2000-01-01",
                "fuzzy": False,
            },
            "links": [
                "/link/my-first-link/index.json",
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="my-first-source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the-containing-source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the-contained-source",
                    name="The Contained Source",
                )
            ],
            links=[link],
            privacy=Privacy.PRIVATE,
        )
        Citation(
            id="my-first-citation",
            source=source,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/my-first-source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "my-first-source",
            "privacy": True,
            "files": [],
            "contains": [
                "/source/the-contained-source/index.json",
            ],
            "citations": [
                "/citation/my-first-citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the-containing-source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected
