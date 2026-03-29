from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, cast, override

import pytest

from betty.date import Date
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.model import Entity
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.link import Link
from betty.plugins.entity.source import Source
from betty.privacy import Privacy
from betty.test_utils.model import EntityTestBase

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
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    def test___init____with_author(self) -> None:
        author = "Me"
        sut = Source(author=author)
        assert sut.author is not None
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    def test___init____with_publisher(self) -> None:
        publisher = "Me"
        sut = Source(publisher=publisher)
        assert sut.publisher is not None
        assert sut.publisher.localize(DEFAULT_LOCALIZER) == publisher

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
        source_id = "S1"
        sut = Source(id=source_id)
        assert sut.id == source_id

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
        assert list(sut.file_references) == []

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
            "name": {DEFAULT_LOCALE_TAG: "The Source"},
            "fileReferences": [],
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
            "name": {DEFAULT_LOCALE_TAG: "The Source"},
            "author": {DEFAULT_LOCALE_TAG: "The Author"},
            "publisher": {DEFAULT_LOCALE_TAG: "The Publisher"},
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
                    "id": link.id,
                    "url": {
                        to_language_tag(
                            DEFAULT_LOCALE
                        ): "https://example.com/the-source",
                    },
                    "label": {
                        DEFAULT_LOCALE_TAG: "The Source Online",
                    },
                    "owner": "/source/the_source/index.json",
                    "private": False,
                },
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
            privacy=Privacy.PRIVATE,
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

    async def test_dump_linked_data__should_dump_with_private_associations(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        contained_by_source = Source(
            id="the_containing_source",
            name="The Containing Source",
        )
        contains_source = Source(
            id="the_contained_source",
            name="The Contained Source",
            privacy=Privacy.PRIVATE,
        )
        source = Source(
            id="the_source",
            contained_by=contained_by_source,
            contains=[contains_source],
        )
        Citation(
            id="the_citation",
            source=source,
            privacy=Privacy.PRIVATE,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
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
