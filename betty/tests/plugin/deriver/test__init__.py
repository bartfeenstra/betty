from tempfile import TemporaryDirectory
from typing import Optional, Set, Type
from parameterized import parameterized

from betty.ancestry import Person, Presence, Subject, EventType, CreatableDerivableEventType, \
    DerivableEventType, Event, Residence
from betty.config import Configuration
from betty.asyncio import sync
from betty.locale import DateRange, Date, Datey
from betty.parse import parse
from betty.plugin.deriver import derive, Deriver
from betty.site import Site
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
        reference_presence = Presence(person, Subject(), Event(Residence()))
        reference_presence.event.date = Date(1970, 1, 1)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = None
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(3, len(person.presences))
        self.assertEquals(DateRange(None, Date(1970, 1, 1), end_is_boundary=True), person.start.date)
        self.assertEquals(DateRange(Date(1970, 1, 1), start_is_boundary=True), person.end.date)


class DeriveTest(TestCase):
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

        created, updated = derive(person, event_type_type)

        self.assertEquals(0, created)
        self.assertEquals(0, updated)
        self.assertEquals(0, len(person.presences))

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
        derivable_event = Event(Ignored())
        Presence(person, Subject(), derivable_event)

        created, updated = derive(person, event_type_type)

        self.assertEquals(0, created)
        self.assertEquals(0, updated)
        self.assertEquals(1, len(person.presences))
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
        Presence(person, Subject(), Event(Ignored()))
        derivable_event = Event(event_type_type())
        Presence(person, Subject(), derivable_event)

        created, updated = derive(person, event_type_type)

        self.assertEquals(0, created)
        self.assertEquals(0, updated)
        self.assertEquals(2, len(person.presences))
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
        Presence(person, Subject(), Event(Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(ComesBeforeReference(), before_datey))
        derivable_event = Event(ComesBeforeDerivable(), derivable_datey)
        Presence(person, Subject(), derivable_event)

        created, updated = derive(person, ComesBeforeDerivable)

        self.assertEquals(0, created)
        self.assertEquals(expected_updates, updated)
        self.assertEquals(3, len(person.presences))
        self.assertEquals(expected_datey, derivable_event.date)

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
        Presence(person, Subject(), Event(Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(ComesBeforeReference(), before_datey))

        created, updated = derive(person, ComesBeforeCreatableDerivable)

        derived_presences = [presence for presence in person.presences if isinstance(presence.event.type, ComesBeforeCreatableDerivable)]
        self.assertEquals(expected_creations, len(derived_presences))
        if expected_creations:
            derived_presence = derived_presences[0]
            self.assertIsInstance(derived_presence.role, Subject)
            self.assertEquals(expected_datey, derived_presence.event.date)
        self.assertEquals(expected_creations, created)
        self.assertEquals(0, updated)
        self.assertEquals(2 + expected_creations, len(person.presences))

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
        Presence(person, Subject(), Event(Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(ComesAfterReference(), after_datey))
        derivable_event = Event(ComesAfterDerivable(), derivable_datey)
        Presence(person, Subject(), derivable_event)

        created, updated = derive(person, ComesAfterDerivable)

        self.assertEquals(expected_datey, derivable_event.date)
        self.assertEquals(0, created)
        self.assertEquals(expected_updates, updated)
        self.assertEquals(3, len(person.presences))

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
        Presence(person, Subject(), Event(Ignored(), Date(0, 0, 0)))
        Presence(person, Subject(), Event(ComesAfterReference(), after_datey))

        created, updated = derive(person, ComesAfterCreatableDerivable)

        derived_presences = [presence for presence in person.presences if isinstance(presence.event.type, ComesAfterCreatableDerivable)]
        self.assertEquals(expected_creations, len(derived_presences))
        if expected_creations:
            derived_presence = derived_presences[0]
            self.assertIsInstance(derived_presence.role, Subject)
            self.assertEquals(expected_datey, derived_presence.event.date)
        self.assertEquals(expected_creations, created)
        self.assertEquals(0, updated)
        self.assertEquals(2 + expected_creations, len(person.presences))
