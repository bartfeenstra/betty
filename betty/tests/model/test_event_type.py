from __future__ import annotations

from typing_extensions import override

from betty.locale.date import Date
from betty.model.ancestry import Person, Presence, Event
from betty.model.event_type import Death, Birth
from betty.model.presence_role import Subject
from betty.test_utils.model.event_type import EventTypeTestBase

_LIFETIME_THRESHOLD = 125


class TestDeath(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[Death]:
        return Death

    async def test_may_create_may_not_for_person_without_presences(self) -> None:
        person = Person(id="P0")

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is False

    async def test_may_create_may_not_within_lifetime_threshold(self) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth(),
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
                event_type=Birth(),
                date=Date(1, 1, 1),
            ),
        )

        assert Death.may_create(person, _LIFETIME_THRESHOLD) is True
