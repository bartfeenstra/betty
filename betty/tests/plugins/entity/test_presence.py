from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.presence import Presence
from betty.plugins.event_type.unknown import Unknown as UnknownEventType
from betty.plugins.role.subject import Subject
from betty.plugins.role.unknown import Unknown as UnknownRole
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from betty.entity import Entity
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestPresence(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Presence(Person(), UnknownRole(), Event())

    def test_person(self) -> None:
        person = Person()
        sut = Presence(person, Subject(), Event(event_type=UnknownEventType()))
        assert sut.person == person

    def test_event(self) -> None:
        role = Subject()
        sut = Presence(Person(), role, Event(event_type=UnknownEventType()))
        assert sut.role == role

    def test_role(self) -> None:
        event = Event(event_type=UnknownEventType())
        sut = Presence(Person(), Subject(), event)
        assert sut.event == event

    @pytest.mark.parametrize(
        ("expected", "person_privacy", "presence_privacy", "event_privacy"),
        [
            (Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PRIVATE, Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PRIVATE),
        ],
    )
    def test_privacy(
        self,
        expected: Privacy,
        person_privacy: Privacy,
        presence_privacy: Privacy,
        event_privacy: Privacy,
    ) -> None:
        person = Person(privacy=person_privacy)
        event = Event(privacy=event_privacy, event_type=UnknownEventType())
        sut = Presence(person, Subject(), event)
        sut.privacy = presence_privacy

        assert sut.privacy == expected

    async def test_dump_linked_data__should_dump(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        person = Person(id="my-first-person")
        event = Event(id="my-first-event")
        role = Subject()
        sut = Presence(person, role, event)

        expected: PortableMapping = {
            "id": sut.id,
            "event": "/event/my-first-event/index.json",
            "person": "/person/my-first-person/index.json",
            "privacy": False,
            "role": role.plugin().id,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        person = Person(id="my-first-person")
        event = Event(id="my-first-event")
        role = Subject()
        sut = Presence(person, role, event, privacy=Privacy.PRIVATE)

        expected: PortableMapping = {
            "id": sut.id,
            "event": "/event/my-first-event/index.json",
            "person": "/person/my-first-person/index.json",
            "privacy": True,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected
