from gettext import NullTranslations
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from unittest.mock import Mock

from geopy import Point
from parameterized import parameterized

from betty.locale import Date, Translations
from betty.media_type import MediaType
from betty.model import Entity
from betty.model.ancestry import Person, Event, Place, File, Note, Presence, PlaceName, PersonName, Subject, \
    Enclosure, Described, Dated, HasPrivacy, HasMediaType, Link, HasLinks, HasNotes, HasFiles, Source, Citation, \
    HasCitations, PresenceRole, Attendee, Beneficiary, Witness, EventType
from betty.model.event_type import Burial, Birth
from betty.tests import TestCase


class HasPrivacyTest(TestCase):
    def test_date(self) -> None:
        sut = HasPrivacy()
        self.assertIsNone(sut.private)


class DatedTest(TestCase):
    def test_date(self) -> None:
        sut = Dated()
        self.assertIsNone(sut.date)


class NoteTest(TestCase):
    def test_id(self) -> None:
        note_id = 'N1'
        sut = Note(note_id, 'Betty wrote this.')
        self.assertEqual(note_id, sut.id)

    def test_text(self) -> None:
        text = 'Betty wrote this.'
        sut = Note('N1', text)
        self.assertEqual(text, sut.text)


class HasNotesTest(TestCase):
    class _HasNotes(HasNotes, Entity):
        pass

    def test_notes(self) -> None:
        sut = self._HasNotes()
        self.assertSequenceEqual([], sut.notes)


class DescribedTest(TestCase):
    def test_description(self) -> None:
        sut = Described()
        self.assertIsNone(sut.description)


class HasMediaTypeTest(TestCase):
    def test_media_type(self) -> None:
        sut = HasMediaType()
        self.assertIsNone(sut.media_type)


class LinkTest(TestCase):
    def test_url(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        self.assertEqual(url, sut.url)

    def test_media_type(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        self.assertIsNone(sut.media_type)

    def test_locale(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        self.assertIsNone(sut.locale)

    def test_description(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        self.assertIsNone(sut.description)

    def test_relationship(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        self.assertIsNone(sut.relationship)

    def test_label(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        self.assertIsNone(sut.label)


class HasLinksTest(TestCase):
    def test_links(self) -> None:
        sut = HasLinks()
        self.assertEqual(set(), sut.links)


class FileTest(TestCase):
    def test_id(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertEqual(file_id, sut.id)

    def test_private(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertIsNone(sut.private)
        private = True
        sut.private = private
        self.assertEqual(private, sut.private)

    def test_media_type(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertIsNone(sut.media_type)
        media_type = MediaType('text/plain')
        sut.media_type = media_type
        self.assertEqual(media_type, sut.media_type)

    def test_path_with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            file_path = Path(f.name)
            sut = File(file_id, file_path)
            self.assertEqual(file_path, sut.path)

    def test_path_with_str(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertEqual(Path(f.name), sut.path)

    def test_description(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertIsNone(sut.description)
        description = 'Hi, my name is Betty!'
        sut.description = description
        self.assertEqual(description, sut.description)

    def test_notes(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.notes)
        notes = [Mock(Note), Mock(Note)]
        sut.notes = notes
        self.assertCountEqual(notes, sut.notes)

    def test_entities(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.entities)

        class _HasFiles(Entity, HasFiles):
            pass
        entities = [_HasFiles(), _HasFiles()]
        sut.entities = entities
        self.assertCountEqual(entities, sut.entities)

    def test_citations(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.citations)


class HasFilesTest(TestCase):
    def test_files(self) -> None:
        class _HasFiles(Entity, HasFiles):
            pass
        sut = _HasFiles()
        self.assertCountEqual([], sut.files)
        files = [Mock(File), Mock(File)]
        sut.files = files
        self.assertCountEqual(files, sut.files)


class SourceTest(TestCase):
    def test_id(self) -> None:
        source_id = 'S1'
        sut = Source(source_id)
        self.assertEqual(source_id, sut.id)

    def test_name(self) -> None:
        name = 'The Source'
        sut = Source(None, name)
        self.assertEqual(name, sut.name)

    def test_contained_by(self) -> None:
        contained_by_source = Source(None)
        sut = Source(None)
        self.assertIsNone(sut.contained_by)
        sut.contained_by = contained_by_source
        self.assertEqual(contained_by_source, sut.contained_by)

    def test_contains(self) -> None:
        contains_source = Source(None)
        sut = Source(None)
        self.assertCountEqual([], sut.contains)
        sut.contains = [contains_source]
        self.assertCountEqual([contains_source], sut.contains)

    def test_citations(self) -> None:
        sut = Source(None)
        self.assertCountEqual([], sut.citations)

    def test_author(self) -> None:
        sut = Source(None)
        self.assertIsNone(sut.author)
        author = 'Me'
        sut.author = author
        self.assertEqual(author, sut.author)

    def test_publisher(self) -> None:
        sut = Source(None)
        self.assertIsNone(sut.publisher)
        publisher = 'Me'
        sut.publisher = publisher
        self.assertEqual(publisher, sut.publisher)

    def test_date(self) -> None:
        sut = Source(None)
        self.assertIsNone(sut.date)

    def test_files(self) -> None:
        sut = Source(None)
        self.assertCountEqual([], sut.files)

    def test_links(self) -> None:
        sut = Source(None)
        self.assertCountEqual([], sut.links)

    def test_private(self) -> None:
        sut = Source(None)
        self.assertIsNone(sut.private)
        private = True
        sut.private = private
        self.assertEqual(private, sut.private)


class CitationTest(TestCase):
    def test_id(self) -> None:
        citation_id = 'C1'
        sut = Citation(citation_id, Mock(Source))
        self.assertEqual(citation_id, sut.id)

    def test_facts(self) -> None:
        class _HasCitations(Entity, HasCitations):
            pass
        fact = _HasCitations()
        sut = Citation(None, Mock(Source))
        self.assertCountEqual([], sut.facts)
        sut.facts = [fact]
        self.assertCountEqual([fact], sut.facts)

    def test_source(self) -> None:
        source = Mock(Source)
        sut = Citation(None, source)
        self.assertEqual(source, sut.source)

    def test_location(self) -> None:
        sut = Citation(None, Mock(Source))
        self.assertIsNone(sut.location)
        location = 'Somewhere'
        sut.location = location
        self.assertEqual(location, sut.location)

    def test_date(self) -> None:
        sut = Citation(None, Mock(Source))
        self.assertIsNone(sut.date)

    def test_files(self) -> None:
        sut = Citation(None, Mock(Source))
        self.assertCountEqual([], sut.files)

    def test_private(self) -> None:
        sut = Citation(None, Mock(Source))
        self.assertIsNone(sut.private)
        private = True
        sut.private = private
        self.assertEqual(private, sut.private)


class HasCitationsTest(TestCase):
    def test_citations(self) -> None:
        class _HasCitations(Entity, HasCitations):
            pass
        sut = _HasCitations()
        self.assertCountEqual([], sut.citations)
        citation = Mock(Citation)
        sut.citations = [citation]
        self.assertCountEqual([citation], sut.citations)


class PlaceNameTest(TestCase):
    @parameterized.expand([
        (True, PlaceName('Ikke'), PlaceName('Ikke')),
        (True, PlaceName('Ikke', 'nl-NL'), PlaceName('Ikke', 'nl-NL')),
        (False, PlaceName('Ikke', 'nl-NL'), PlaceName('Ikke', 'nl-BE')),
        (False, PlaceName('Ikke', 'nl-NL'), PlaceName('Ik', 'nl-NL')),
        (False, PlaceName('Ikke'), PlaceName('Ik')),
        (False, PlaceName('Ikke'), None),
        (False, PlaceName('Ikke'), 'not-a-place-name'),
    ])
    def test_eq(self, expected, a, b) -> None:
        self.assertEqual(expected, a == b)

    def test_str(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name)
        self.assertEqual(name, str(sut))

    def test_name(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name)
        self.assertEqual(name, sut.name)

    def test_locale(self) -> None:
        locale = 'nl-NL'
        sut = PlaceName('Ikke', locale=locale)
        self.assertEqual(locale, sut.locale)

    def test_date(self) -> None:
        date = Date()
        sut = PlaceName('Ikke', date=date)
        self.assertEqual(date, sut.date)


class EnclosureTest(TestCase):
    def test_encloses(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        self.assertEqual(encloses, sut.encloses)

    def test_enclosed_by(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        self.assertEqual(enclosed_by, sut.enclosed_by)

    def test_date(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        date = Date()
        self.assertIsNone(sut.date)
        sut.date = date
        self.assertEqual(date, sut.date)

    def test_citations(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        citation = Mock(Citation)
        self.assertIsNone(sut.date)
        sut.citations = [citation]
        self.assertCountEqual([citation], sut.citations)


class PlaceTest(TestCase):
    def test_events(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        event = Event('1', Birth())
        sut.events.append(event)
        self.assertIn(event, sut.events)
        self.assertEqual(sut, event.place)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertEqual(None, event.place)

    def test_enclosed_by(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        self.assertCountEqual([], sut.enclosed_by)
        enclosing_place = Place('P2', [PlaceName('The Other Place')])
        enclosure = Enclosure(sut, enclosing_place)
        self.assertIn(enclosure, sut.enclosed_by)
        self.assertEqual(sut, enclosure.encloses)
        sut.enclosed_by.remove(enclosure)
        self.assertCountEqual([], sut.enclosed_by)
        self.assertIsNone(enclosure.encloses)

    def test_encloses(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        self.assertCountEqual([], sut.encloses)
        enclosed_place = Place('P2', [PlaceName('The Other Place')])
        enclosure = Enclosure(enclosed_place, sut)
        self.assertIn(enclosure, sut.encloses)
        self.assertEqual(sut, enclosure.enclosed_by)
        sut.encloses.remove(enclosure)
        self.assertCountEqual([], sut.encloses)
        self.assertIsNone(enclosure.enclosed_by)

    def test_id(self) -> None:
        place_id = 'C1'
        sut = Place(place_id, [PlaceName('one')])
        self.assertEqual(place_id, sut.id)

    def test_links(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        self.assertCountEqual([], sut.links)

    def test_names(self) -> None:
        name = PlaceName('The Place')
        sut = Place('P1', [name])
        self.assertCountEqual([name], sut.names)

    def test_coordinates(self) -> None:
        name = PlaceName('The Place')
        sut = Place('P1', [name])
        coordinates = Point()
        sut.coordinates = coordinates
        self.assertEqual(coordinates, sut.coordinates)


class SubjectTest(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Subject.name(), str)
        self.assertNotEqual('', Subject.name)

    def test_label(self) -> None:
        sut = Subject()
        with Translations(NullTranslations()):
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class WitnessTest(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Witness.name(), str)
        self.assertNotEqual('', Witness.name)

    def test_label(self) -> None:
        sut = Witness()
        with Translations(NullTranslations()):
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class BeneficiaryTest(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Beneficiary.name(), str)
        self.assertNotEqual('', Beneficiary.name)

    def test_label(self) -> None:
        sut = Beneficiary()
        with Translations(NullTranslations()):
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class AttendeeTest(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Attendee.name(), str)
        self.assertNotEqual('', Attendee.name)

    def test_label(self) -> None:
        sut = Attendee()
        with Translations(NullTranslations()):
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class PresenceTest(TestCase):
    def test_person(self) -> None:
        person = Mock(Person)
        sut = Presence(person, Mock(PresenceRole), Mock(Event))
        self.assertEqual(person, sut.person)

    def test_event(self) -> None:
        role = Mock(PresenceRole)
        sut = Presence(Mock(Person), role, Mock(Event))
        self.assertEqual(role, sut.role)

    def test_role(self) -> None:
        event = Mock(Event)
        sut = Presence(Mock(Person), Mock(PresenceRole), event)
        self.assertEqual(event, sut.event)


class EventTest(TestCase):
    def test_id(self) -> None:
        event_id = 'E1'
        sut = Event(event_id, Mock(EventType))
        self.assertEqual(event_id, sut.id)

    def test_place(self) -> None:
        place = Place('1', [PlaceName('one')])
        sut = Event(None, Mock(EventType))
        sut.place = place
        self.assertEqual(place, sut.place)
        self.assertIn(sut, place.events)
        sut.place = None
        self.assertEqual(None, sut.place)
        self.assertNotIn(sut, place.events)

    def test_presences(self) -> None:
        person = Person('P1')
        sut = Event(None, Mock(EventType))
        presence = Presence(person, Subject(), sut)
        sut.presences.append(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEqual(sut, presence.event)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.event)

    def test_date(self) -> None:
        sut = Event(None, Mock(EventType))
        self.assertIsNone(sut.date)
        date = Mock(Date)
        sut.date = date
        self.assertEqual(date, sut.date)

    def test_files(self) -> None:
        sut = Event(None, Mock(EventType))
        self.assertCountEqual([], sut.files)

    def test_citations(self) -> None:
        sut = Event(None, Mock(EventType))
        self.assertCountEqual([], sut.citations)

    def test_description(self) -> None:
        sut = Event(None, Mock(EventType))
        self.assertIsNone(sut.description)

    def test_private(self) -> None:
        sut = Event(None, Mock(EventType))
        self.assertIsNone(sut.private)

    def test_type(self) -> None:
        event_type = Mock(EventType)
        sut = Event(None, event_type)
        self.assertEqual(event_type, sut.type)

    def test_associated_files(self) -> None:
        file1 = Mock(File)
        file2 = Mock(File)
        file3 = Mock(File)
        file4 = Mock(File)
        sut = Event(None, Mock(EventType))
        sut.files = [file1, file2, file1]
        citation = Mock(Citation)
        citation.associated_files = [file3, file4, file2]
        sut.citations = [citation]
        self.assertEqual([file1, file2, file3, file4], list(sut.associated_files))


class PersonNameTest(TestCase):
    def test_person(self) -> None:
        person = Person('1')
        sut = PersonName(person, 'Janet', 'Not a Girl')
        self.assertEqual(person, sut.person)
        self.assertCountEqual([sut], person.names)
        sut.person = None
        self.assertIsNone(sut.person)
        self.assertCountEqual([], person.names)

    def test_locale(self) -> None:
        person = Person('1')
        sut = PersonName(person, 'Janet', 'Not a Girl')
        self.assertIsNone(sut.locale)

    def test_citations(self) -> None:
        person = Person('1')
        sut = PersonName(person, 'Janet', 'Not a Girl')
        self.assertCountEqual([], sut.citations)

    def test_individual(self) -> None:
        person = Person('1')
        individual = 'Janet'
        sut = PersonName(person, individual, 'Not a Girl')
        self.assertEqual(individual, sut.individual)

    def test_affiliation(self) -> None:
        person = Person('1')
        affiliation = 'Not a Girl'
        sut = PersonName(person, 'Janet', affiliation)
        self.assertEqual(affiliation, sut.affiliation)

    @parameterized.expand([
        (True, PersonName(Person('1'), 'Janet', 'Not a Girl'), PersonName(Person('1'), 'Janet', 'Not a Girl')),
        (True, PersonName(Person('1'), 'Janet'), PersonName(Person('1'), 'Janet')),
        (True, PersonName(Person('1'), None, 'Not a Girl'), PersonName(Person('1'), None, 'Not a Girl')),
        (False, PersonName(Person('1'), 'Janet'), PersonName(Person('1'), None, 'Not a Girl')),
        (False, PersonName(Person('1'), 'Janet', 'Not a Girl'), None),
        (False, PersonName(Person('1'), 'Janet', 'Not a Girl'), True),
        (False, PersonName(Person('1'), 'Janet', 'Not a Girl'), 9),
        (False, PersonName(Person('1'), 'Janet', 'Not a Girl'), object()),
    ])
    def test_eq(self, expected: bool, left: PersonName, right: Any) -> None:
        self.assertEqual(expected, left == right)

    @parameterized.expand([
        (False, PersonName(Person('1'), 'Janet', 'Not a Girl'), PersonName(Person('1'), 'Janet', 'Not a Girl')),
        (True, PersonName(Person('1'), 'Janet', 'Not a Girl'), PersonName(Person('1'), 'Not a Girl', 'Janet')),
        (True, PersonName(Person('1'), 'Janet', 'Not a Girl'), None),
    ])
    def test_gt(self, expected: bool, left: PersonName, right: Any) -> None:
        self.assertEqual(expected, left > right)


class PersonTest(TestCase):
    def test_parents(self) -> None:
        sut = Person('1')
        parent = Person('2')
        sut.parents.append(parent)
        self.assertCountEqual([parent], sut.parents)
        self.assertCountEqual([sut], parent.children)
        sut.parents.remove(parent)
        self.assertCountEqual([], sut.parents)
        self.assertCountEqual([], parent.children)

    def test_children(self) -> None:
        sut = Person('1')
        child = Person('2')
        sut.children.append(child)
        self.assertCountEqual([child], sut.children)
        self.assertCountEqual([sut], child.parents)
        sut.children.remove(child)
        self.assertCountEqual([], sut.children)
        self.assertCountEqual([], child.parents)

    def test_presences(self) -> None:
        event = Event(None, Birth())
        sut = Person('1')
        presence = Presence(sut, Subject(), event)
        sut.presences.append(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEqual(sut, presence.person)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.person)

    def test_names(self) -> None:
        sut = Person('1')
        name = PersonName(sut, 'Janet', 'Not a Girl')
        self.assertCountEqual([name], sut.names)
        self.assertEqual(sut, name.person)
        sut.names.remove(name)
        self.assertCountEqual([], sut.names)
        self.assertIsNone(name.person)

    def test_id(self) -> None:
        person_id = 'P1'
        sut = Person(person_id)
        self.assertEqual(person_id, sut.id)

    def test_files(self) -> None:
        sut = Source(None)
        self.assertCountEqual([], sut.files)

    def test_citations(self) -> None:
        sut = Source(None)
        self.assertCountEqual([], sut.citations)

    def test_links(self) -> None:
        sut = Source(None)
        self.assertCountEqual([], sut.links)

    def test_private(self) -> None:
        sut = Event(None, Mock(EventType))
        self.assertIsNone(sut.private)

    def test_name_with_names(self) -> None:
        sut = Person('P1')
        name = PersonName(sut)
        self.assertEqual(name, sut.name)

    def test_name_without_names(self) -> None:
        self.assertIsNone(Person('P1').name)

    def test_alternative_names(self) -> None:
        sut = Person('P1')
        PersonName(sut, 'Janet', 'Not a Girl')
        alternative_name = PersonName(sut, 'Janet', 'Still not a Girl')
        self.assertSequenceEqual([alternative_name], sut.alternative_names)

    def test_start(self) -> None:
        start = Event(None, Birth())
        sut = Person('P1')
        Presence(sut, Subject(), start)
        self.assertEqual(start, sut.start)

    def test_end(self) -> None:
        end = Event(None, Burial())
        sut = Person('P1')
        Presence(sut, Subject(), end)
        self.assertEqual(end, sut.end)

    def test_siblings_without_parents(self) -> None:
        sut = Person('person')
        self.assertCountEqual([], sut.siblings)

    def test_siblings_with_one_common_parent(self) -> None:
        sut = Person('1')
        sibling = Person('2')
        parent = Person('3')
        parent.children = [sut, sibling]
        self.assertCountEqual([sibling], sut.siblings)

    def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person('1')
        sibling = Person('2')
        parent = Person('3')
        parent.children = [sut, sibling]
        self.assertCountEqual([sibling], sut.siblings)

    def test_associated_files(self) -> None:
        file1 = Mock(File)
        file2 = Mock(File)
        file3 = Mock(File)
        file4 = Mock(File)
        file5 = Mock(File)
        file6 = Mock(File)
        sut = Person('1')
        sut.files = [file1, file2, file1]
        citation = Mock(Citation)
        citation.associated_files = [file3, file4, file2]
        name = PersonName(sut)
        name.citations = [citation]
        event = Mock(Event)
        event.associated_files = [file5, file6, file4]
        Presence(sut, Subject(), event)
        self.assertEqual([file1, file2, file3, file4, file5, file6], list(sut.associated_files))
