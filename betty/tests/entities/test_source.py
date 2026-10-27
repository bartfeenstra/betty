from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import pytest

from betty.entities.source import Source
from betty.entity import Entity
from betty.localizables.plain import Plain
from betty.localizer import default_localizer
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence


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
