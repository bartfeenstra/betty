from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    DerivableEventType,
    CreatableDerivableEventType,
    Residence,
    StartOfLifeEventType,
    EndOfLifeEventType,
)
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import DateRange, Date
from betty.model.collections import record_added
from betty.project import Project
from betty.project.extension.deriver import Deriver
from betty.project.load import load
from betty.test_utils.ancestry.event_type import DummyEventType
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.plugin import PluginIdentifier
    from betty.ancestry.event_type import EventType
    from betty.app import App


class Ignored(DummyEventType):
    pass


class ComesBeforeReference(DummyEventType):
    pass


class ComesAfterReference(DummyEventType):
    pass


class ComesBeforeDerivable(DerivableEventType):
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {ComesBeforeReference}


class ComesBeforeCreatableDerivable(CreatableDerivableEventType, ComesBeforeDerivable):
    pass


class ComesAfterDerivable(DerivableEventType, DummyEventType):
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {ComesAfterReference}


class ComesAfterCreatableDerivable(CreatableDerivableEventType, ComesAfterDerivable):
    pass


class ComesBeforeAndAfterDerivable(DerivableEventType, DummyEventType):
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Ignored}

    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {Ignored}


class ComesBeforeAndAfterCreatableDerivable(
    CreatableDerivableEventType, DerivableEventType
):
    pass


class TestDeriver(ExtensionTestBase[Deriver]):
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
            project.configuration.extensions.enable(Deriver)
            project.ancestry.add(person)
            async with project:
                async with record_added(project.ancestry) as added:
                    await load(project)

                assert len(person.presences) == 3
                start = [
                    presence
                    for presence in person.presences
                    if isinstance(presence.event.event_type, StartOfLifeEventType)
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
                    if isinstance(presence.event.event_type, EndOfLifeEventType)
                ][0]
                assert end is not None
                assert end.event is not None
                assert (
                    DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
                )
                assert len(added[Event]) == 2
                assert start.event in added[Event]
                assert end.event in added[Event]
