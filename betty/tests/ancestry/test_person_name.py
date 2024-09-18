from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.locale import UNDETERMINED_LOCALE
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.model import Entity


class TestPersonName(EntityTestBase):
    @override
    def get_sut_class(self) -> type[PersonName]:
        return PersonName

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            PersonName(person=Person(), individual="Jane"),
            PersonName(person=Person(), affiliation="Doe"),
            PersonName(person=Person(), individual="Jane", affiliation="Doe"),
        ]

    async def test_person(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.person == person
        assert [sut] == list(person.names)

    async def test_locale(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.locale is UNDETERMINED_LOCALE

    async def test_citations(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.citations) == []

    async def test_individual(self) -> None:
        person = Person(id="1")
        individual = "Janet"
        sut = PersonName(
            person=person,
            individual=individual,
            affiliation="Not a Girl",
        )
        assert sut.individual == individual

    async def test_affiliation(self) -> None:
        person = Person(id="1")
        affiliation = "Not a Girl"
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation=affiliation,
        )
        assert sut.affiliation == affiliation

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                    },
                    "individual": "Jane",
                    "locale": UNDETERMINED_LOCALE,
                    "private": False,
                    "citations": [],
                },
                PersonName(person=Person(), individual="Jane"),
            ),
            (
                {
                    "@context": {
                        "affiliation": "https://schema.org/familyName",
                    },
                    "affiliation": "Dough",
                    "locale": UNDETERMINED_LOCALE,
                    "private": False,
                    "citations": [],
                },
                PersonName(person=Person(), affiliation="Dough"),
            ),
            (
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "individual": "Jane",
                    "affiliation": "Dough",
                    "locale": "nl-NL",
                    "private": False,
                    "citations": [],
                },
                PersonName(
                    person=Person(),
                    individual="Jane",
                    affiliation="Dough",
                    locale="nl-NL",
                ),
            ),
            (
                {
                    "locale": "nl-NL",
                    "private": True,
                    "citations": [],
                },
                PersonName(
                    person=Person(),
                    individual="Jane",
                    affiliation="Dough",
                    locale="nl-NL",
                    private=True,
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: PersonName
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
