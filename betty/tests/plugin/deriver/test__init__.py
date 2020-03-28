from tempfile import TemporaryDirectory
from typing import Optional
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Person, Presence, IdentifiableEvent, Event
from betty.config import Configuration
from betty.functools import sync
from betty.locale import DateRange, Date, Datey
from betty.parse import parse
from betty.plugin.deriver import Deriver
from betty.site import Site


class DeriverTest(TestCase):
    @sync
    async def test_post_parse(self):
        person = Person('P0')
        other_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.MARRIAGE))
        other_presence.event.date = Date(1970, 1, 1)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(3, len(person.presences))
        self.assertEquals(DateRange(None, Date(1970, 1, 1)), person.start.date)
        self.assertEquals(DateRange(Date(1970, 1, 1)), person.end.date)

    @sync
    async def test_derive_without_events(self):
        person = Person('P0')

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(0, len(person.presences))

    @sync
    async def test_derive_with_events_without_dates(self):
        person = Person('P0')
        Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.MARRIAGE))

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(1, len(person.presences))

    @parameterized.expand([
        (DateRange(None, Date(1970, 1, 1)), None,),
        (Date(1970, 2, 2), Date(1970, 2, 2),),
        (DateRange(None, Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2)),),
        (DateRange(Date(1969, 2, 1), Date(1970, 1, 1)), DateRange(Date(1969, 2, 1)),),
    ])
    @sync
    async def test_derive_birth_with_existing_birth(self, expected: Datey, existing_datey: Optional[Datey]):
        person = Person('P0')
        birth_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.BIRTH))
        birth_presence.event.date = existing_datey
        other_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.MARRIAGE))
        other_presence.event.date = Date(1970, 1, 1)
        irrelevant_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E1', Event.Type.DIVORCE))
        irrelevant_presence.event.date = Date(1971, 1, 1)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(4, len(person.presences))
        self.assertEquals(expected, birth_presence.event.date)

    @parameterized.expand([
        (Date(1971, 1, 1),),
        (DateRange(Date(1971, 1, 1)),),
        (DateRange(None, Date(1971, 1, 1)),),
    ])
    @sync
    async def test_derive_birth_with_existing_event(self, other_date: Datey):
        person = Person('P0')
        other_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.MARRIAGE))
        other_presence.event.date = other_date
        irrelevant_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E1', Event.Type.DIVORCE))
        irrelevant_presence.event.date = Date(1972, 1, 1)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(4, len(person.presences))
        self.assertEquals(DateRange(None, Date(1971, 1, 1)), person.start.date)

    @parameterized.expand([
        (DateRange(Date(1971, 1, 1)), None,),
        (Date(1970, 2, 2), Date(1970, 2, 2),),
        (DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2)),),
        (DateRange(Date(1971, 1, 1), Date(1972, 1, 1)), DateRange(None, Date(1972, 1, 1)),),
    ])
    @sync
    async def test_derive_death_with_existing_death(self, expected: Datey, existing_datey: Optional[Datey]):
        person = Person('P0')
        death_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.DEATH))
        death_presence.event.date = existing_datey
        other_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.MARRIAGE))
        other_presence.event.date = Date(1971, 1, 1)
        irrelevant_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E1', Event.Type.DIVORCE))
        irrelevant_presence.event.date = Date(1970, 1, 1)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(4, len(person.presences))
        self.assertEquals(expected, death_presence.event.date)

    @parameterized.expand([
        (Date(1971, 1, 1),),
        (DateRange(Date(1971, 1, 1)),),
        (DateRange(None, Date(1971, 1, 1)),),
    ])
    @sync
    async def test_derive_death_with_existing_event(self, other_date: Datey):
        person = Person('P0')
        other_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.MARRIAGE))
        other_presence.event.date = other_date
        irrelevant_presence = Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E1', Event.Type.DIVORCE))
        irrelevant_presence.event.date = Date(1970, 1, 1)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)

        self.assertEquals(4, len(person.presences))
        self.assertEquals(DateRange(Date(1971, 1, 1)), person.end.date)
