from __future__ import annotations

from typing import TYPE_CHECKING

from betty.date import Date
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.presence import Presence
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.role.subject import Subject

if TYPE_CHECKING:
    from betty.project import Project


class TestDeath:
    async def test_may_create_may_not_for_person_without_presences(
        self, isolated_project: Project
    ) -> None:
        person = Person(id="P0")

        assert await Death.should_exist(isolated_project, person) is False

    async def test_may_create_may_not_within_lifetime_threshold(
        self, isolated_project: Project
    ) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth(),
                date=Date(1970, 1, 1),
            ),
        )

        assert await Death.should_exist(isolated_project, person) is False

    async def test_may_create_may_over_lifetime_threshold(
        self, isolated_project: Project
    ) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth(),
                date=Date(1, 1, 1),
            ),
        )

        assert await Death.should_exist(isolated_project, person) is True
