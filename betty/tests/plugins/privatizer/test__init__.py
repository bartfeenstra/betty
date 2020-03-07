from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Ancestry, Person, Presence, IdentifiableEvent, Event, Source, IdentifiableSource, File, \
    IdentifiableCitation
from betty.config import Configuration
from betty.locale import Date, DateRange
from betty.parse import parse
from betty.plugins.privatizer import Privatizer
from betty.site import Site


def _expand_person(generation: int):
    multiplier = abs(generation) + 1 if generation < 0 else 1
    threshold_year = datetime.now().year - 100 * multiplier
    date_under_threshold = Date(threshold_year + 1, 1, 1)
    date_range_start_under_threshold = DateRange(date_under_threshold)
    date_range_end_under_threshold = DateRange(None, date_under_threshold)
    date_over_threshold = Date(threshold_year - 1, 1, 1)
    date_range_start_over_threshold = DateRange(date_over_threshold)
    date_range_end_over_threshold = DateRange(None, date_over_threshold)
    return parameterized.expand([
        # If there are no events for a person, their privacy does not change.
        (True, None, None),
        (True, True, None),
        (False, False, None),
        # Deaths and burials are special, and their existence prevents generation 0 from being private even without
        # having passed the usual threshold.
        (generation != 0, None, IdentifiableEvent('E0', Event.Type.DEATH, date=Date(datetime.now().year, datetime.now().month, datetime.now().day))),
        (generation != 0, None, IdentifiableEvent('E0', Event.Type.DEATH, date=date_under_threshold)),
        (True, None, IdentifiableEvent('E0', Event.Type.DEATH, date=date_range_start_under_threshold)),
        (generation != 0, None, IdentifiableEvent('E0', Event.Type.DEATH, date=date_range_end_under_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.DEATH)),
        (False, False, IdentifiableEvent('E0', Event.Type.DEATH)),
        (generation != 0, None, IdentifiableEvent('E0', Event.Type.BURIAL, date=Date(datetime.now().year, datetime.now().month, datetime.now().day))),
        (generation != 0, None, IdentifiableEvent('E0', Event.Type.BURIAL, date=date_under_threshold)),
        (True, None, IdentifiableEvent('E0', Event.Type.BURIAL, date=date_range_start_under_threshold)),
        (generation != 0, None, IdentifiableEvent('E0', Event.Type.BURIAL, date=date_range_end_under_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BURIAL)),
        (False, False, IdentifiableEvent('E0', Event.Type.BURIAL)),
        # Regular events without dates do not affect privacy.
        (True, None, IdentifiableEvent('E0', Event.Type.BIRTH)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH)),
        # Regular events with incomplete dates do not affect privacy.
        (True, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=Date())),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=Date())),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=Date())),
        # Regular events under the lifetime threshold do not affect privacy.
        (True, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_under_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_under_threshold)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_under_threshold)),
        (True, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_start_under_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_start_under_threshold)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_start_under_threshold)),
        (True, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_end_under_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_end_under_threshold)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_end_under_threshold)),
        # Regular events over the lifetime threshold affect privacy.
        (False, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_over_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_over_threshold)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_over_threshold)),
        (False, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_start_over_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_start_over_threshold)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_start_over_threshold)),
        (False, None, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_end_over_threshold)),
        (True, True, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_end_over_threshold)),
        (False, False, IdentifiableEvent('E0', Event.Type.BIRTH, date=date_range_end_over_threshold)),
    ])


class PrivatizerTest(TestCase):
    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Privatizer] = {}
            site = Site(configuration)
            person = Person('P0')
            Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('E0', Event.Type.BIRTH))
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertTrue(person.private)

    def test_privatize_person_should_not_privatize_if_public(self):
        ancestry = Ancestry()
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.files.append(citation_file)
        person_file = File('F2', __file__)
        person = Person('P0')
        person.private = False
        person.citations.append(citation)
        person.files.append(person_file)
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEqual(False, person.private)
        self.assertIsNone(citation.private)
        self.assertIsNone(source.private)
        self.assertIsNone(person_file.private)
        self.assertIsNone(citation_file.private)
        self.assertIsNone(source_file.private)

    def test_privatize_person_should_privatize_if_private(self):
        ancestry = Ancestry()
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.files.append(citation_file)
        person_file = File('F2', __file__)
        person = Person('P0')
        person.private = True
        person.citations.append(citation)
        person.files.append(person_file)
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertTrue(person.private)
        self.assertTrue(citation.private)
        self.assertTrue(source.private)
        self.assertTrue(person_file.private)
        self.assertTrue(citation_file.private)
        self.assertTrue(source_file.private)

    @_expand_person(0)
    def test_privatize_person_without_relatives(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        if event is not None:
            Presence(person, Presence.Role.SUBJECT, event)
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand_person(1)
    def test_privatize_person_with_child(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        child = Person('P1')
        if event is not None:
            Presence(child, Presence.Role.SUBJECT, event)
        person.children.append(child)
        ancestry.people[person.id] = person
        ancestry.people[child.id] = child
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand_person(2)
    def test_privatize_person_with_grandchild(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        if event is not None:
            Presence(grandchild, Presence.Role.SUBJECT, event)
        child.children.append(grandchild)
        ancestry.people[person.id] = person
        ancestry.people[child.id] = child
        ancestry.people[grandchild.id] = grandchild
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand_person(3)
    def test_privatize_person_with_great_grandchild(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        child.children.append(grandchild)
        great_grandchild = Person('P2')
        if event is not None:
            Presence(great_grandchild, Presence.Role.SUBJECT, event)
        grandchild.children.append(great_grandchild)
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand_person(-1)
    def test_privatize_person_with_parent(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        if event is not None:
            Presence(parent, Presence.Role.SUBJECT, event)
        person.parents.append(parent)
        ancestry.people[person.id] = person
        ancestry.people[parent.id] = parent
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand_person(-2)
    def test_privatize_person_with_grandparent(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        if event is not None:
            Presence(grandparent, Presence.Role.SUBJECT, event)
        parent.parents.append(grandparent)
        ancestry.people[person.id] = person
        ancestry.people[parent.id] = parent
        ancestry.people[grandparent.id] = grandparent
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand_person(-3)
    def test_privatize_person_with_great_grandparent(self, expected, private, event: Optional[Event]):
        ancestry = Ancestry()
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        parent.parents.append(grandparent)
        great_grandparent = Person('P2')
        if event is not None:
            Presence(great_grandparent, Presence.Role.SUBJECT, event)
        grandparent.parents.append(great_grandparent)
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    def test_privatize_source_should_not_privatize_if_public(self):
        ancestry = Ancestry()
        file = File('F0', __file__)
        source = IdentifiableSource('S0', 'The Source')
        source.private = False
        source.files.append(file)
        ancestry.sources[source.id] = source
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEqual(False, source.private)
        self.assertIsNone(file.private)

    def test_privatize_source_should_privatize_if_private(self):
        ancestry = Ancestry()
        file = File('F0', __file__)
        source = IdentifiableSource('S0', 'The Source')
        source.private = True
        source.files.append(file)
        ancestry.sources[source.id] = source
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertTrue(source.private)
        self.assertTrue(file.private)

    def test_privatize_citation_should_not_privatize_if_public(self):
        ancestry = Ancestry()
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.private = False
        citation.files.append(citation_file)
        ancestry.citations[citation.id] = citation
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEqual(False, citation.private)
        self.assertIsNone(source.private)
        self.assertIsNone(citation_file.private)
        self.assertIsNone(source_file.private)

    def test_privatize_citation_should_privatize_if_private(self):
        ancestry = Ancestry()
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = IdentifiableCitation('C0', source)
        citation.private = True
        citation.files.append(citation_file)
        ancestry.citations[citation.id] = citation
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertTrue(citation.private)
        self.assertTrue(source.private)
        self.assertTrue(citation_file.private)
        self.assertTrue(source_file.private)
