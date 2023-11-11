from __future__ import annotations

from betty.locale import Date
from betty.model.ancestry import Person, Presence, Subject, Event
from betty.model.event_type import Death, Birth

_LIFETIME_THRESHOLD = 125


class TestDeath:
    async def test_may_create_may_not_for_person_without_presences(self) -> None:
        person = Person('P0')

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is False

    async def test_may_create_may_not_within_lifetime_threshold(self) -> None:
        person = Person('P0')
        Presence(None, person, Subject(), Event(None, Birth, Date(1970, 1, 1)))

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is False

    async def test_may_create_may_over_lifetime_threshold(self) -> None:
        person = Person('P0')
        Presence(None, person, Subject(), Event(None, Birth, Date(1, 1, 1)))

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is True
