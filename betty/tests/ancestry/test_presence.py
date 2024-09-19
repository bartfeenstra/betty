from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import (
    Unknown as UnknownPresenceRole,
    Subject,
)
from betty.ancestry.privacy import Privacy
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity


class TestPresence(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Presence]:
        return Presence

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Presence(None, UnknownPresenceRole(), None),
            Presence(Person(), UnknownPresenceRole(), None),
            Presence(None, UnknownPresenceRole(), Event()),
            Presence(Person(), UnknownPresenceRole(), Event()),
        ]

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
