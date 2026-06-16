from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import pytest

from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.link import Link
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.entity import Entity
from betty.entity.association import AssociationRequired, TemporaryToOneResolver
from betty.event_types.birth import Birth
from betty.genders.non_binary import NonBinary
from betty.genders.unknown import Unknown as UnknownGender
from betty.privacy import Privacy
from betty.roles.subject import Subject
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.test_utils.conftest import AssertDumpsLinkedData


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
        sut = Person(id="my-first-person")
        assert sut.id == "my-first-person"

    def test_file_references(self) -> None:
        sut = Person()
        assert list(sut.files) == []

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

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        person = Person(id="my-first-person")
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/my-first-person/index.json",
            "@type": "https://schema.org/Person",
            "id": "my-first-person",
            "privacy": False,
            "gender": UnknownGender.plugin().id,
            "names": [],
            "parents": [],
            "children": [],
            "siblings": [],
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [],
            "files": [],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        parent = Person(id="my-first-parent")

        child = Person(id="my-first-child")

        sibling = Person(id="my-first-sibling")
        sibling.parents.add(parent)

        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(
            id="my-first-person", privacy=Privacy.PUBLIC, gender=NonBinary()
        )
        PersonName(
            id="my-first-person-name",
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
            locale="en-US",
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link(
            "https://example.com/the-person",
            id="my-first-link",
            label="The Person Online",
        )
        person.links.add(link)
        person.citations.add(
            Citation(
                id="my-first-citation",
                source=Source(
                    id="my-first-source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="my-first-event",
                event_type=Birth(),
            ),
            id="my-first-presence",
        )

        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/my-first-person/index.json",
            "@type": "https://schema.org/Person",
            "id": "my-first-person",
            "privacy": False,
            "gender": NonBinary.plugin().id,
            "names": [
                "/person-name/my-first-person-name/index.json",
            ],
            "parents": [
                "/person/my-first-parent/index.json",
            ],
            "children": [
                "/person/my-first-child/index.json",
            ],
            "siblings": [
                "/person/my-first-sibling/index.json",
            ],
            "presences": [
                "/presence/my-first-presence/index.json",
            ],
            "citations": [
                "/citation/my-first-citation/index.json",
            ],
            "notes": [],
            "links": [
                "/link/my-first-link/index.json",
            ],
            "files": [],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        parent = Person(id="my-first-parent")

        child = Person(id="my-first-child")

        sibling = Person(id="my-first-sibling")
        sibling.parents.add(parent)

        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(
            id="my-first-person",
            privacy=Privacy.PRIVATE,
        )
        PersonName(
            id="my-first-person-name",
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link("https://example.com/the-person", id="my-first-link")
        link.label = "The Person Online"
        person.links.add(link)
        person.citations.add(
            Citation(
                id="my-first-citation",
                source=Source(
                    id="my-first-source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="my-first-event",
                event_type=Birth(),
            ),
            id="my-first-presence",
        )

        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/my-first-person/index.json",
            "@type": "https://schema.org/Person",
            "id": "my-first-person",
            "names": [
                "/person-name/my-first-person-name/index.json",
            ],
            "parents": [
                "/person/my-first-parent/index.json",
            ],
            "children": [
                "/person/my-first-child/index.json",
            ],
            "siblings": [
                "/person/my-first-sibling/index.json",
            ],
            "privacy": True,
            "presences": [
                "/presence/my-first-presence/index.json",
            ],
            "citations": [
                "/citation/my-first-citation/index.json",
            ],
            "notes": [],
            "links": [
                "/link/my-first-link/index.json",
            ],
            "files": [],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    def test_gender(self) -> None:
        gender = NonBinary()
        sut = Person()
        sut.gender = gender
        assert sut.gender is gender
