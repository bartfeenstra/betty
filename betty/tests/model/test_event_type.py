from __future__ import annotations

import pytest

from betty.locale import Date
from betty.model.ancestry import Person, Presence, Subject, Event
from betty.model.event_type import Death, Birth, EventType

_LIFETIME_THRESHOLD = 125


class TestEventType:
    async def test_new(self) -> None:
        with pytest.raises(RuntimeError):
            EventType()


class TestDeath:
    async def test_may_create_may_not_for_person_without_presences(self) -> None:
        person = Person(id="P0")

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is False

    async def test_may_create_may_not_within_lifetime_threshold(self) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth,
                date=Date(1970, 1, 1),
            ),
        )

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is False

    async def test_may_create_may_over_lifetime_threshold(self) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth,
                date=Date(1, 1, 1),
            ),
        )

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is True
