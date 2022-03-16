from typing import Optional, Set, Type
from parameterized import parameterized

from betty.model.ancestry import Person, Presence, Subject, EventType, Event
from betty.asyncio import sync
from betty.locale import DateRange, Date, Datey
from betty.load import load
from betty.deriver import Deriver
from betty.app import App, AppExtensionConfiguration
from betty.model.event_type import DerivableEventType, CreatableDerivableEventType, Residence
from betty.tests import TestCase


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


class DeriverTest(TestCase):
    @sync
    async def test_post_parse(self):
        person = Person('P0')
        reference_presence = Presence(person, Subject(), Event(None, Residence()))
        reference_presence.event.date = Date(1970, 1, 1)

        async with App() as app:
            app.configuration.extensions.add(AppExtensionConfiguration(Deriver))
            app.ancestry.entities.append(person)
            await load(app)

        self.assertEqual(3, len(person.presences))
        self.assertEqual(DateRange(None, Date(1970, 1, 1), end_is_boundary=True), person.start.date)
        self.assertEqual(DateRange(Date(1970, 1, 1), start_is_boundary=True), person.end.date)


class DeriveTest(TestCase):
    @sync
    async def setUp(self) -> None:
        self._app = App()
        await self._app.activate()
        self._app.configuration.extensions.add(AppExtensionConfiguration(Deriver))

    @sync
    async def tearDown(self) -> None:
        await self._app.deactivate()

    @parameterized.expand([
        (ComesBeforeDerivable,),
        (ComesBeforeCreatableDerivable,),
        (ComesAfterDerivable,),
        (ComesAfterCreatableDerivable,),
        (ComesBeforeAndAfterDerivable,),
        (ComesBeforeAndAfterCreatableDerivable,),
    ])
    @sync
    async def test_derive_without_events(self, event_type_type: Type[DerivableEventType]):
        person = Person('P0')

        created, updated = self._app.extensions[Deriver].derive_person(person, event_type_type)

        self.assertEqual(0, created)
        self.assertEqual(0, updated)
        self.assertEqual(0, len(person.presences))

    @parameterized.expand([
        (ComesBeforeDerivable,),
        (ComesBeforeCreatableDerivable,),
        (ComesAfterDerivable,),
        (ComesAfterCreatableDerivable,),
        (ComesBeforeAndAfterDerivable,),
        (ComesBeforeAndAfterCreatableDerivable,),
    ])
    @sync
    async def test_derive_create_derivable_events_without_reference_events(self, event_type_type: Type[DerivableEventType]):
        person = Person('P0')
        derivable_event = Event(None, Ignored())
        Presence(person, Subject(), derivable_event)

        created, updated = self._app.extensions[Deriver].derive_person(person, event_type_type)

        self.assertEqual(0, created)
        self.assertEqual(0, updated)
        self.assertEqual(1, len(person.presences))
        self.assertIsNone(derivable_event.date)

    @parameterized.expand([
        (ComesBeforeDerivable,),
        (ComesBeforeCreatableDerivable,),
        (ComesAfterDerivable,),
        (ComesAfterCreatableDerivable,),
        (ComesBeforeAndAfterDerivable,),
        (ComesBeforeAndAfterCreatableDerivable,),
    ])
    @sync
    async def test_derive_update_derivable_event_without_reference_events(self, event_type_type: Type[DerivableEventType]):
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored()))
        derivable_event = Event(None, event_type_type())
        Presence(person, Subject(), derivable_event)

        created, updated = self._app.extensions[Deriver].derive_person(person, event_type_type)

        self.assertEqual(0, created)
        self.assertEqual(0, updated)
        self.assertEqual(2, len(person.presences))
        self.assertIsNone(derivable_event.date)

    @parameterized.expand([
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
    @sync
    async def test_derive_update_comes_before_derivable_event(self, expected_datey: Optional[Datey], before_datey: Optional[Datey], derivable_datey: Optional[Datey]):
        expected_updates = 0 if expected_datey == derivable_datey else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesBeforeReference(), before_datey))
        derivable_event = Event(None, ComesBeforeDerivable(), derivable_datey)
        Presence(person, Subject(), derivable_event)

        created, updated = self._app.extensions[Deriver].derive_person(person, ComesBeforeDerivable)

        self.assertEqual(0, created)
        self.assertEqual(expected_updates, updated)
        self.assertEqual(3, len(person.presences))
        self.assertEqual(expected_datey, derivable_event.date)

    @parameterized.expand([
        (None, None,),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), Date(1970, 1, 1)),
        (None, DateRange(None, None)),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(None, Date(1970, 1, 1))),
        (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1971, 1, 1))),
    ])
    @sync
    async def test_derive_create_comes_before_derivable_event(self, expected_datey: Optional[Datey], before_datey: Optional[Datey]):
        expected_creations = 0 if expected_datey is None else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesBeforeReference(), before_datey))

        created, updated = self._app.extensions[Deriver].derive_person(person, ComesBeforeCreatableDerivable)

        derived_presences = [presence for presence in person.presences if isinstance(presence.event.type, ComesBeforeCreatableDerivable)]
        self.assertEqual(expected_creations, len(derived_presences))
        if expected_creations:
            derived_presence = derived_presences[0]
            self.assertIsInstance(derived_presence.role, Subject)
            self.assertEqual(expected_datey, derived_presence.event.date)
        self.assertEqual(expected_creations, created)
        self.assertEqual(0, updated)
        self.assertEqual(2 + expected_creations, len(person.presences))

    @parameterized.expand([
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
    @sync
    async def test_derive_update_comes_after_derivable_event(self, expected_datey: Optional[Datey], after_datey: Optional[Datey], derivable_datey: Optional[Datey]):
        expected_updates = 0 if expected_datey == derivable_datey else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesAfterReference(), after_datey))
        derivable_event = Event(None, ComesAfterDerivable(), derivable_datey)
        Presence(person, Subject(), derivable_event)

        created, updated = self._app.extensions[Deriver].derive_person(person, ComesAfterDerivable)

        self.assertEqual(expected_datey, derivable_event.date)
        self.assertEqual(0, created)
        self.assertEqual(expected_updates, updated)
        self.assertEqual(3, len(person.presences))

    @parameterized.expand([
        (None, None),
        (None, Date()),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), Date(1970, 1, 1)),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1))),
        (DateRange(Date(1999, 12, 31), start_is_boundary=True), DateRange(None, Date(1999, 12, 31))),
        (DateRange(Date(1999, 12, 31), start_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31))),
        (DateRange(Date(1970, 1, 1), start_is_boundary=True), DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True)),
    ])
    @sync
    async def test_derive_create_comes_after_derivable_event(self, expected_datey: Optional[Datey], after_datey: Optional[Datey]):
        expected_creations = 0 if expected_datey is None else 1
        person = Person('P0')
        Presence(person, Subject(), Event(None, Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(None, ComesAfterReference(), after_datey))

        created, updated = self._app.extensions[Deriver].derive_person(person, ComesAfterCreatableDerivable)

        derived_presences = [presence for presence in person.presences if isinstance(presence.event.type, ComesAfterCreatableDerivable)]
        self.assertEqual(expected_creations, len(derived_presences))
        if expected_creations:
            derived_presence = derived_presences[0]
            self.assertIsInstance(derived_presence.role, Subject)
            self.assertEqual(expected_datey, derived_presence.event.date)
        self.assertEqual(expected_creations, created)
        self.assertEqual(0, updated)
        self.assertEqual(2 + expected_creations, len(person.presences))
