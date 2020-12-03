from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Optional

from parameterized import parameterized

from betty.ancestry import Person, Presence, Event, Source, IdentifiableSource, File, \
    IdentifiableCitation, Subject, Attendee, Birth, Marriage, Death
from betty.config import Configuration
from betty.asyncio import sync
from betty.locale import Date, DateRange
from betty.parse import parse
from betty.plugin.privatizer import Privatizer, privatize_event, privatize_source, privatize_citation, privatize_person
from betty.site import Site
from betty.tests import TestCase


def _expand_person(generation: int):
    lifetime_threshold = 125
    multiplier = abs(generation) + 1 if generation < 0 else 1
    lifetime_threshold_year = datetime.now().year - lifetime_threshold * multiplier
    date_under_lifetime_threshold = Date(lifetime_threshold_year + 1, 1, 1)
    date_range_start_under_lifetime_threshold = DateRange(date_under_lifetime_threshold)
    date_range_end_under_lifetime_threshold = DateRange(None, date_under_lifetime_threshold)
    date_over_lifetime_threshold = Date(lifetime_threshold_year - 1, 1, 1)
    date_range_start_over_lifetime_threshold = DateRange(date_over_lifetime_threshold)
    date_range_end_over_lifetime_threshold = DateRange(None, date_over_lifetime_threshold)
    return parameterized.expand([
        # If there are no events for a person, they are private.
        (True, None, None),
        (True, True, None),
        (False, False, None),

        # Deaths and other end-of-life events are special, but only for the person whose privacy is being checked:
        # - If they're present without dates, the person isn't private.
        # - If they're present and their dates or date ranges' end dates are in the past, the person isn't private.
        (generation != 0, None, Event(Death(), date=Date(datetime.now().year, datetime.now().month, datetime.now().day))),
        (generation != 0, None, Event(Death(), date=date_under_lifetime_threshold)),
        (True, None, Event(Death(), date=date_range_start_under_lifetime_threshold)),
        (generation != 0, None, Event(Death(), date=date_range_end_under_lifetime_threshold)),
        (False, None, Event(Death(), date=date_over_lifetime_threshold)),
        (True, None, Event(Death(), date=date_range_start_over_lifetime_threshold)),
        (False, None, Event(Death(), date=date_range_end_over_lifetime_threshold)),
        (True, True, Event(Death())),
        (False, False, Event(Death())),
        (generation != 0, None, Event(Death())),

        # Regular events without dates do not affect privacy.
        (True, None, Event(Birth())),
        (True, True, Event(Birth())),
        (False, False, Event(Birth())),

        # Regular events with incomplete dates do not affect privacy.
        (True, None, Event(Birth(), date=Date())),
        (True, True, Event(Birth(), date=Date())),
        (False, False, Event(Birth(), date=Date())),

        # Regular events under the lifetime threshold do not affect privacy.
        (True, None, Event(Birth(), date=date_under_lifetime_threshold)),
        (True, True, Event(Birth(), date=date_under_lifetime_threshold)),
        (False, False, Event(Birth(), date=date_under_lifetime_threshold)),
        (True, None, Event(Birth(), date=date_range_start_under_lifetime_threshold)),
        (True, True, Event(Birth(), date=date_range_start_under_lifetime_threshold)),
        (False, False, Event(Birth(), date=date_range_start_under_lifetime_threshold)),
        (True, None, Event(Birth(), date=date_range_end_under_lifetime_threshold)),
        (True, True, Event(Birth(), date=date_range_end_under_lifetime_threshold)),
        (False, False, Event(Birth(), date=date_range_end_under_lifetime_threshold)),

        # Regular events over the lifetime threshold affect privacy.
        (False, None, Event(Birth(), date=date_over_lifetime_threshold)),
        (True, True, Event(Birth(), date=date_over_lifetime_threshold)),
        (False, False, Event(Birth(), date=date_over_lifetime_threshold)),
        (True, None, Event(Birth(), date=date_range_start_over_lifetime_threshold)),
        (True, True, Event(Birth(), date=date_range_start_over_lifetime_threshold)),
        (False, False, Event(Birth(), date=date_range_start_over_lifetime_threshold)),
        (False, None, Event(Birth(), date=date_range_end_over_lifetime_threshold)),
        (True, True, Event(Birth(), date=date_range_end_over_lifetime_threshold)),
        (False, False, Event(Birth(), date=date_range_end_over_lifetime_threshold)),
    ])


class PrivatizerTest(TestCase):
    @sync
    async def test_post_parse(self):
        person = Person('P0')
        Presence(person, Subject(), Event(Birth()))

        source_file = File('F0', __file__)
        source = IdentifiableSource('S0', 'The Source')
        source.private = True
        source.files.append(source_file)

        citation_file = File('F0', __file__)
        citation_source = Source('The Source')
        citation = IdentifiableCitation('C0', citation_source)
        citation.private = True
        citation.files.append(citation_file)

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Privatizer] = None
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                site.ancestry.sources[source.id] = source
                site.ancestry.citations[citation.id] = citation
                await parse(site)

            self.assertTrue(person.private)
            self.assertTrue(source_file.private)
            self.assertTrue(citation_file.private)

    def test_privatize_person_should_not_privatize_if_public(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.files.append(citation_file)
        event_as_subject = Event(Birth())
        event_as_attendee = Event(Marriage())
        person_file = File('F2', __file__)
        person = Person('P0')
        person.private = False
        person.citations.append(citation)
        person.files.append(person_file)
        Presence(person, Subject(), event_as_subject)
        Presence(person, Attendee(), event_as_attendee)
        privatize_person(person, 125)
        self.assertEqual(False, person.private)
        self.assertIsNone(citation.private)
        self.assertIsNone(source.private)
        self.assertIsNone(person_file.private)
        self.assertIsNone(citation_file.private)
        self.assertIsNone(source_file.private)
        self.assertIsNone(event_as_subject.private)
        self.assertIsNone(event_as_attendee.private)

    def test_privatize_person_should_privatize_if_private(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.files.append(citation_file)
        event_as_subject = Event(Birth())
        event_as_attendee = Event(Marriage())
        person_file = File('F2', __file__)
        person = Person('P0')
        person.private = True
        person.citations.append(citation)
        person.files.append(person_file)
        Presence(person, Subject(), event_as_subject)
        Presence(person, Attendee(), event_as_attendee)
        privatize_person(person, 125)
        self.assertTrue(person.private)
        self.assertTrue(citation.private)
        self.assertTrue(source.private)
        self.assertTrue(person_file.private)
        self.assertTrue(citation_file.private)
        self.assertTrue(source_file.private)
        self.assertTrue(event_as_subject.private)
        self.assertIsNone(event_as_attendee.private)

    @_expand_person(0)
    def test_privatize_person_without_relatives(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        if event is not None:
            Presence(person, Subject(), event)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    @_expand_person(1)
    def test_privatize_person_with_child(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        if event is not None:
            Presence(child, Subject(), event)
        person.children.append(child)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    @_expand_person(2)
    def test_privatize_person_with_grandchild(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        if event is not None:
            Presence(grandchild, Subject(), event)
        child.children.append(grandchild)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    @_expand_person(3)
    def test_privatize_person_with_great_grandchild(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        child.children.append(grandchild)
        great_grandchild = Person('P2')
        if event is not None:
            Presence(great_grandchild, Subject(), event)
        grandchild.children.append(great_grandchild)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    @_expand_person(-1)
    def test_privatize_person_with_parent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        if event is not None:
            Presence(parent, Subject(), event)
        person.parents.append(parent)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    @_expand_person(-2)
    def test_privatize_person_with_grandparent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        if event is not None:
            Presence(grandparent, Subject(), event)
        parent.parents.append(grandparent)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    @_expand_person(-3)
    def test_privatize_person_with_great_grandparent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        parent.parents.append(grandparent)
        great_grandparent = Person('P2')
        if event is not None:
            Presence(great_grandparent, Subject(), event)
        grandparent.parents.append(great_grandparent)
        privatize_person(person, 125)
        self.assertEquals(expected, person.private)

    def test_privatize_event_should_not_privatize_if_public(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.files.append(citation_file)
        event_file = File('F1', __file__)
        event = Event(Birth())
        event.private = False
        event.citations.append(citation)
        event.files.append(event_file)
        person = Person('P0')
        Presence(person, Subject(), event)
        privatize_event(event)
        self.assertEqual(False, event.private)
        self.assertIsNone(event_file.private)
        self.assertIsNone(citation.private)
        self.assertIsNone(source.private)
        self.assertIsNone(citation_file.private)
        self.assertIsNone(source_file.private)
        self.assertIsNone(person.private)

    def test_privatize_event_should_privatize_if_private(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.files.append(citation_file)
        event_file = File('F1', __file__)
        event = Event(Birth())
        event.private = True
        event.citations.append(citation)
        event.files.append(event_file)
        person = Person('P0')
        Presence(person, Subject(), event)
        privatize_event(event)
        self.assertTrue(event.private)
        self.assertTrue(event_file.private)
        self.assertTrue(citation.private)
        self.assertTrue(source.private)
        self.assertTrue(citation_file.private)
        self.assertTrue(source_file.private)
        self.assertIsNone(person.private)

    def test_privatize_source_should_not_privatize_if_public(self):
        file = File('F0', __file__)
        source = IdentifiableSource('S0', 'The Source')
        source.private = False
        source.files.append(file)
        privatize_source(source)
        self.assertEqual(False, source.private)
        self.assertIsNone(file.private)

    def test_privatize_source_should_privatize_if_private(self):
        file = File('F0', __file__)
        source = IdentifiableSource('S0', 'The Source')
        source.private = True
        source.files.append(file)
        privatize_source(source)
        self.assertTrue(source.private)
        self.assertTrue(file.private)

    def test_privatize_citation_should_not_privatize_if_public(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.private = False
        citation.files.append(citation_file)
        privatize_citation(citation)
        self.assertEqual(False, citation.private)
        self.assertIsNone(source.private)
        self.assertIsNone(citation_file.private)
        self.assertIsNone(source_file.private)

    def test_privatize_citation_should_privatize_if_private(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.private = True
        citation.files.append(citation_file)
        privatize_citation(citation)
        self.assertTrue(citation.private)
        self.assertTrue(source.private)
        self.assertTrue(citation_file.private)
        self.assertTrue(source_file.private)
