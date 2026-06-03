from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import pytest

from betty.entities.citation import Citation
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.source import Source
from betty.entity import Entity
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestPersonName(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            PersonName(person=Person(), individual="Jane"),
            PersonName(person=Person(), affiliation="Doe"),
            PersonName(person=Person(), individual="Jane", affiliation="Doe"),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test___init___should_require_at_least_one_type_of_name(self) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            PersonName(person=Person())

    def test___init___with_citations(self) -> None:
        citation = Citation(source=Source())
        sut = PersonName(person=Person(), individual="Jane", citations=[citation])
        assert list(sut.citations) == [citation]

    def test_person(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.person == person
        assert [sut] == list(person.names)

    def test_locale(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.locale is None

    def test_citations(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.citations) == []

    def test_individual(self) -> None:
        person = Person(id="1")
        individual = "Janet"
        sut = PersonName(
            person=person,
            individual=individual,
            affiliation="Not a Girl",
        )
        assert sut.individual == individual

    def test_affiliation(self) -> None:
        person = Person(id="1")
        affiliation = "Not a Girl"
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation=affiliation,
        )
        assert sut.affiliation == affiliation

    async def test_dump_linked_data__should_dump_minimal_individual(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        sut = PersonName(person=Person(), individual="Jane")
        actual = await assert_dumps_linked_data(sut)
        expected: PortableMapping = {
            "@context": {
                "individual": "https://schema.org/givenName",
            },
            "id": sut.id,
            "individual": "Jane",
            "locale": "und",
            "privacy": False,
            "citations": [],
            "person": None,
        }
        assert actual == expected

    async def test_dump_linked_data__should_dump_minimal_affiliation(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        sut = PersonName(person=Person(), affiliation="Doe")
        actual = await assert_dumps_linked_data(sut)
        expected: PortableMapping = {
            "@context": {
                "affiliation": "https://schema.org/familyName",
            },
            "id": sut.id,
            "affiliation": "Doe",
            "locale": "und",
            "privacy": False,
            "citations": [],
            "person": None,
        }
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        person = Person(id="P1")
        citation = Citation(id="C1", source=Source())
        locale = "nl-NL"
        sut = PersonName(
            person=person,
            individual="Jane",
            affiliation="Doe",
            citations=[citation],
            locale=locale,
        )
        actual = await assert_dumps_linked_data(sut)
        expected = {
            "@context": {
                "individual": "https://schema.org/givenName",
                "affiliation": "https://schema.org/familyName",
            },
            "id": sut.id,
            "individual": "Jane",
            "affiliation": "Doe",
            "locale": locale,
            "privacy": False,
            "citations": [
                "/citation/C1/index.json",
            ],
            "person": "/person/P1/index.json",
        }
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        person = Person(id="P1")
        citation = Citation(id="C1", source=Source())
        locale = "nl-NL"
        sut = PersonName(
            person=person,
            individual="Jane",
            affiliation="Doe",
            citations=[citation],
            locale=locale,
            privacy=Privacy.PRIVATE,
        )
        actual = await assert_dumps_linked_data(sut)
        expected = {
            "id": sut.id,
            "locale": None,
            "privacy": True,
            "citations": [
                "/citation/C1/index.json",
            ],
            "person": "/person/P1/index.json",
        }
        assert actual == expected
