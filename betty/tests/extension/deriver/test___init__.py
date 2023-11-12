from __future__ import annotations

from betty.app import App
from betty.extension import Deriver
from betty.load import load
from betty.locale import DateRange, Date
from betty.model import record_added
from betty.model.ancestry import Person, Presence, Subject, Event
from betty.model.event_type import DerivableEventType, CreatableDerivableEventType, Residence, EventType
from betty.project import ExtensionConfiguration


class Ignored(EventType):
    pass


class ComesBeforeReference(EventType):
    pass


class ComesAfterReference(EventType):
    pass


class ComesBeforeDerivable(DerivableEventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {ComesBeforeReference}


class ComesBeforeCreatableDerivable(CreatableDerivableEventType, ComesBeforeDerivable):
    pass


class ComesAfterDerivable(DerivableEventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {ComesAfterReference}


class ComesAfterCreatableDerivable(CreatableDerivableEventType, ComesAfterDerivable):
    pass


class ComesBeforeAndAfterDerivable(DerivableEventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Ignored}

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Ignored}


class ComesBeforeAndAfterCreatableDerivable(CreatableDerivableEventType, DerivableEventType):
    pass


class TestDeriver:
    async def test_post_load(self) -> None:
        person = Person('P0')
        event = Event(None, Residence)
        event.date = Date(1, 1, 1)
        Presence(None, person, Subject(), event)

        app = App()
        app.project.configuration.extensions.append(ExtensionConfiguration(Deriver))
        app.project.ancestry.add(person)
        with record_added(app.project.ancestry) as added:
            await load(app)

        assert 3 == len(person.presences)
        start = person.start
        assert start is not None
        assert start.event is not None
        assert isinstance(start.event, Event)
        assert DateRange(None, Date(1, 1, 1), end_is_boundary=True) == start.event.date
        end = person.end
        assert end is not None
        assert end.event is not None
        assert DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
        assert 2 == len(added[Event])
        assert start.event in added[Event]
        assert end.event in added[Event]