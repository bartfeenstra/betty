from __future__ import annotations

from typing import TYPE_CHECKING

from betty.date import Date, DateRange
from betty.model.collections import record_added
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.presence import Presence
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.event_type.residence import Residence
from betty.plugins.extension.deriver import Deriver
from betty.plugins.role.subject import Subject
from betty.project import Project
from betty.project.load import load

if TYPE_CHECKING:
    from betty.app import App


class TestDeriver:
    async def test_post_load(self, isolated_app: App) -> None:
        person = Person(id="P0")
        event = Event(
            event_type=Residence(),
            date=Date(1, 1, 1),
        )
        Presence(person, Subject(), event)

        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Deriver)
            project.ancestry.add(person)
            async with project:
                with record_added(project.ancestry) as added:
                    await load(project)

                assert len(person.presences) == 3
                birth = [
                    presence
                    for presence in person.presences
                    if presence.event.event_type.plugin().id == Birth.plugin().id
                    or presence.event.event_type.plugin().indicates == Birth.plugin().id
                ][0]
                assert birth is not None
                assert birth.event is not None
                assert isinstance(birth.event, Event)
                assert (
                    DateRange(None, Date(1, 1, 1), end_is_boundary=True)
                    == birth.event.date
                )
                end = [
                    presence
                    for presence in person.presences
                    if presence.event.event_type.plugin().id == Death.plugin().id
                    or presence.event.event_type.plugin().indicates == Death.plugin().id
                ][0]
                assert end is not None
                assert end.event is not None
                assert (
                    DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
                )
                assert len(added[Event]) == 2
                assert birth.event in added[Event]
                assert end.event in added[Event]
