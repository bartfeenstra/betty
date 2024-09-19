from __future__ import annotations

from typing import Sequence, Mapping, Any, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry import PersonName, Event, Presence, Citation, Source
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.gender.genders import Unknown as UnknownGender, NonBinary
from betty.ancestry.link import Link
from betty.ancestry.person import Person
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.privacy import Privacy
from betty.locale import UNDETERMINED_LOCALE
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity


class TestPerson(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Person]:
        return Person

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            # No names.
            Person(),
            # No public names.
            Person(
                names=[PersonName(individual="Jane", affiliation="Doe", private=True)]
            ),
            # One public name.
            Person(names=[PersonName(individual="Jane", affiliation="Doe")]),
        ]

    async def test_parents(self) -> None:
        sut = Person(id="1")
        parent = Person(id="2")
        sut.parents.add(parent)
        assert list(sut.parents) == [parent]
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert list(sut.parents) == []
        assert list(parent.children) == []

    async def test_children(self) -> None:
        sut = Person(id="1")
        child = Person(id="2")
        sut.children.add(child)
        assert list(sut.children) == [child]
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert list(sut.children) == []
        assert list(child.parents) == []

    async def test_presences(self) -> None:
        event = Event(event_type=Birth())
        sut = Person(id="1")
        presence = Presence(sut, Subject(), event)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.person
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        assert presence.person is None

    async def test_names(self) -> None:
        sut = Person(id="1")
        name = PersonName(
            person=sut,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.names) == [name]
        assert sut == name.person
        sut.names.remove(name)
        assert list(sut.names) == []
        assert name.person is None

    async def test_id(self) -> None:
        person_id = "P1"
        sut = Person(id=person_id)
        assert sut.id == person_id

    async def test_file_references(self) -> None:
        sut = Person(id="1")
        assert list(sut.file_references) == []

    async def test_citations(self) -> None:
        sut = Person(id="1")
        assert list(sut.citations) == []

    async def test_links(self) -> None:
        sut = Person(id="1")
        assert list(sut.links) == []

    async def test_private(self) -> None:
        sut = Person(id="1")
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_siblings_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.siblings) == []

    async def test_siblings_with_one_common_parent(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    async def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    async def test_ancestors_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.ancestors) == []

    async def test_ancestors_with_parent(self) -> None:
        sut = Person(id="1")
        parent = Person(id="3")
        sut.parents.add(parent)
        grandparent = Person(id="2")
        parent.parents.add(grandparent)
        assert list(sut.ancestors) == [parent, grandparent]

    async def test_descendants_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.descendants) == []

    async def test_descendants_with_parent(self) -> None:
        sut = Person(id="1")
        child = Person(id="3")
        sut.children.add(child)
        grandchild = Person(id="2")
        child.children.add(grandchild)
        assert list(sut.descendants) == [child, grandchild]

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        person_id = "the_person"
        person = Person(id=person_id)
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "private": False,
            "gender": UnknownGender.plugin_id(),
            "names": [],
            "parents": [],
            "children": [],
            "siblings": [],
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        parent_id = "the_parent"
        parent = Person(id=parent_id)

        child_id = "the_child"
        child = Person(id=child_id)

        sibling_id = "the_sibling"
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = "the_person"
        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(id=person_id, public=True, gender=NonBinary())
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
            locale="en-US",
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link(
            "https://example.com/the-person",
            label="The Person Online",
        )
        person.links.append(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="the_event",
                event_type=Birth(),
            ),
        )

        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "private": False,
            "gender": NonBinary.plugin_id(),
            "names": [
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "individual": person_individual_name,
                    "affiliation": person_affiliation_name,
                    "locale": "en-US",
                    "citations": [],
                    "private": False,
                },
            ],
            "parents": [
                "/person/the_parent/index.json",
            ],
            "children": [
                "/person/the_child/index.json",
            ],
            "siblings": [
                "/person/the_sibling/index.json",
            ],
            "presences": [
                {
                    "@context": {
                        "event": "https://schema.org/performerIn",
                    },
                    "role": "subject",
                    "event": "/event/the_event/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "url": "https://example.com/the-person",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Person Online"}
                    },
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        parent_id = "the_parent"
        parent = Person(id=parent_id)

        child_id = "the_child"
        child = Person(id=child_id)

        sibling_id = "the_sibling"
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = "the_person"
        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(
            id=person_id,
            private=True,
        )
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link("https://example.com/the-person")
        link.label = "The Person Online"
        person.links.append(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="the_event",
                event_type=Birth(),
            ),
        )

        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "names": [],
            "parents": [
                "/person/the_parent/index.json",
            ],
            "children": [
                "/person/the_child/index.json",
            ],
            "siblings": [
                "/person/the_sibling/index.json",
            ],
            "private": True,
            "presences": [
                {
                    "@context": {
                        "event": "https://schema.org/performerIn",
                    },
                    "event": "/event/the_event/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected
