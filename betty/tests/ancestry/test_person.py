from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import pytest

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.link import Link
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.presence import Presence
from betty.ancestry.source import Source
from betty.event_type.event_types import Birth
from betty.gender.genders import NonBinary
from betty.gender.genders import Unknown as UnknownGender
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, to_language_tag
from betty.model import Entity
from betty.model.association import AssociationRequired, TemporaryToOneResolver
from betty.presence_role.presence_roles import Subject
from betty.privacy import Privacy
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class TestPerson(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        person_with_private_names_only = Person()
        PersonName(
            person=person_with_private_names_only,
            individual="Jane",
            affiliation="Doe",
            privacy=Privacy.PRIVATE,
        )
        person_with_one_public_name = Person()
        PersonName(
            person=person_with_one_public_name, individual="Jane", affiliation="Doe"
        )
        return [
            Person(),
            person_with_private_names_only,
            person_with_one_public_name,
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test___init____with_children(self) -> None:
        child = Person()
        sut = Person(children=[child])
        assert list(sut.children) == [child]
        assert [sut] == list(child.parents)

    def test___init____with_parents(self) -> None:
        parent = Person()
        sut = Person(parents=[parent])
        assert list(sut.parents) == [parent]
        assert [sut] == list(parent.children)

    def test___init____with_presences(self) -> None:
        event = Event(event_type=Birth())
        presence = Presence(TemporaryToOneResolver(), Subject(), event)
        sut = Person(presences=[presence])
        assert list(sut.presences) == [presence]
        assert sut == presence.person

    def test___init____with_names(self) -> None:
        name = PersonName(
            person=TemporaryToOneResolver(),
            individual="Janet",
            affiliation="Not a Girl",
        )
        sut = Person(names=[name])
        assert list(sut.names) == [name]
        assert sut == name.person

    def test_parents(self) -> None:
        sut = Person()
        parent = Person()
        sut.parents.add(parent)
        assert list(sut.parents) == [parent]
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert list(sut.parents) == []
        assert list(parent.children) == []

    def test_children(self) -> None:
        sut = Person()
        child = Person()
        sut.children.add(child)
        assert list(sut.children) == [child]
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert list(sut.children) == []
        assert list(child.parents) == []

    def test_presences(self) -> None:
        event = Event(event_type=Birth())
        sut = Person()
        presence = Presence(sut, Subject(), event)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.person
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        with pytest.raises(AssociationRequired):
            presence.person  # noqa: B018

    def test_names(self) -> None:
        sut = Person()
        name = PersonName(
            person=sut,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.names) == [name]
        assert sut == name.person
        sut.names.remove(name)
        assert list(sut.names) == []
        with pytest.raises(AssociationRequired):
            name.person  # noqa: B018

    def test_id(self) -> None:
        person_id = "P1"
        sut = Person(id=person_id)
        assert sut.id == person_id

    def test_file_references(self) -> None:
        sut = Person()
        assert list(sut.file_references) == []

    def test_citations(self) -> None:
        sut = Person()
        assert list(sut.citations) == []

    def test_links(self) -> None:
        sut = Person()
        assert list(sut.links) == []

    def test_private(self) -> None:
        sut = Person()
        assert sut.privacy is Privacy.UNDETERMINED

    def test_siblings__without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.siblings) == []

    def test_siblings__with_one_common_parent(self) -> None:
        sut = Person()
        sibling = Person()
        parent = Person()
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    def test_siblings__with_multiple_common_parents(self) -> None:
        sut = Person()
        sibling = Person()
        parent = Person()
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    def test_ancestors__without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.ancestors) == []

    def test_ancestors__with_parent(self) -> None:
        sut = Person()
        parent = Person()
        sut.parents.add(parent)
        grandparent = Person()
        parent.parents.add(grandparent)
        assert list(sut.ancestors) == [parent, grandparent]

    def test_descendants__without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.descendants) == []

    def test_descendants__with_parent(self) -> None:
        sut = Person()
        child = Person()
        sut.children.add(child)
        grandchild = Person()
        child.children.add(grandchild)
        assert list(sut.descendants) == [child, grandchild]

    async def test_dump_linked_data__should_dump_minimal(self) -> None:
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
            "gender": UnknownGender.plugin().id,
            "names": [],
            "parents": [],
            "children": [],
            "siblings": [],
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [],
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(self) -> None:
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
        person = Person(id=person_id, privacy=Privacy.PUBLIC, gender=NonBinary())
        name = PersonName(
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
        person.links.add(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        presence = Presence(
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
            "gender": NonBinary.plugin().id,
            "names": [
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "id": name.id,
                    "individual": person_individual_name,
                    "affiliation": person_affiliation_name,
                    "locale": "en-US",
                    "citations": [],
                    "private": False,
                    "person": "/person/the_person/index.json",
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
                    "id": presence.id,
                    "role": "subject",
                    "event": "/event/the_event/index.json",
                    "person": "/person/the_person/index.json",
                    "private": False,
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "@context": {"description": "https://schema.org/description"},
                    "id": link.id,
                    "url": {
                        to_language_tag(
                            DEFAULT_LOCALE
                        ): "https://example.com/the-person",
                    },
                    "label": {
                        DEFAULT_LOCALE_TAG: "The Person Online",
                    },
                    "owner": "/person/the_person/index.json",
                    "private": False,
                },
            ],
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
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
            privacy=Privacy.PRIVATE,
        )
        name = PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link("https://example.com/the-person")
        link.label = "The Person Online"
        person.links.add(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        presence = Presence(
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
            "names": [
                {
                    "id": name.id,
                    "citations": [],
                    "locale": None,
                    "person": "/person/the_person/index.json",
                    "private": True,
                }
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
            "private": True,
            "presences": [
                {
                    "id": presence.id,
                    "event": "/event/the_event/index.json",
                    "person": "/person/the_person/index.json",
                    "private": True,
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "@context": {"description": "https://schema.org/description"},
                    "id": link.id,
                    "owner": "/person/the_person/index.json",
                    "private": True,
                }
            ],
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    def test_gender(self) -> None:
        gender = NonBinary()
        sut = Person()
        sut.gender = gender
        assert sut.gender is gender
