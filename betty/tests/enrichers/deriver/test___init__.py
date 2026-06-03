from __future__ import annotations

from typing import TYPE_CHECKING

from betty.date import Date, DateRange
from betty.enrichers.deriver import Deriver
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.event_types.residence import Residence
from betty.load import load
from betty.roles.subject import Subject
from betty.test_utils.entity import record_added

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestDeriver:
    async def test_enrich(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        person = Person(id="P0")
        event = Event(
            event_type=Residence(),
            date=Date(1, 1, 1),
        )
        Presence(person, Subject(), event)

        async with isolated_project_factory(enrichers=[Deriver]) as project:
            project.ancestry.add(person)
            with record_added(project.ancestry) as added:
                await load(project)

            assert len(person.presences) == 3
            birth = next(
                presence
                for presence in person.presences
                if presence.event.event_type.plugin().id == Birth.plugin().id
                or presence.event.event_type.plugin().indicates == Birth.plugin().id
            )
            assert birth is not None
            assert birth.event is not None
            assert isinstance(birth.event, Event)
            assert (
                DateRange(None, Date(1, 1, 1), end_is_boundary=True) == birth.event.date
            )
            end = next(
                presence
                for presence in person.presences
                if presence.event.event_type.plugin().id == Death.plugin().id
                or presence.event.event_type.plugin().indicates == Death.plugin().id
            )
            assert end is not None
            assert end.event is not None
            assert DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
            assert len(added[Event]) == 2
            assert birth.event in added[Event]
            assert end.event in added[Event]
