from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.extension.deriver import Deriver
from betty.load import load
from betty.locale.date import DateRange, Date
from betty.model.collections import record_added
from betty.model.ancestry import Person, Presence, Event
from betty.model.event_type import (
    DerivableEventType,
    CreatableDerivableEventType,
    Residence,
    EventType,
    StartOfLifeEventType,
    EndOfLifeEventType,
)
from betty.model.presence_role import Subject
from betty.project import ExtensionConfiguration, Project
from betty.test_utils.model.event_type import DummyEventType
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App


class Ignored(DummyEventType):
    pass


class ComesBeforeReference(DummyEventType):
    pass


class ComesAfterReference(DummyEventType):
    pass


class ComesBeforeDerivable(DerivableEventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {ComesBeforeReference}


class ComesBeforeCreatableDerivable(CreatableDerivableEventType, ComesBeforeDerivable):
    pass


class ComesAfterDerivable(DerivableEventType, DummyEventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {ComesAfterReference}


class ComesAfterCreatableDerivable(CreatableDerivableEventType, ComesAfterDerivable):
    pass


class ComesBeforeAndAfterDerivable(DerivableEventType, DummyEventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Ignored}

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Ignored}


class ComesBeforeAndAfterCreatableDerivable(
    CreatableDerivableEventType, DerivableEventType
):
    pass


class TestDeriver(ExtensionTestBase):
    @override
    def get_sut_class(self) -> type[Deriver]:
        return Deriver

    async def test_post_load(self, new_temporary_app: App) -> None:
        person = Person(id="P0")
        event = Event(
            event_type=Residence(),
            date=Date(1, 1, 1),
        )
        Presence(person, Subject(), event)

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(ExtensionConfiguration(Deriver))
            project.ancestry.add(person)
            async with project:
                with record_added(project.ancestry) as added:
                    await load(project)

                assert len(person.presences) == 3
                start = [
                    presence
                    for presence in person.presences
                    if presence.event
                    and isinstance(presence.event.event_type, StartOfLifeEventType)
                ][0]
                assert start is not None
                assert start.event is not None
                assert isinstance(start.event, Event)
                assert (
                    DateRange(None, Date(1, 1, 1), end_is_boundary=True)
                    == start.event.date
                )
                end = [
                    presence
                    for presence in person.presences
                    if presence.event
                    and isinstance(presence.event.event_type, EndOfLifeEventType)
                ][0]
                assert end is not None
                assert end.event is not None
                assert (
                    DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
                )
                assert len(added[Event]) == 2
                assert start.event in added[Event]
                assert end.event in added[Event]
