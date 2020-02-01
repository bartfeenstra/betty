from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Person, Presence, IdentifiableEvent, Event
from betty.config import Configuration
from betty.locale import Period, Date
from betty.parse import parse
from betty.plugins.deriver import Deriver
from betty.site import Site


class DeriverTest(TestCase):
    def test_post_parse(self):
        self.fail()
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            site = Site(configuration)
            person = Person('P0')
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = IdentifiableEvent('E0', Event.Type.BIRTH)
            person.presences.append(presence)
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertTrue(person.private)

    def test_derive_without_events(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            site = Site(configuration)
            person = Person('P0')
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertEquals(0, len(person.presences))

    def test_derive_with_events_without_dates(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            site = Site(configuration)
            person = Person('P0')
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = IdentifiableEvent('E0', Event.Type.MARRIAGE)
            person.presences.append(presence)
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertEquals(1, len(person.presences))

    def test_derive_birth_with_existing_birth_with_date(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            site = Site(configuration)
            person = Person('P0')
            birth_presence = Presence(Presence.Role.SUBJECT)
            birth_presence.event = IdentifiableEvent('E0', Event.Type.BIRTH)
            birth_presence.event.date = Date(1970, 2, 1)
            person.presences.append(birth_presence)
            other_presence = Presence(Presence.Role.SUBJECT)
            other_presence.event = IdentifiableEvent('E0', Event.Type.MARRIAGE)
            other_presence.event.date = Date(1970, 1, 1)
            person.presences.append(other_presence)
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertIsNotNone(birth_presence.event.date)
            self.assertEquals(Period(None, Date(1970, 2, 1)), birth_presence.event.date)

    def test_derive_birth_with_existing_birth_without_date(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Deriver] = {}
            site = Site(configuration)
            person = Person('P0')
            birth_presence = Presence(Presence.Role.SUBJECT)
            birth_presence.event = IdentifiableEvent('E0', Event.Type.BIRTH)
            person.presences.append(birth_presence)
            other_presence = Presence(Presence.Role.SUBJECT)
            other_presence.event = IdentifiableEvent('E0', Event.Type.MARRIAGE)
            other_presence.event.date = Date(1970, 1, 1)
            person.presences.append(other_presence)
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertIsNotNone(birth_presence.event.date)
            self.assertEquals(Period(None, Date(1970, 1, 1)), birth_presence.event.date)

    # def test_derive_birth_with_existing_event_with_date(self):
    #     self.fail()
    #
    # def test_derive_birth_with_existing_event_with_period(self):
    #     self.fail()
    #
    # def test_derive_death_with_existing_death_with_date(self):
    #     self.fail()
    #
    # def test_derive_death_with_existing_death_without_date(self):
    #     self.fail()
    #
    # def test_derive_death_with_existing_event_with_date(self):
    #     self.fail()
    #
    # def test_derive_death_with_existing_event_with_period(self):
    #     self.fail()
