from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.privacy import Privacy
from betty.roles.subject import Subject
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from betty.entity import Entity


class TestPresence(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Presence(Person(), None, Event())

    def test_person(self) -> None:
        person = Person()
        sut = Presence(person, Subject(), Event())
        assert sut.person == person

    def test_event(self) -> None:
        role = Subject()
        sut = Presence(Person(), role, Event())
        assert sut.role == role

    def test_role(self) -> None:
        event = Event()
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
        event = Event(
            privacy=event_privacy,
        )
        sut = Presence(person, Subject(), event)
        sut.privacy = presence_privacy

        assert sut.privacy == expected
