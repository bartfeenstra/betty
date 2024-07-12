from __future__ import annotations

from typing_extensions import override

from betty.extension.deriver import Deriver
from betty.load import load
from betty.locale.date import DateRange, Date
from betty.locale.localizable import Localizable, plain
from betty.model import record_added
from betty.model.ancestry import Person, Presence, Event
from betty.model.presence_role import Subject
from betty.model.event_type import (
    DerivableEventType,
    CreatableDerivableEventType,
    Residence,
    EventType,
    StartOfLifeEventType,
    EndOfLifeEventType,
)
from betty.project import ExtensionConfiguration, Project
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.plugin import PluginId
    from betty.app import App


class DummyEventType(EventType):
    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return cls.__name__

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("")


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


class TestDeriver:
    async def test_post_load(self, new_temporary_app: App) -> None:
        person = Person(id="P0")
        event = Event(
            event_type=Residence,
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
                    and issubclass(presence.event.event_type, StartOfLifeEventType)
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
                    and issubclass(presence.event.event_type, EndOfLifeEventType)
                ][0]
                assert end is not None
                assert end.event is not None
                assert (
                    DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
                )
                assert len(added[Event]) == 2
                assert start.event in added[Event]
                assert end.event in added[Event]
