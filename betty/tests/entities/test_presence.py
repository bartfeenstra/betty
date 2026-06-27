from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.event_types.unknown import UnknownEventType
from betty.privacy import Privacy
from betty.roles.subject import Subject
from betty.roles.unknown import UnknownRole
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

    async def test_dump_linked_data__should_dump(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        person = Person(id="my-first-person")
        event = Event(id="my-first-event")
        role = Subject()
        sut = Presence(person, role, event, id="my-first-presence")

        expected: PortableMapping = {
            "@id": "https://example.com/presence/my-first-presence/index.json",
            "id": "my-first-presence",
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
        sut = Presence(
            person, role, event, id="my-first-presence", privacy=Privacy.PRIVATE
        )

        expected: PortableMapping = {
            "@id": "https://example.com/presence/my-first-presence/index.json",
            "id": "my-first-presence",
            "event": "/event/my-first-event/index.json",
            "person": "/person/my-first-person/index.json",
            "privacy": True,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected
