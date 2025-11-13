from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role import PresenceRole
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.presence_role.presence_roles import Unknown as UnknownPresenceRole
from betty.mutability import Mutable
from betty.privacy import Privacy
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityDefinitionTestBase, EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity
    from betty.plugin import PluginDefinition
    from betty.serde.dump import Dump, DumpMapping


class TestPresenceDefinition(EntityDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Presence.plugin


class TestPresence(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Presence(Person(), UnknownPresenceRole(), Event())

    async def test_person(self) -> None:
        person = Person()
        sut = Presence(person, Subject(), Event(event_type=UnknownEventType()))
        assert sut.person == person

    async def test_event(self) -> None:
        role = Subject()
        sut = Presence(Person(), role, Event(event_type=UnknownEventType()))
        assert sut.role == role

    async def test_role(self) -> None:
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
    async def test_privacy(
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

    async def test_dump_linked_data__should_dump(self) -> None:
        person = Person(id="my-first-person")
        event = Event(id="my-first-event")
        role = Subject()
        sut = Presence(person, role, event)

        expected: DumpMapping[Dump] = {
            "id": sut.id,
            "event": "/event/my-first-event/index.json",
            "person": "/person/my-first-person/index.json",
            "private": False,
            "role": role.plugin.id,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
        person = Person(id="my-first-person")
        event = Event(id="my-first-event")
        role = Subject()
        sut = Presence(person, role, event, private=True)

        expected: DumpMapping[Dump] = {
            "id": sut.id,
            "event": "/event/my-first-event/index.json",
            "person": "/person/my-first-person/index.json",
            "private": True,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected

    def test_get_mutable_instances(self) -> None:
        class _MutablePresenceRole(PresenceRole, Mutable):
            pass

        role = _MutablePresenceRole()
        sut = Presence(Person(), role, Event())
        sut.immutable = True
        assert role.immutable
