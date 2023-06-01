from typing import Optional, Set, Type, Iterator

import pytest

from betty.app import App
from betty.deriver import Deriver
from betty.load import load
from betty.locale import DateRange, Date, Datey
from betty.model.ancestry import Person, Presence, Subject, EventType, Event
from betty.model.event_type import DerivableEventType, CreatableDerivableEventType, Residence
from betty.project import ExtensionConfiguration


class Ignored(EventType):
    pass


class ComesBeforeReference(EventType):
    pass


class ComesAfterReference(EventType):
    pass


class ComesBeforeDerivable(DerivableEventType):
    @classmethod
    def comes_before(cls) -> Set[Type['EventType']]:
        return {ComesBeforeReference}


class ComesBeforeCreatableDerivable(CreatableDerivableEventType, ComesBeforeDerivable):
    pass


class ComesAfterDerivable(DerivableEventType):
    @classmethod
    def comes_after(cls) -> Set[Type['EventType']]:
        return {ComesAfterReference}


class ComesAfterCreatableDerivable(CreatableDerivableEventType, ComesAfterDerivable):
    pass


class ComesBeforeAndAfterDerivable(DerivableEventType):
    @classmethod
    def comes_before(cls) -> Set[Type['EventType']]:
        return {Ignored}

    @classmethod
    def comes_after(cls) -> Set[Type['EventType']]:
        return {Ignored}


class ComesBeforeAndAfterCreatableDerivable(CreatableDerivableEventType, DerivableEventType):
    pass


class TestDeriver:
    async def test_post_parse(self):
        person = Person('P0')
        reference_presence = Presence(person, Subject(), Event(None, Residence))
        reference_presence.event.date = Date(1970, 1, 1)

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


@pytest.fixture(scope='function')
def test_derive_app() -> Iterator[App]:
    app = App()
    with app:
        app.project.configuration.extensions.append(ExtensionConfiguration(Deriver))
        yield app


class TestDerive:
    @pytest.mark.parametrize('event_type', [
        ComesBeforeDerivable,
        ComesBeforeCreatableDerivable,
        ComesAfterDerivable,
        ComesAfterCreatableDerivable,
        ComesBeforeAndAfterDerivable,
        ComesBeforeAndAfterCreatableDerivable,
    ])
    def test_derive_without_events(self, event_type: Type[DerivableEventType], test_derive_app: App):
        person = Person('P0')

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, event_type)

        assert 0 == created
        assert 0 == updated
        assert 0 == len(person.presences)

    @pytest.mark.parametrize('event_type', [
        ComesBeforeDerivable,
        ComesBeforeCreatableDerivable,
        ComesAfterDerivable,
        ComesAfterCreatableDerivable,
        ComesBeforeAndAfterDerivable,
        ComesBeforeAndAfterCreatableDerivable,
    ])
    def test_derive_create_derivable_events_without_reference_events(self, event_type: Type[DerivableEventType], test_derive_app: App):
        person = Person('P0')
        derivable_event = Event(None, Ignored)
        Presence(person, Subject(), derivable_event)

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, event_type)

        assert 0 == created
        assert 0 == updated
        assert 1 == len(person.presences)
        assert derivable_event.date is None

    @pytest.mark.parametrize('event_type', [
        ComesBeforeDerivable,
        ComesBeforeCreatableDerivable,
        ComesAfterDerivable,
        ComesAfterCreatableDerivable,
        ComesBeforeAndAfterDerivable,
        ComesBeforeAndAfterCreatableDerivable,
    ])
    def test_derive_update_derivable_event_without_reference_events(self, event_type: Type[DerivableEventType], test_derive_app: App):
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored))
        derivable_event = Event(None, event_type)
        Presence(person, Subject(), derivable_event)

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, event_type)

        assert 0 == created
        assert 0 == updated
        assert 2 == len(person.presences)
        assert derivable_event.date is None

    @pytest.mark.parametrize('expected_datey, before_datey, derivable_datey', [
        (None, None, None),
        (Date(2000, 1, 1), Date(1970, 1, 1), Date(2000, 1, 1)),
        (Date(1969, 1, 1), Date(1970, 1, 1), Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), DateRange(Date(1970, 1, 1)), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1)), DateRange(Date(1969, 1, 1))),
        (DateRange(None, Date(2000, 1, 1)), DateRange(None, Date(1970, 1, 1)), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), DateRange(None, Date(1970, 1, 1)), DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), None, DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), None, DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), Date(1970, 1, 1), None),
        (Date(2000, 1, 1), DateRange(Date(1970, 1, 1)), Date(2000, 1, 1)),
        (Date(1969, 1, 1), DateRange(Date(1970, 1, 1)), Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True), DateRange(None, Date(1970, 1, 1)), DateRange(Date(1969, 1, 1))),
        (DateRange(None, Date(2000, 1, 1)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(None, Date(1969, 1, 1))),
        (DateRange(None, Date(2000, 1, 1)), None, DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), None, DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), Date(1970, 1, 1), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), Date(1970, 1, 1), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1)), None),
        (Date(2000, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(2000, 1, 1)),
        (Date(1969, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1)), None, DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1)), None, DateRange(Date(1969, 1, 1))),
        (DateRange(None, Date(2000, 1, 1)), Date(1970, 1, 1), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), Date(1970, 1, 1), DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), DateRange(Date(1970, 1, 1)), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), DateRange(Date(1970, 1, 1)), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(None, Date(1970, 1, 1)), None),
        (Date(2000, 1, 1), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), Date(2000, 1, 1)),
        (Date(1969, 1, 1), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), Date(1969, 1, 1)),
        (Date(2000, 1, 1), None, Date(2000, 1, 1)),
        (Date(1969, 1, 1), None, Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), Date(1970, 1, 1), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True), Date(1970, 1, 1), DateRange(Date(1969, 1, 1))),
        (DateRange(None, Date(2000, 1, 1)), DateRange(Date(1970, 1, 1)), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), DateRange(Date(1970, 1, 1)), DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), None),
    ])
    def test_derive_update_comes_before_derivable_event(self, expected_datey: Optional[Datey], before_datey: Optional[Datey], derivable_datey: Optional[Datey], test_derive_app: App):
        expected_updates = 0 if expected_datey == derivable_datey else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored, Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesBeforeReference, before_datey))
        derivable_event = Event(None, ComesBeforeDerivable, derivable_datey)
        Presence(person, Subject(), derivable_event)

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, ComesBeforeDerivable)

        assert 0 == created
        assert expected_updates == updated
        assert 3 == len(person.presences)
        assert expected_datey == derivable_event.date

    @pytest.mark.parametrize('expected_datey, before_datey', [
        (None, None,),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), Date(1970, 1, 1)),
        (None, DateRange(None, None)),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(None, Date(1970, 1, 1))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1971, 1, 1))),
    ])
    def test_derive_create_comes_before_derivable_event(self, expected_datey: Optional[Datey], before_datey: Optional[Datey], test_derive_app: App):
        expected_creations = 0 if expected_datey is None else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored, Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesBeforeReference, before_datey))

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, ComesBeforeCreatableDerivable)

        derived_presences = [presence for presence in person.presences if issubclass(presence.event.type, ComesBeforeCreatableDerivable)]
        assert expected_creations == len(derived_presences)
        if expected_creations:
            derived_presence = derived_presences[0]
            assert isinstance(derived_presence.role, Subject)
            assert expected_datey == derived_presence.event.date
        assert expected_creations == created
        assert 0 == updated
        assert 2 + expected_creations == len(person.presences)

    @pytest.mark.parametrize('expected_datey, after_datey, derivable_datey', [
        (None, None, None),
        (Date(2000, 1, 1), Date(1970, 1, 1), Date(2000, 1, 1)),
        (Date(1969, 1, 1), Date(1970, 1, 1), Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), DateRange(Date(1970, 1, 1)), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1)), DateRange(Date(1970, 1, 1)), DateRange(Date(1969, 1, 1))),
        (DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True), DateRange(None, Date(1970, 1, 1)), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), DateRange(None, Date(1970, 1, 1)), DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), None, DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), None, DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), Date(1970, 1, 1), None),
        (Date(2000, 1, 1), DateRange(Date(1970, 1, 1)), Date(2000, 1, 1)),
        (Date(1969, 1, 1), DateRange(Date(1970, 1, 1)), Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(1969, 1, 1))),
        (DateRange(Date(1999, 12, 31), Date(2000, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(None, Date(1969, 1, 1))),
        (DateRange(None, Date(2000, 1, 1)), None, DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), None, DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), Date(1970, 1, 1), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), Date(1970, 1, 1), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1)), None),
        (Date(2000, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(2000, 1, 1)),
        (Date(1969, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1)), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), DateRange(Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1)), None, DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1)), None, DateRange(Date(1969, 1, 1))),
        (DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True), Date(1970, 1, 1), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), Date(1970, 1, 1), DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), DateRange(Date(1970, 1, 1)), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), DateRange(Date(1970, 1, 1)), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), DateRange(None, Date(1970, 1, 1)), None),
        (Date(2000, 1, 1), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), Date(2000, 1, 1)),
        (Date(1969, 1, 1), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), Date(1969, 1, 1)),
        (Date(2000, 1, 1), None, Date(2000, 1, 1)),
        (Date(1969, 1, 1), None, Date(1969, 1, 1)),
        (DateRange(Date(2000, 1, 1)), Date(1970, 1, 1), DateRange(Date(2000, 1, 1))),
        (DateRange(Date(1969, 1, 1)), Date(1970, 1, 1), DateRange(Date(1969, 1, 1))),
        (DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1)), DateRange(None, Date(2000, 1, 1))),
        (DateRange(None, Date(1969, 1, 1)), DateRange(Date(1970, 1, 1)), DateRange(None, Date(1969, 1, 1))),
        (DateRange(Date(2000, 1, 1), Date(2000, 12, 31)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(2000, 1, 1), Date(2000, 12, 31))),
        (DateRange(Date(1969, 1, 1), Date(1969, 12, 31)), DateRange(None, Date(1970, 1, 1)), DateRange(Date(1969, 1, 1), Date(1969, 12, 31))),
        (DateRange(Date(1999, 12, 31), start_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31)), None),
    ])
    def test_derive_update_comes_after_derivable_event(self, expected_datey: Optional[Datey], after_datey: Optional[Datey], derivable_datey: Optional[Datey], test_derive_app: App):
        expected_updates = 0 if expected_datey == derivable_datey else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored, Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesAfterReference, after_datey))
        derivable_event = Event(None, ComesAfterDerivable, derivable_datey)
        Presence(person, Subject(), derivable_event)

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, ComesAfterDerivable)

        assert expected_datey == derivable_event.date
        assert 0 == created
        assert expected_updates == updated
        assert 3 == len(person.presences)

    @pytest.mark.parametrize('expected_datey, after_datey', [
        (None, None),
        (None, Date()),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), Date(1970, 1, 1)),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1))),
        (DateRange(Date(1999, 12, 31), start_is_boundary=True), DateRange(None, Date(1999, 12, 31))),
        (DateRange(Date(1999, 12, 31), start_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31))),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True)),
    ])
    def test_derive_create_comes_after_derivable_event(self, expected_datey: Optional[Datey], after_datey: Optional[Datey], test_derive_app: App):
        expected_creations = 0 if expected_datey is None else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored, Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesAfterReference, after_datey))

        created, updated = test_derive_app.extensions[Deriver].derive_person(person, ComesAfterCreatableDerivable)

        derived_presences = [presence for presence in person.presences if issubclass(presence.event.type, ComesAfterCreatableDerivable)]
        assert expected_creations == len(derived_presences)
        if expected_creations:
            derived_presence = derived_presences[0]
            assert isinstance(derived_presence.role, Subject)
            assert expected_datey == derived_presence.event.date
        assert expected_creations == created
        assert 0 == updated
        assert 2 + expected_creations == len(person.presences)
