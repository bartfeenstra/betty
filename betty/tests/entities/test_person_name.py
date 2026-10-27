from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import pytest

from betty.entities.citation import Citation
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.source import Source
from betty.entity import Entity
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence


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
        person = Person()
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.person == person
        assert [sut] == list(person.names)

    def test_locale(self) -> None:
        person = Person()
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.locale is None

    def test_citations(self) -> None:
        person = Person()
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.citations) == []

    def test_individual(self) -> None:
        person = Person()
        individual = "Janet"
        sut = PersonName(
            person=person,
            individual=individual,
            affiliation="Not a Girl",
        )
        assert sut.individual == individual

    def test_affiliation(self) -> None:
        person = Person()
        affiliation = "Not a Girl"
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation=affiliation,
        )
        assert sut.affiliation == affiliation
