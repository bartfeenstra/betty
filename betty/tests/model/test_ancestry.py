from gettext import NullTranslations
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from unittest.mock import Mock

import pytest
from geopy import Point

from betty.locale import Date, Translation
from betty.media_type import MediaType
from betty.model import Entity
from betty.model.ancestry import Person, Event, Place, File, Note, Presence, PlaceName, PersonName, Subject, \
    Enclosure, Described, Dated, HasPrivacy, HasMediaType, Link, HasLinks, HasNotes, HasFiles, Source, Citation, \
    HasCitations, PresenceRole, Attendee, Beneficiary, Witness, EventType
from betty.model.event_type import Burial, Birth


class TestHasPrivacy:
    def test_date(self) -> None:
        class _HasPrivacy(HasPrivacy):
            pass
        sut = _HasPrivacy()
        assert sut.private is None


class TestDated:
    def test_date(self) -> None:
        class _Dated(Dated):
            pass
        sut = _Dated()
        assert sut.date is None


class TestNote:
    def test_id(self) -> None:
        note_id = 'N1'
        sut = Note(note_id, 'Betty wrote this.')
        assert note_id == sut.id

    def test_text(self) -> None:
        text = 'Betty wrote this.'
        sut = Note('N1', text)
        assert text == sut.text


class HasNotesTestEntity(HasNotes, Entity):
    pass


class TestHasNotes:
    def test_notes(self) -> None:
        sut = HasNotesTestEntity()
        assert [] == list(sut.notes)


class TestDescribed:
    def test_description(self) -> None:
        class _Described(Described):
            pass
        sut = _Described()
        assert sut.description is None


class TestHasMediaType:
    def test_media_type(self) -> None:
        class _HasMediaType(HasMediaType):
            pass
        sut = _HasMediaType()
        assert sut.media_type is None


class TestLink:
    def test_url(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert url == sut.url

    def test_media_type(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.media_type is None

    def test_locale(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.locale is None

    def test_description(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.description is None

    def test_relationship(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.relationship is None

    def test_label(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.label is None


class TestHasLinks:
    def test_links(self) -> None:
        class _HasLinks(HasLinks):
            pass
        sut = _HasLinks()
        assert set() == sut.links


class _HasFiles(HasFiles, Entity):
    pass


class TestFile:
    def test_id(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert file_id == sut.id

    def test_private(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert sut.private is None
        private = True
        sut.private = private
        assert private == sut.private

    def test_media_type(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert sut.media_type is None
        media_type = MediaType('text/plain')
        sut.media_type = media_type
        assert media_type == sut.media_type

    def test_path_with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            file_path = Path(f.name)
            sut = File(file_id, file_path)
            assert file_path == sut.path

    def test_path_with_str(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            assert Path(f.name) == sut.path

    def test_description(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert sut.description is None
        description = 'Hi, my name is Betty!'
        sut.description = description
        assert description == sut.description

    def test_notes(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert [] == list(sut.notes)
        notes = [Mock(Note), Mock(Note)]
        sut.notes = notes  # type: ignore
        assert notes == list(sut.notes)

    def test_entities(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert [] == list(sut.entities)

        entities = [_HasFiles(), _HasFiles()]
        sut.entities = entities  # type: ignore
        assert entities == list(sut.entities)

    def test_citations(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(file_id, file_path)
        assert [] == list(sut.citations)


class TestHasFiles:
    def test_files(self) -> None:
        sut = _HasFiles()
        assert [] == list(sut.files)
        files = [Mock(File), Mock(File)]
        sut.files = files  # type: ignore
        assert files == list(sut.files)


class TestSource:
    def test_id(self) -> None:
        source_id = 'S1'
        sut = Source(source_id)
        assert source_id == sut.id

    def test_name(self) -> None:
        name = 'The Source'
        sut = Source(None, name)
        assert name == sut.name

    def test_contained_by(self) -> None:
        contained_by_source = Source(None)
        sut = Source(None)
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert contained_by_source == sut.contained_by

    def test_contains(self) -> None:
        contains_source = Source(None)
        sut = Source(None)
        assert [] == list(sut.contains)
        sut.contains = [contains_source]  # type: ignore
        assert [contains_source] == list(sut.contains)

    def test_citations(self) -> None:
        sut = Source(None)
        assert [] == list(sut.citations)

    def test_author(self) -> None:
        sut = Source(None)
        assert sut.author is None
        author = 'Me'
        sut.author = author
        assert author == sut.author

    def test_publisher(self) -> None:
        sut = Source(None)
        assert sut.publisher is None
        publisher = 'Me'
        sut.publisher = publisher
        assert publisher == sut.publisher

    def test_date(self) -> None:
        sut = Source(None)
        assert sut.date is None

    def test_files(self) -> None:
        sut = Source(None)
        assert [] == list(sut.files)

    def test_links(self) -> None:
        sut = Source(None)
        assert [] == list(sut.links)

    def test_private(self) -> None:
        sut = Source(None)
        assert sut.private is None
        private = True
        sut.private = private
        assert private == sut.private


class _HasCitations(HasCitations, Entity):
    pass


class TestCitation:
    def test_id(self) -> None:
        citation_id = 'C1'
        sut = Citation(citation_id, Mock(Source))
        assert citation_id == sut.id

    def test_facts(self) -> None:
        fact = _HasCitations()
        sut = Citation(None, Mock(Source))
        assert [] == list(sut.facts)
        sut.facts = [fact]  # type: ignore
        assert [fact] == list(sut.facts)

    def test_source(self) -> None:
        source = Mock(Source)
        sut = Citation(None, source)
        assert source == sut.source

    def test_location(self) -> None:
        sut = Citation(None, Mock(Source))
        assert sut.location is None
        location = 'Somewhere'
        sut.location = location
        assert location == sut.location

    def test_date(self) -> None:
        sut = Citation(None, Mock(Source))
        assert sut.date is None

    def test_files(self) -> None:
        sut = Citation(None, Mock(Source))
        assert [] == list(sut.files)

    def test_private(self) -> None:
        sut = Citation(None, Mock(Source))
        assert sut.private is None
        private = True
        sut.private = private
        assert private == sut.private


class TestHasCitations:
    def test_citations(self) -> None:
        sut = _HasCitations()
        assert [] == list(sut.citations)
        citation = Mock(Citation)
        sut.citations = [citation]  # type: ignore
        assert [citation] == list(sut.citations)


class TestPlaceName:
    @pytest.mark.parametrize('expected, a, b', [
        (True, PlaceName('Ikke'), PlaceName('Ikke')),
        (True, PlaceName('Ikke', 'nl-NL'), PlaceName('Ikke', 'nl-NL')),
        (False, PlaceName('Ikke', 'nl-NL'), PlaceName('Ikke', 'nl-BE')),
        (False, PlaceName('Ikke', 'nl-NL'), PlaceName('Ik', 'nl-NL')),
        (False, PlaceName('Ikke'), PlaceName('Ik')),
        (False, PlaceName('Ikke'), None),
        (False, PlaceName('Ikke'), 'not-a-place-name'),
    ])
    def test_eq(self, expected: bool, a: PlaceName, b: Any) -> None:
        assert expected == (a == b)

    def test_str(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name)
        assert name == str(sut)

    def test_name(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name)
        assert name == sut.name

    def test_locale(self) -> None:
        locale = 'nl-NL'
        sut = PlaceName('Ikke', locale=locale)
        assert locale == sut.locale

    def test_date(self) -> None:
        date = Date()
        sut = PlaceName('Ikke', date=date)
        assert date == sut.date


class TestEnclosure:
    def test_encloses(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        assert encloses == sut.encloses

    def test_enclosed_by(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        assert enclosed_by == sut.enclosed_by

    def test_date(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert date == sut.date

    def test_citations(self) -> None:
        encloses = Mock(Place)
        enclosed_by = Mock(Place)
        sut = Enclosure(encloses, enclosed_by)
        citation = Mock(Citation)
        assert sut.date is None
        sut.citations = [citation]  # type: ignore
        assert [citation] == list(sut.citations)


class TestPlace:
    def test_events(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        event = Event('1', Birth())
        sut.events.append(event)
        assert event in sut.events
        assert sut == event.place
        sut.events.remove(event)
        assert [] == list(sut.events)
        assert event.place is None

    def test_enclosed_by(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        assert [] == list(sut.enclosed_by)
        enclosing_place = Place('P2', [PlaceName('The Other Place')])
        enclosure = Enclosure(sut, enclosing_place)
        assert enclosure in sut.enclosed_by
        assert sut == enclosure.encloses
        sut.enclosed_by.remove(enclosure)
        assert [] == list(sut.enclosed_by)
        assert enclosure.encloses is None

    def test_encloses(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        assert [] == list(sut.encloses)
        enclosed_place = Place('P2', [PlaceName('The Other Place')])
        enclosure = Enclosure(enclosed_place, sut)
        assert enclosure in sut.encloses
        assert sut == enclosure.enclosed_by
        sut.encloses.remove(enclosure)
        assert [] == list(sut.encloses)
        assert enclosure.enclosed_by is None

    def test_id(self) -> None:
        place_id = 'C1'
        sut = Place(place_id, [PlaceName('one')])
        assert place_id == sut.id

    def test_links(self) -> None:
        sut = Place('P1', [PlaceName('The Place')])
        assert [] == list(sut.links)

    def test_names(self) -> None:
        name = PlaceName('The Place')
        sut = Place('P1', [name])
        assert [name] == list(sut.names)

    def test_coordinates(self) -> None:
        name = PlaceName('The Place')
        sut = Place('P1', [name])
        coordinates = Point()
        sut.coordinates = coordinates
        assert coordinates == sut.coordinates


class TestSubject:
    def test_name(self) -> None:
        assert isinstance(Subject.name(), str)
        assert '' != Subject.name

    def test_label(self) -> None:
        sut = Subject()
        with Translation(NullTranslations()):
            assert isinstance(sut.label, str)
            assert '' != sut.label


class TestWitness:
    def test_name(self) -> None:
        assert isinstance(Witness.name(), str)
        assert '' != Witness.name

    def test_label(self) -> None:
        sut = Witness()
        with Translation(NullTranslations()):
            assert isinstance(sut.label, str)
            assert '' != sut.label


class TestBeneficiary:
    def test_name(self) -> None:
        assert isinstance(Beneficiary.name(), str)
        assert '' != Beneficiary.name

    def test_label(self) -> None:
        sut = Beneficiary()
        with Translation(NullTranslations()):
            assert isinstance(sut.label, str)
            assert '' != sut.label


class TestAttendee:
    def test_name(self) -> None:
        assert isinstance(Attendee.name(), str)
        assert '' != Attendee.name

    def test_label(self) -> None:
        sut = Attendee()
        with Translation(NullTranslations()):
            assert isinstance(sut.label, str)
            assert '' != sut.label


class TestPresence:
    def test_person(self) -> None:
        person = Mock(Person)
        sut = Presence(person, Mock(PresenceRole), Mock(Event))
        assert person == sut.person

    def test_event(self) -> None:
        role = Mock(PresenceRole)
        sut = Presence(Mock(Person), role, Mock(Event))
        assert role == sut.role

    def test_role(self) -> None:
        event = Mock(Event)
        sut = Presence(Mock(Person), Mock(PresenceRole), event)
        assert event == sut.event


class TestEvent:
    def test_id(self) -> None:
        event_id = 'E1'
        sut = Event(event_id, Mock(EventType))
        assert event_id == sut.id

    def test_place(self) -> None:
        place = Place('1', [PlaceName('one')])
        sut = Event(None, Mock(EventType))
        sut.place = place
        assert place == sut.place
        assert sut in place.events
        sut.place = None
        assert sut.place is None
        assert sut not in place.events

    def test_presences(self) -> None:
        person = Person('P1')
        sut = Event(None, Mock(EventType))
        presence = Presence(person, Subject(), sut)
        sut.presences.append(presence)
        assert [presence] == list(sut.presences)
        assert sut == presence.event
        sut.presences.remove(presence)
        assert [] == list(sut.presences)
        assert presence.event is None

    def test_date(self) -> None:
        sut = Event(None, Mock(EventType))
        assert sut.date is None
        date = Mock(Date)
        sut.date = date
        assert date == sut.date

    def test_files(self) -> None:
        sut = Event(None, Mock(EventType))
        assert [] == list(sut.files)

    def test_citations(self) -> None:
        sut = Event(None, Mock(EventType))
        assert [] == list(sut.citations)

    def test_description(self) -> None:
        sut = Event(None, Mock(EventType))
        assert sut.description is None

    def test_private(self) -> None:
        sut = Event(None, Mock(EventType))
        assert sut.private is None

    def test_type(self) -> None:
        event_type = Mock(EventType)
        sut = Event(None, event_type)
        assert event_type == sut.type

    def test_associated_files(self) -> None:
        file1 = Mock(File)
        file2 = Mock(File)
        file3 = Mock(File)
        file4 = Mock(File)
        sut = Event(None, Mock(EventType))
        sut.files = [file1, file2, file1]  # type: ignore
        citation = Mock(Citation)
        citation.associated_files = [file3, file4, file2]
        sut.citations = [citation]  # type: ignore
        assert [file1 == file2, file3, file4], list(sut.associated_files)


class TestPersonName:
    def test_person(self) -> None:
        person = Person('1')
        sut = PersonName(person, 'Janet', 'Not a Girl')
        assert person == sut.person
        assert [sut] == list(person.names)

    def test_locale(self) -> None:
        person = Person('1')
        sut = PersonName(person, 'Janet', 'Not a Girl')
        assert sut.locale is None

    def test_citations(self) -> None:
        person = Person('1')
        sut = PersonName(person, 'Janet', 'Not a Girl')
        assert [] == list(sut.citations)

    def test_individual(self) -> None:
        person = Person('1')
        individual = 'Janet'
        sut = PersonName(person, individual, 'Not a Girl')
        assert individual == sut.individual

    def test_affiliation(self) -> None:
        person = Person('1')
        affiliation = 'Not a Girl'
        sut = PersonName(person, 'Janet', affiliation)
        assert affiliation == sut.affiliation

    @pytest.mark.parametrize('expected, left, right', [
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
        assert expected == (left == right)

    @pytest.mark.parametrize('expected, left, right', [
        (False, PersonName(Person('1'), 'Janet', 'Not a Girl'), PersonName(Person('1'), 'Janet', 'Not a Girl')),
        (True, PersonName(Person('1'), 'Janet', 'Not a Girl'), PersonName(Person('1'), 'Not a Girl', 'Janet')),
        (True, PersonName(Person('1'), 'Janet', 'Not a Girl'), None),
    ])
    def test_gt(self, expected: bool, left: PersonName, right: Any) -> None:
        assert expected == (left > right)


class TestPerson:
    def test_parents(self) -> None:
        sut = Person('1')
        parent = Person('2')
        sut.parents.append(parent)
        assert [parent] == list(sut.parents)
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert [] == list(sut.parents)
        assert [] == list(parent.children)

    def test_children(self) -> None:
        sut = Person('1')
        child = Person('2')
        sut.children.append(child)
        assert [child] == list(sut.children)
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert [] == list(sut.children)
        assert [] == list(child.parents)

    def test_presences(self) -> None:
        event = Event(None, Birth())
        sut = Person('1')
        presence = Presence(sut, Subject(), event)
        sut.presences.append(presence)
        assert [presence] == list(sut.presences)
        assert sut == presence.person
        sut.presences.remove(presence)
        assert [] == list(sut.presences)
        assert presence.person is None

    def test_names(self) -> None:
        sut = Person('1')
        name = PersonName(sut, 'Janet', 'Not a Girl')
        assert [name] == list(sut.names)
        assert sut == name.person
        sut.names.remove(name)
        assert [] == list(sut.names)
        assert name.person is None

    def test_id(self) -> None:
        person_id = 'P1'
        sut = Person(person_id)
        assert person_id == sut.id

    def test_files(self) -> None:
        sut = Person('1')
        assert [] == list(sut.files)

    def test_citations(self) -> None:
        sut = Person('1')
        assert [] == list(sut.citations)

    def test_links(self) -> None:
        sut = Person('1')
        assert [] == list(sut.links)

    def test_private(self) -> None:
        sut = Person('1')
        assert sut.private is None

    def test_name_with_names(self) -> None:
        sut = Person('P1')
        name = PersonName(sut, 'Janet')
        assert name == sut.name

    def test_name_without_names(self) -> None:
        assert Person('P1').name is None

    def test_alternative_names(self) -> None:
        sut = Person('P1')
        PersonName(sut, 'Janet', 'Not a Girl')
        alternative_name = PersonName(sut, 'Janet', 'Still not a Girl')
        assert [alternative_name] == list(sut.alternative_names)

    def test_start(self) -> None:
        start = Event(None, Birth())
        sut = Person('P1')
        Presence(sut, Subject(), start)
        assert start == sut.start

    def test_end(self) -> None:
        end = Event(None, Burial())
        sut = Person('P1')
        Presence(sut, Subject(), end)
        assert end == sut.end

    def test_siblings_without_parents(self) -> None:
        sut = Person('person')
        assert [] == list(sut.siblings)

    def test_siblings_with_one_common_parent(self) -> None:
        sut = Person('1')
        sibling = Person('2')
        parent = Person('3')
        parent.children = [sut, sibling]  # type: ignore
        assert [sibling] == list(sut.siblings)

    def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person('1')
        sibling = Person('2')
        parent = Person('3')
        parent.children = [sut, sibling]  # type: ignore
        assert [sibling] == list(sut.siblings)

    def test_associated_files(self) -> None:
        file1 = Mock(File)
        file2 = Mock(File)
        file3 = Mock(File)
        file4 = Mock(File)
        file5 = Mock(File)
        file6 = Mock(File)
        sut = Person('1')
        sut.files = [file1, file2, file1]  # type: ignore
        citation = Mock(Citation)
        citation.associated_files = [file3, file4, file2]
        name = PersonName(sut, 'Janet')
        name.citations = [citation]  # type: ignore
        event = Mock(Event)
        event.associated_files = [file5, file6, file4]
        Presence(sut, Subject(), event)
        assert [file1 == file2, file3, file4, file5, file6], list(sut.associated_files)
