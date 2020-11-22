from gettext import NullTranslations
from tempfile import TemporaryFile, NamedTemporaryFile
from typing import Any
from unittest.mock import Mock

from geopy import Point
from parameterized import parameterized

from betty.ancestry import EventHandlingSetList, Person, Event, Place, File, Note, Presence, PlaceName, PersonName, \
    IdentifiableEvent, Subject, Birth, Enclosure, Identifiable, Described, Dated, HasPrivacy, HasMediaType, Link, \
    HasLinks, HasNotes, HasFiles, Source, Citation, HasCitations, IdentifiableCitation, IdentifiableSource, \
    PresenceRole, Attendee, Beneficiary, Witness, EventType, UnknownEventType, LifeEventType, PreBirthEventType, \
    PostDeathEventType, Baptism, Adoption, Death, Funeral, FinalDispositionEventType, Cremation, Burial, Will, \
    Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, \
    Correspondence, Occupation, Retirement, Confirmation, Missing, EVENT_TYPE_TYPES, RESOURCE_TYPES, Resource
from betty.locale import Date, Translations
from betty.media_type import MediaType
from betty.tests import TestCase


class EventHandlingSetListTest(TestCase):
    def test_prepend(self) -> None:
        added = []
        removal_handler = Mock()
        sut = EventHandlingSetList(lambda value: added.append(value), removal_handler)
        sut.prepend(3)
        sut.prepend(2)
        sut.prepend(1)
        # Prepend an already prepended value again, and assert that it was ignored.
        sut.prepend(1)
        self.assertSequenceEqual([1, 2, 3], sut)
        self.assertSequenceEqual([3, 2, 1], added)
        removal_handler.assert_not_called()

    def test_append(self) -> None:
        added = []
        removal_handler = Mock()
        sut = EventHandlingSetList(lambda value: added.append(value), removal_handler)
        sut.append(3)
        sut.append(2)
        sut.append(1)
        # Append an already appended value again, and assert that it was ignored.
        sut.append(1)
        self.assertSequenceEqual([3, 2, 1], sut)
        self.assertSequenceEqual([3, 2, 1], added)
        removal_handler.assert_not_called()

    def test_remove(self) -> None:
        added = []
        removed = []
        sut = EventHandlingSetList(lambda value: added.append(value), lambda value: removed.append(value))
        sut.append(1, 2, 3, 4)
        sut.remove(4, 2)
        self.assertSequenceEqual([1, 3], sut)
        self.assertSequenceEqual([1, 2, 3, 4], added)
        self.assertSequenceEqual([4, 2], removed)

    def test_replace(self) -> None:
        added = []
        removed = []
        sut = EventHandlingSetList(lambda value: added.append(value), lambda value: removed.append(value))
        sut.append(1, 2, 3)
        sut.replace(4, 5, 6)
        self.assertSequenceEqual([4, 5, 6], sut)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], added)
        self.assertSequenceEqual([1, 2, 3], removed)

    def test_clear(self) -> None:
        added = []
        removed = []
        sut = EventHandlingSetList(lambda value: added.append(value), lambda value: removed.append(value))
        sut.append(1, 2, 3)
        sut.clear()
        self.assertSequenceEqual([], sut)
        self.assertSequenceEqual([1, 2, 3], added)
        self.assertSequenceEqual([1, 2, 3], removed)

    def test_list(self) -> None:
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        self.assertEqual([1, 2, 3], sut.list)

    def test_len(self) -> None:
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        self.assertEqual(3, len(sut))

    def test_iter(self) -> None:
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        # list() gets all items through __iter__ and stores them in the same order.
        self.assertSequenceEqual([1, 2, 3], list(sut))

    def test_getitem(self) -> None:
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        self.assertEqual(1, sut[0])
        self.assertEqual(2, sut[1])
        self.assertEqual(3, sut[2])
        with self.assertRaises(IndexError):
            sut[3]

    def test_set_like_functionality(self) -> None:
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        # Ensure duplicates are skipped.
        sut.append(1, 2, 3, 1, 2, 3, 1, 2, 3)
        # Ensure skipped duplicates do not affect further new values.
        sut.append(1, 2, 3, 4, 5, 6, 7, 8, 9)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6, 7, 8, 9], sut)


class HasPrivacyTest(TestCase):
    def test_date(self) -> None:
        sut = HasPrivacy()
        self.assertIsNone(sut.private)


class DatedTest(TestCase):
    def test_date(self) -> None:
        sut = Dated()
        self.assertIsNone(sut.date)


class NoteTest(TestCase):
    def test_text(self) -> None:
        text = 'Betty wrote this.'
        sut = Note(text)
        self.assertEquals(text, sut.text)


class HasNotesTest(TestCase):
    def test_notes(self) -> None:
        sut = HasNotes()
        self.assertEquals([], sut.notes)


class IdentifiableTest(TestCase):
    def test_id(self) -> None:
        identifiable_id = '000000001'
        sut = Identifiable(identifiable_id)
        self.assertEquals(identifiable_id, sut.id)


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
        self.assertEquals(url, sut.url)

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
        self.assertEquals(set(), sut.links)


class FileTest(TestCase):
    def test_resource_type_name(self) -> None:
        self.assertIsInstance(File.resource_type_name(), str)
        self.assertNotEqual('', File.resource_type_name())

    def test_id(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertEquals(file_id, sut.id)

    def test_private(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertIsNone(sut.private)
        private = True
        sut.private = private
        self.assertEquals(private, sut.private)

    def test_media_type(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertIsNone(sut.media_type)
        media_type = MediaType('text/plain')
        sut.media_type = media_type
        self.assertEquals(media_type, sut.media_type)

    def test_path(self) -> None:
        with TemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertEquals(f.name, sut.path)

    def test_extension_with_extension(self) -> None:
        extension = 'betty'
        with NamedTemporaryFile(suffix='.%s' % extension) as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertEquals(extension, sut.extension)

    def test_extension_without_extension(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertIsNone(sut.extension)

    def test_description(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertIsNone(sut.description)
        description = 'Hi, my name is Betty!'
        sut.description = description
        self.assertEquals(description, sut.description)

    def test_notes(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.notes)
        notes = [Mock(Note), Mock(Note)]
        sut.notes = notes
        self.assertCountEqual(notes, sut.notes)

    def test_resources(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.resources)
        resources = [Mock(HasFiles), Mock(HasFiles)]
        sut.resources = resources
        self.assertCountEqual(resources, sut.resources)

    def test_sources(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.resources)
        source = Mock(Source)
        citation_source = Mock(Source)
        citation = Citation(citation_source)
        resources = [citation, source, Mock(HasFiles)]
        sut.resources = resources
        self.assertCountEqual([citation_source, source], sut.sources)

    def test_citations(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.resources)
        citation = Mock(Citation)
        resources = [citation, Mock(HasFiles)]
        sut.resources = resources
        self.assertCountEqual([citation], sut.citations)

    def test_name(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty.png'
        sut = File(file_id, file_path)
        self.assertEquals('betty.png', sut.name)

    def test_basename(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty.png'
        sut = File(file_id, file_path)
        self.assertEquals('/tmp/betty', sut.basename)

    def test_extension(self) -> None:
        file_id = 'BETTY01'
        file_path = '/tmp/betty.png'
        sut = File(file_id, file_path)
        self.assertEquals('png', sut.extension)


class HasFilesTest(TestCase):
    def test_files(self) -> None:
        sut = HasFiles()
        self.assertCountEqual([], sut.files)
        files = [Mock(File), Mock(File)]
        sut.files = files
        self.assertCountEqual(files, sut.files)


class SourceTest(TestCase):
    def test_resource_type_name(self) -> None:
        self.assertIsInstance(Source.resource_type_name(), str)
        self.assertNotEqual('', Source.resource_type_name())

    def test_name(self) -> None:
        name = 'The Source'
        sut = Source(name)
        self.assertEquals(name, sut.name)

    def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        self.assertIsNone(sut.contained_by)
        sut.contained_by = contained_by_source
        self.assertEquals(contained_by_source, sut.contained_by)

    def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        self.assertCountEqual([], sut.contains)
        sut.contains = [contains_source]
        self.assertCountEqual([contains_source], sut.contains)

    def test_citations(self) -> None:
        sut = Source()
        self.assertCountEqual([], sut.citations)

    def test_author(self) -> None:
        sut = Source()
        self.assertIsNone(sut.author)
        author = 'Me'
        sut.author = author
        self.assertEquals(author, sut.author)

    def test_publisher(self) -> None:
        sut = Source()
        self.assertIsNone(sut.publisher)
        publisher = 'Me'
        sut.publisher = publisher
        self.assertEquals(publisher, sut.publisher)

    def test_date(self) -> None:
        sut = Source()
        self.assertIsNone(sut.date)

    def test_files(self) -> None:
        sut = Source()
        self.assertCountEqual([], sut.files)

    def test_links(self) -> None:
        sut = Source()
        self.assertCountEqual([], sut.links)

    def test_private(self) -> None:
        sut = Source()
        self.assertIsNone(sut.private)
        private = True
        sut.private = private
        self.assertEquals(private, sut.private)


class IdentifiableSourceTest(TestCase):
    def test_id(self) -> None:
        source_id = 'C1'
        sut = IdentifiableSource(source_id)
        self.assertEquals(source_id, sut.id)


class CitationTest(TestCase):
    def test_resource_type_name(self) -> None:
        self.assertIsInstance(Citation.resource_type_name(), str)
        self.assertNotEqual('', Citation.resource_type_name())

    def test_facts(self) -> None:
        fact = Mock(HasCitations)
        sut = Citation(Mock(Source))
        self.assertCountEqual([], sut.facts)
        sut.facts = [fact]
        self.assertCountEqual([fact], sut.facts)

    def test_source(self) -> None:
        source = Mock(Source)
        sut = Citation(source)
        self.assertEquals(source, sut.source)

    def test_location(self) -> None:
        sut = Citation(Mock(Source))
        self.assertIsNone(sut.location)
        location = 'Somewhere'
        sut.location = location
        self.assertEquals(location, sut.location)

    def test_date(self) -> None:
        sut = Citation(Mock(Source))
        self.assertIsNone(sut.date)

    def test_files(self) -> None:
        sut = Citation(Mock(Source))
        self.assertCountEqual([], sut.files)

    def test_private(self) -> None:
        sut = Citation(Mock(Source))
        self.assertIsNone(sut.private)
        private = True
        sut.private = private
        self.assertEquals(private, sut.private)


class IdentifiableCitationTest(TestCase):
    def test_id(self) -> None:
        citation_id = 'C1'
        sut = IdentifiableCitation(citation_id, Mock(Source))
        self.assertEquals(citation_id, sut.id)


class HasCitationsTest(TestCase):
    def test_citations(self) -> None:
        sut = HasCitations()
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
        self.assertEquals(expected, a == b)

    def test_str(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name)
        self.assertEquals(name, str(sut))

    def test_name(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name)
        self.assertEquals(name, sut.name)

    def test_locale(self) -> None:
        locale = 'nl-NL'
        sut = PlaceName('Ikke', locale=locale)
        self.assertEquals(locale, sut.locale)

    def test_date(self) -> None:
        date = Date()
        sut = PlaceName('Ikke', date=date)
        self.assertEquals(date, sut.date)


class EnclosureTest(TestCase):
    def test_encloses(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        self.assertEquals(encloses, sut.encloses)

    def test_enclosed_by(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        self.assertEquals(enclosed_by, sut.enclosed_by)

    def test_date(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        date = Date()
        self.assertIsNone(sut.date)
        sut.date = date
        self.assertEquals(date, sut.date)

    def test_citations(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        citation = Mock(Citation)
        self.assertIsNone(sut.date)
        sut.citations = [citation]
        self.assertCountEqual([citation], sut.citations)


class PlaceTest(TestCase):
    def test_resource_type_name(self) -> None:
        self.assertIsInstance(Citation.resource_type_name(), str)
        self.assertNotEqual('', Citation.resource_type_name())

    def test_events(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        event = IdentifiableEvent('1', Birth())
        sut.events.append(event)
        self.assertIn(event, sut.events)
        self.assertEquals(sut, event.place)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertEquals(None, event.place)

    def test_enclosed_by(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        self.assertCountEqual([], sut.enclosed_by)
        enclosing_place = Place('P2', [PlaceName('The Other Place')])
        enclosure = Enclosure(sut, enclosing_place)
        self.assertIn(enclosure, sut.enclosed_by)
        self.assertEquals(sut, enclosure.encloses)
        sut.enclosed_by.remove(enclosure)
        self.assertCountEqual([], sut.enclosed_by)
        self.assertIsNone(enclosure.encloses)

    def test_encloses(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        self.assertCountEqual([], sut.encloses)
        enclosed_place = Place('P2', [PlaceName('The Other Place')])
        enclosure = Enclosure(enclosed_place, sut)
        self.assertIn(enclosure, sut.encloses)
        self.assertEquals(sut, enclosure.enclosed_by)
        sut.encloses.remove(enclosure)
        self.assertCountEqual([], sut.encloses)
        self.assertIsNone(enclosure.enclosed_by)

    def test_id(self) -> None:
        place_id = 'C1'
        sut = Place(place_id, [PlaceName('one')])
        self.assertEquals(place_id, sut.id)

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
        self.assertEquals(coordinates, sut.coordinates)


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
        self.assertEquals(person, sut.person)

    def test_event(self) -> None:
        role = Mock(PresenceRole)
        sut = Presence(Mock(Person), role, Mock(Event))
        self.assertEquals(role, sut.role)

    def test_role(self) -> None:
        event = Mock(Event)
        sut = Presence(Mock(Person), Mock(PresenceRole), event)
        self.assertEquals(event, sut.event)


class EventTypeTest(TestCase):
    def test_comes_before(self) -> None:
        self.assertIsInstance(EventType.comes_before(), set)

    def test_comes_after(self) -> None:
        self.assertIsInstance(EventType.comes_after(), set)


class UnknownEventTypeTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(UnknownEventType.name(), str)
        self.assertNotEqual('', UnknownEventType.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = UnknownEventType()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_before(self) -> None:
        self.assertIsInstance(UnknownEventType.comes_before(), set)

    def test_comes_after(self) -> None:
        self.assertIsInstance(UnknownEventType.comes_after(), set)


class PreBirthEventTypeTestCase(TestCase):
    def test_comes_before(self) -> None:
        self.assertIsInstance(PreBirthEventType.comes_before(), set)


class LifeEventTypeTestCase(TestCase):
    def test_comes_before(self) -> None:
        self.assertIsInstance(LifeEventType.comes_before(), set)

    def test_comes_after(self) -> None:
        self.assertIsInstance(LifeEventType.comes_after(), set)


class PostDeathEventTypeTestCase(TestCase):
    def test_comes_after(self) -> None:
        self.assertIsInstance(PostDeathEventType.comes_after(), set)


class BirthTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Birth.name(), str)
        self.assertNotEqual('', Birth.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Birth()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_before(self) -> None:
        self.assertIsInstance(Birth.comes_before(), set)


class BaptismTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Baptism.name(), str)
        self.assertNotEqual('', Baptism.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Baptism()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class AdoptionTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Adoption.name(), str)
        self.assertNotEqual('', Adoption.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Adoption()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class DeathTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Death.name(), str)
        self.assertNotEqual('', Death.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Death()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_after(self) -> None:
        self.assertIsInstance(Death.comes_after(), set)


class FuneralTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Funeral.name(), str)
        self.assertNotEqual('', Funeral.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Funeral()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_after(self) -> None:
        self.assertIsInstance(Funeral.comes_after(), set)


class FinalDispositionEventTypeTestCase(TestCase):
    def test_comes_after(self) -> None:
        self.assertIsInstance(FinalDispositionEventType.comes_after(), set)


class CremationTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Cremation.name(), str)
        self.assertNotEqual('', Cremation.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Cremation()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class BurialTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Burial.name(), str)
        self.assertNotEqual('', Burial.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Burial()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class WillTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Will.name(), str)
        self.assertNotEqual('', Will.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Will()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_after(self) -> None:
        self.assertIsInstance(Will.comes_after(), set)


class EngagementTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Engagement.name(), str)
        self.assertNotEqual('', Engagement.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Engagement()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_before(self) -> None:
        self.assertIsInstance(Engagement.comes_before(), set)


class MarriageTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Marriage.name(), str)
        self.assertNotEqual('', Marriage.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Marriage()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class MarriageAnnouncementTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(MarriageAnnouncement.name(), str)
        self.assertNotEqual('', MarriageAnnouncement.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = MarriageAnnouncement()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_before(self) -> None:
        self.assertIsInstance(MarriageAnnouncement.comes_before(), set)


class DivorceTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Divorce.name(), str)
        self.assertNotEqual('', Divorce.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Divorce()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_after(self) -> None:
        self.assertIsInstance(Divorce.comes_after(), set)


class DivorceAnnouncementTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(DivorceAnnouncement.name(), str)
        self.assertNotEqual('', DivorceAnnouncement.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = DivorceAnnouncement()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)

    def test_comes_before(self) -> None:
        self.assertIsInstance(DivorceAnnouncement.comes_before(), set)

    def test_comes_after(self) -> None:
        self.assertIsInstance(DivorceAnnouncement.comes_after(), set)


class ResidenceTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Residence.name(), str)
        self.assertNotEqual('', Residence.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Residence()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class ImmigrationTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Immigration.name(), str)
        self.assertNotEqual('', Immigration.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Immigration()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class EmigrationTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Emigration.name(), str)
        self.assertNotEqual('', Emigration.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Emigration()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class OccupationTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Occupation.name(), str)
        self.assertNotEqual('', Occupation.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Occupation()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class RetirementTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Retirement.name(), str)
        self.assertNotEqual('', Retirement.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Retirement()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class CorrespondenceTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Correspondence.name(), str)
        self.assertNotEqual('', Correspondence.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Correspondence()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class ConfirmationTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Confirmation.name(), str)
        self.assertNotEqual('', Confirmation.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Confirmation()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class MissingTestCase(TestCase):
    def test_name(self) -> None:
        self.assertIsInstance(Missing.name(), str)
        self.assertNotEqual('', Missing.name())

    def test_label(self) -> None:
        with Translations(NullTranslations()):
            sut = Missing()
            self.assertIsInstance(sut.label, str)
            self.assertNotEqual('', sut.label)


class EventTypeTypesTest(TestCase):
    def test(self) -> None:
        for event_type_type in EVENT_TYPE_TYPES:
            self.assertTrue(issubclass(event_type_type, EventType))


class EventTest(TestCase):
    def test_resource_type_name(self) -> None:
        self.assertIsInstance(Event.resource_type_name(), str)
        self.assertNotEqual('', Event.resource_type_name())

    def test_place(self) -> None:
        place = Place('1', [PlaceName('one')])
        sut = Event(Mock(EventType))
        sut.place = place
        self.assertEquals(place, sut.place)
        self.assertIn(sut, place.events)
        sut.place = None
        self.assertEquals(None, sut.place)
        self.assertNotIn(sut, place.events)

    def test_presences(self) -> None:
        person = Person('P1')
        sut = Event(Mock(EventType))
        presence = Presence(person, Subject(), sut)
        sut.presences.append(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEquals(sut, presence.event)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.event)

    def test_date(self) -> None:
        sut = Event(Mock(EventType))
        self.assertIsNone(sut.date)
        date = Mock(Date)
        sut.date = date
        self.assertEquals(date, sut.date)

    def test_files(self) -> None:
        sut = Event(Mock(EventType))
        self.assertCountEqual([], sut.files)

    def test_citations(self) -> None:
        sut = Event(Mock(EventType))
        self.assertCountEqual([], sut.citations)

    def test_description(self) -> None:
        sut = Event(Mock(EventType))
        self.assertIsNone(sut.description)

    def test_private(self) -> None:
        sut = Event(Mock(EventType))
        self.assertIsNone(sut.private)

    def test_type(self) -> None:
        event_type = Mock(EventType)
        sut = Event(event_type)
        self.assertEquals(event_type, sut.type)

    def test_associated_files(self) -> None:
        file1 = Mock(File)
        file2 = Mock(File)
        file3 = Mock(File)
        file4 = Mock(File)
        sut = Event(Mock(EventType))
        sut.files = [file1, file2, file1]
        citation = Mock(Citation)
        citation.associated_files = [file3, file4, file2]
        sut.citations = [citation]
        self.assertEquals([file1, file2, file3, file4], list(sut.associated_files))


class IdentifiableEventTest(TestCase):
    def test_id(self) -> None:
        event_id = 'E1'
        sut = IdentifiableEvent(event_id, Mock(EventType))
        self.assertEquals(event_id, sut.id)


class PersonNameTest(TestCase):
    def test_person(self) -> None:
        sut = PersonName('Janet', 'Not a Girl')
        person = Person('1')
        sut.person = person
        self.assertEquals(person, sut.person)
        self.assertCountEqual([sut], person.names)
        sut.person = None
        self.assertIsNone(sut.person)
        self.assertCountEqual([], person.names)

    def test_locale(self) -> None:
        sut = PersonName('Janet', 'Not a Girl')
        self.assertIsNone(sut.locale)

    def test_citations(self) -> None:
        sut = PersonName('Janet', 'Not a Girl')
        self.assertCountEqual([], sut.citations)

    def test_individual(self) -> None:
        individual = 'Janet'
        sut = PersonName(individual, 'Not a Girl')
        self.assertEquals(individual, sut.individual)

    def test_affiliation(self) -> None:
        affiliation = 'Not a Girl'
        sut = PersonName('Janet', affiliation)
        self.assertEquals(affiliation, sut.affiliation)

    @parameterized.expand([
        (True, PersonName('Janet', 'Not a Girl'), PersonName('Janet', 'Not a Girl')),
        (True, PersonName('Janet'), PersonName('Janet')),
        (True, PersonName(None, 'Not a Girl'), PersonName(None, 'Not a Girl')),
        (False, PersonName('Janet'), PersonName(None, 'Not a Girl')),
        (False, PersonName('Janet', 'Not a Girl'), None),
        (False, PersonName('Janet', 'Not a Girl'), True),
        (False, PersonName('Janet', 'Not a Girl'), 9),
        (False, PersonName('Janet', 'Not a Girl'), object()),
    ])
    def test_eq(self, expected: bool, left: PersonName, right: Any) -> None:
        self.assertEquals(expected, left == right)

    @parameterized.expand([
        (False, PersonName('Janet', 'Not a Girl'), PersonName('Janet', 'Not a Girl')),
        (True, PersonName('Janet', 'Not a Girl'), PersonName('Not a Girl', 'Janet')),
        (True, PersonName('Janet', 'Not a Girl'), None),
    ])
    def test_gt(self, expected: bool, left: PersonName, right: Any) -> None:
        self.assertEquals(expected, left > right)


class PersonTest(TestCase):
    def test_resource_type_name(self) -> None:
        self.assertIsInstance(Person.resource_type_name(), str)
        self.assertNotEqual('', Person.resource_type_name())

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
        event = Event(Birth())
        sut = Person('1')
        presence = Presence(sut, Subject(), event)
        sut.presences.append(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEquals(sut, presence.person)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.person)

    def test_names(self) -> None:
        sut = Person('1')
        name = PersonName('Janet', 'Not a Girl')
        sut.names.append(name)
        self.assertCountEqual([name], sut.names)
        self.assertEquals(sut, name.person)
        sut.names.remove(name)
        self.assertCountEqual([], sut.names)
        self.assertIsNone(name.person)

    def test_id(self) -> None:
        person_id = 'P1'
        sut = Person(person_id)
        self.assertEquals(person_id, sut.id)

    def test_files(self) -> None:
        sut = Source()
        self.assertCountEqual([], sut.files)

    def test_citations(self) -> None:
        sut = Source()
        self.assertCountEqual([], sut.citations)

    def test_links(self) -> None:
        sut = Source()
        self.assertCountEqual([], sut.links)

    def test_private(self) -> None:
        sut = Event(Mock(EventType))
        self.assertIsNone(sut.private)

    def test_name_with_names(self) -> None:
        sut = Person('P1')
        name = PersonName()
        sut.names = [name, PersonName()]
        self.assertEquals(name, sut.name)

    def test_name_without_names(self) -> None:
        self.assertIsNone(Person('P1').name)

    def test_alternative_names(self) -> None:
        sut = Person('P1')
        name = PersonName('Janet', 'Not a Girl')
        alternative_name = PersonName('Janet', 'Still not a Girl')
        sut.names = [name, alternative_name]
        self.assertEquals([alternative_name], sut.alternative_names)

    def test_start(self) -> None:
        start = Event(Birth())
        sut = Person('P1')
        Presence(sut, Subject(), start)
        self.assertEquals(start, sut.start)

    def test_end(self) -> None:
        end = Event(Burial())
        sut = Person('P1')
        Presence(sut, Subject(), end)
        self.assertEquals(end, sut.end)

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
        name = PersonName()
        name.citations = [citation]
        sut.names = [name]
        event = Mock(Event)
        event.associated_files = [file5, file6, file4]
        Presence(sut, Subject(), event)
        self.assertEquals([file1, file2, file3, file4, file5, file6], list(sut.associated_files))


class ResourceTypesTest(TestCase):
    def test(self) -> None:
        for resource_type in RESOURCE_TYPES:
            self.assertTrue(issubclass(resource_type, Resource))
