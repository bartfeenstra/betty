from __future__ import annotations

from typing import Sequence, Mapping, Any, MutableMapping, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.link import Link
from betty.ancestry.source import Source
from betty.date import Date
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.privacy import Privacy
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity


class TestSource(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Source]:
        return Source

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Source(),
            Source(name="My First Source"),
        ]

    async def test_id(self) -> None:
        source_id = "S1"
        sut = Source(id=source_id)
        assert sut.id == source_id

    async def test_name(self) -> None:
        name = "The Source"
        sut = Source(name=name)
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    async def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert sut.contained_by is contained_by_source

    async def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        assert list(sut.contains) == []
        sut.contains = [contains_source]
        assert list(sut.contains) == [contains_source]

    async def test_walk_contains_without_contains(self) -> None:
        sut = Source()
        assert list(sut.walk_contains) == []

    async def test_walk_contains_with_contains(self) -> None:
        sut = Source()
        contains = Source(contained_by=sut)
        contains_contains = Source(contained_by=contains)
        assert list(sut.walk_contains) == [contains, contains_contains]

    async def test_citations(self) -> None:
        sut = Source()
        assert list(sut.citations) == []

    async def test_author(self) -> None:
        sut = Source()
        assert not sut.author
        author = "Me"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_publisher(self) -> None:
        sut = Source()
        assert not sut.publisher
        publisher = "Me"
        sut.publisher = publisher
        assert sut.publisher.localize(DEFAULT_LOCALIZER) == publisher

    async def test_date(self) -> None:
        sut = Source()
        assert sut.date is None

    async def test_file_references(self) -> None:
        sut = Source()
        assert list(sut.file_references) == []

    async def test_links(self) -> None:
        sut = Source()
        assert list(sut.links) == []

    async def test_private(self) -> None:
        sut = Source()
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        source = Source(
            id="the_source",
            name="The Source",
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {"und": "The Source"}},
            "author": {"translations": {}},
            "publisher": {"translations": {}},
            "fileReferences": [],
            "contains": [],
            "containedBy": None,
            "citations": [],
            "notes": [],
            "links": [],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="the_source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the_containing_source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the_contained_source",
                    name="The Contained Source",
                )
            ],
            links=[link],
        )
        Citation(
            id="the_citation",
            source=source,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {"und": "The Source"}},
            "author": {"translations": {"und": "The Author"}},
            "publisher": {"translations": {"und": "The Publisher"}},
            "fileReferences": [],
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
            "date": {
                "year": 2000,
                "month": 1,
                "day": 1,
                "iso8601": "2000-01-01",
                "fuzzy": False,
            },
            "links": [
                {
                    "@context": {"description": "https://schema.org/description"},
                    "url": "https://example.com/the-source",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Source Online"}
                    },
                    "locale": "und",
                    "description": {"translations": {}},
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="the_source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the_containing_source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the_contained_source",
                    name="The Contained Source",
                )
            ],
            links=[link],
            private=True,
        )
        Citation(
            id="the_citation",
            source=source,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": True,
            "name": None,
            "author": None,
            "publisher": None,
            "fileReferences": [],
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected

    async def test_dump_linked_data_should_dump_with_private_associations(self) -> None:
        contained_by_source = Source(
            id="the_containing_source",
            name="The Containing Source",
        )
        contains_source = Source(
            id="the_contained_source",
            name="The Contained Source",
            private=True,
        )
        source = Source(
            id="the_source",
            contained_by=contained_by_source,
            contains=[contains_source],
        )
        Citation(
            id="the_citation",
            source=source,
            private=True,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {}},
            "author": {"translations": {}},
            "publisher": {"translations": {}},
            "fileReferences": [],
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected
