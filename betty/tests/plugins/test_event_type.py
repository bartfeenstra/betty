from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.date import Date
from betty.plugins.event_type import Birth, Death
from betty.plugins.role import Subject
from betty.project import Project

if TYPE_CHECKING:
    from betty.app import App


class TestDeath:
    async def test_may_create_may_not_for_person_without_presences(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            person = Person(id="P0")

            assert await Death.should_exist(project, person) is False

    async def test_may_create_may_not_within_lifetime_threshold(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Birth(),
                    date=Date(1970, 1, 1),
                ),
            )

            assert await Death.should_exist(project, person) is False

    async def test_may_create_may_over_lifetime_threshold(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Birth(),
                    date=Date(1, 1, 1),
                ),
            )

            assert await Death.should_exist(project, person) is True
