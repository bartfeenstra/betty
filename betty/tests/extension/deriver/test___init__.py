from __future__ import annotations

from betty.app import App
from betty.extension import Deriver
from betty.load import load
from betty.locale import DateRange, Date
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
    async def test_post_parse(self) -> None:
        person = Person('P0')
        event = Event(None, Residence)
        event.date = Date(1970, 1, 1)
        Presence(person, Subject(), event)

        with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(Deriver))
            app.project.ancestry.entities.append(person)
            await load(app)

        assert 3 == len(person.presences)
        start = person.start
        assert isinstance(start, Event)
        assert DateRange(None, Date(1970, 1, 1), end_is_boundary=True) == start.date
        end = person.end
        assert isinstance(end, Event)
        assert DateRange(Date(1970, 1, 1), start_is_boundary=True) == end.date
