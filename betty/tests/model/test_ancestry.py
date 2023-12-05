from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import dill
import pytest
from geopy import Point

from betty.locale import Date
from betty.media_type import MediaType
from betty.model import Entity, one_to_one
from betty.model.ancestry import Person, Event, Place, File, Note, Presence, PlaceName, PersonName, Subject, \
    Enclosure, Described, Dated, HasPrivacy, HasMediaType, Link, HasLinks, HasNotes, HasFiles, Source, Citation, \
    HasCitations, PresenceRole, Attendee, Beneficiary, Witness, Ancestry, is_private, is_public, Privacy, \
    merge_privacies
from betty.model.event_type import Burial, Birth, UnknownEventType


class DummyEntity(Entity):
    pass


class TestHasPrivacy:
    async def test_private(self) -> None:
        class _HasPrivacy(HasPrivacy):
            pass
        sut = _HasPrivacy()
        assert sut.privacy is Privacy.UNDETERMINED


class _HasPrivacy(HasPrivacy, Entity):
    def __init__(self, privacy: Privacy):
        super().__init__(None)
        self._privacy = privacy


class TestIsPrivate:
    @pytest.mark.parametrize('expected, target', [
        (True, _HasPrivacy(Privacy.PRIVATE)),
        (False, _HasPrivacy(Privacy.PUBLIC)),
        (False, _HasPrivacy(Privacy.UNDETERMINED)),
        (False, object()),
    ])
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_private(target)


class TestIsPublic:
    @pytest.mark.parametrize('expected, target', [
        (False, _HasPrivacy(Privacy.PRIVATE)),
        (True, _HasPrivacy(Privacy.PUBLIC)),
        (True, _HasPrivacy(Privacy.UNDETERMINED)),
        (True, object()),
    ])
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_public(target)


class TestMergePrivacies:
    @pytest.mark.parametrize('expected, privacies', [
        (Privacy.PUBLIC, (Privacy.PUBLIC,)),
        (Privacy.UNDETERMINED, (Privacy.UNDETERMINED,)),
        (Privacy.PRIVATE, (Privacy.PRIVATE,)),
        (Privacy.UNDETERMINED, (Privacy.PUBLIC, Privacy.UNDETERMINED)),
        (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.PRIVATE)),
        (Privacy.PRIVATE, (Privacy.UNDETERMINED, Privacy.PRIVATE)),
        (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.UNDETERMINED, Privacy.PRIVATE)),
    ])
    async def test(self, expected: Privacy, privacies: tuple[Privacy]) -> None:
        assert expected == merge_privacies(*privacies)


class TestDated:
    async def test_date(self) -> None:
        class _Dated(Dated):
            pass
        sut = _Dated()
        assert sut.date is None


class TestNote:
    async def test_id(self) -> None:
        note_id = 'N1'
        sut = Note(
            id=note_id,
            text='Betty wrote this.',
        )
        assert note_id == sut.id

    async def test_text(self) -> None:
        text = 'Betty wrote this.'
        sut = Note(
            id='N1',
            text=text,
        )
        assert text == sut.text


class HasNotesTestEntity(HasNotes, Entity):
    pass


class TestHasNotes:
    async def test_notes(self) -> None:
        sut = HasNotesTestEntity()
        assert [] == list(sut.notes)


class TestDescribed:
    async def test_description(self) -> None:
        class _Described(Described):
            pass
        sut = _Described()
        assert sut.description is None


class TestHasMediaType:
    async def test_media_type(self) -> None:
        class _HasMediaType(HasMediaType):
            pass
        sut = _HasMediaType()
        assert sut.media_type is None


class TestLink:
    async def test_url(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert url == sut.url

    async def test_media_type(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.media_type is None

    async def test_locale(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.locale is None

    async def test_description(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.description is None

    async def test_relationship(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.relationship is None

    async def test_label(self) -> None:
        url = 'https://example.com'
        sut = Link(url)
        assert sut.label is None


class TestHasLinks:
    async def test_links(self) -> None:
        class _HasLinks(HasLinks):
            pass
        sut = _HasLinks()
        assert set() == sut.links


class _HasFiles(HasFiles, Entity):
    pass


class TestFile:
    async def test_id(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert file_id == sut.id

    async def test_private(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_media_type(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.media_type is None
        media_type = MediaType('text/plain')
        sut.media_type = media_type
        assert media_type == sut.media_type

    async def test_path_with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            file_path = Path(f.name)
            sut = File(
                id=file_id,
                path=file_path,
            )
            assert file_path == sut.path

    async def test_path_with_str(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(
                id=file_id,
                path=Path(f.name),
            )
            assert Path(f.name) == sut.path

    async def test_description(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.description is None
        description = 'Hi, my name is Betty!'
        sut.description = description
        assert description == sut.description

    async def test_notes(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert [] == list(sut.notes)
        notes = [Note(text=''), Note(text='')]
        sut.notes = notes  # type: ignore[assignment]
        assert notes == list(sut.notes)

    async def test_entities(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert [] == list(sut.entities)

        entities = [_HasFiles(), _HasFiles()]
        sut.entities = entities  # type: ignore[assignment]
        assert entities == list(sut.entities)

    async def test_citations(self) -> None:
        file_id = 'BETTY01'
        file_path = Path('~')
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert [] == list(sut.citations)


class TestHasFiles:
    async def test_files(self) -> None:
        sut = _HasFiles()
        assert [] == list(sut.files)
        files = [File(path=Path()), File(path=Path())]
        sut.files = files  # type: ignore[assignment]
        assert files == list(sut.files)


class TestSource:
    async def test_id(self) -> None:
        source_id = 'S1'
        sut = Source(id=source_id)
        assert source_id == sut.id

    async def test_name(self) -> None:
        name = 'The Source'
        sut = Source(name=name)
        assert name == sut.name

    async def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert contained_by_source == sut.contained_by

    async def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        assert [] == list(sut.contains)
        sut.contains = [contains_source]  # type: ignore[assignment]
        assert [contains_source] == list(sut.contains)

    async def test_citations(self) -> None:
        sut = Source()
        assert [] == list(sut.citations)

    async def test_author(self) -> None:
        sut = Source()
        assert sut.author is None
        author = 'Me'
        sut.author = author
        assert author == sut.author

    async def test_publisher(self) -> None:
        sut = Source()
        assert sut.publisher is None
        publisher = 'Me'
        sut.publisher = publisher
        assert publisher == sut.publisher

    async def test_date(self) -> None:
        sut = Source()
        assert sut.date is None

    async def test_files(self) -> None:
        sut = Source()
        assert [] == list(sut.files)

    async def test_links(self) -> None:
        sut = Source()
        assert [] == list(sut.links)

    async def test_private(self) -> None:
        sut = Source()
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True


class _HasCitations(HasCitations, Entity):
    pass


class TestCitation:
    async def test_id(self) -> None:
        citation_id = 'C1'
        sut = Citation(
            id=citation_id,
            source=Source(),
        )
        assert citation_id == sut.id

    async def test_facts(self) -> None:
        fact = _HasCitations()
        sut = Citation(source=Source())
        assert [] == list(sut.facts)
        sut.facts = [fact]  # type: ignore[assignment]
        assert [fact] == list(sut.facts)

    async def test_source(self) -> None:
        source = Source()
        sut = Citation(source=source)
        assert source == sut.source

    async def test_location(self) -> None:
        sut = Citation(source=Source())
        assert sut.location is None
        location = 'Somewhere'
        sut.location = location
        assert location == sut.location

    async def test_date(self) -> None:
        sut = Citation(source=Source())
        assert sut.date is None

    async def test_files(self) -> None:
        sut = Citation(source=Source())
        assert [] == list(sut.files)

    async def test_private(self) -> None:
        sut = Citation(source=Source())
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True


class TestHasCitations:
    async def test_citations(self) -> None:
        sut = _HasCitations()
        assert [] == list(sut.citations)
        citation = Citation(source=Source())
        sut.citations = [citation]  # type: ignore[assignment]
        assert [citation] == list(sut.citations)


class TestPlaceName:
    @pytest.mark.parametrize('expected, a, b', [
        (True, PlaceName(name='Ikke'), PlaceName(name='Ikke')),
        (True, PlaceName(
            name='Ikke',
            locale='nl-NL'
        ), PlaceName(
            name='Ikke',
            locale='nl-NL',
        )),
        (False, PlaceName(
            name='Ikke',
            locale='nl-NL',
        ), PlaceName(
            name='Ikke',
            locale='nl-BE',
        )),
        (False, PlaceName(
            name='Ikke',
            locale='nl-NL'), PlaceName(
            name='Ik',
            locale='nl-NL',
        )),
        (False, PlaceName(name='Ikke'), PlaceName(name='Ik')),
        (False, PlaceName(name='Ikke'), None),
        (False, PlaceName(name='Ikke'), 'not-a-place-name'),
    ])
    async def test_eq(self, expected: bool, a: PlaceName, b: Any) -> None:
        assert expected == (a == b)

    async def test_str(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name=name)
        assert name == str(sut)

    async def test_name(self) -> None:
        name = 'Ikke'
        sut = PlaceName(name=name)
        assert name == sut.name

    async def test_locale(self) -> None:
        locale = 'nl-NL'
        sut = PlaceName(
            name='Ikke',
            locale=locale,
        )
        assert locale == sut.locale

    async def test_date(self) -> None:
        date = Date()
        sut = PlaceName(
            name='Ikke',
            date=date,
        )
        assert date == sut.date


class TestEnclosure:
    async def test_encloses(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert encloses == sut.encloses

    async def test_enclosed_by(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert enclosed_by == sut.enclosed_by

    async def test_date(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert date == sut.date

    async def test_citations(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]  # type: ignore[assignment]
        assert [citation] == list(sut.citations)


class TestPlace:
    async def test_events(self) -> None:
        sut = Place(
            id='P1',
            names=[PlaceName(name='The Place')],
        )
        event = Event(
            id='1',
            event_type=Birth,
        )
        sut.events.add(event)
        assert event in sut.events
        assert sut == event.place
        sut.events.remove(event)
        assert [] == list(sut.events)
        assert event.place is None

    async def test_enclosed_by(self) -> None:
        sut = Place(
            id='P1',
            names=[PlaceName(name='The Place')],
        )
        assert [] == list(sut.enclosed_by)
        enclosing_place = Place(
            id='P2',
            names=[PlaceName(name='The Other Place')],
        )
        enclosure = Enclosure(encloses=sut, enclosed_by=enclosing_place)
        assert enclosure in sut.enclosed_by
        assert sut == enclosure.encloses
        sut.enclosed_by.remove(enclosure)
        assert [] == list(sut.enclosed_by)
        assert enclosure.encloses is None

    async def test_encloses(self) -> None:
        sut = Place(
            id='P1',
            names=[PlaceName(name='The Place')],
        )
        assert [] == list(sut.encloses)
        enclosed_place = Place(
            id='P2',
            names=[PlaceName(name='The Other Place')],
        )
        enclosure = Enclosure(encloses=enclosed_place, enclosed_by=sut)
        assert enclosure in sut.encloses
        assert sut == enclosure.enclosed_by
        sut.encloses.remove(enclosure)
        assert [] == list(sut.encloses)
        assert enclosure.enclosed_by is None

    async def test_id(self) -> None:
        place_id = 'C1'
        sut = Place(
            id=place_id,
            names=[PlaceName(name='one')],
        )
        assert place_id == sut.id

    async def test_links(self) -> None:
        sut = Place(
            id='P1',
            names=[PlaceName(name='The Place')],
        )
        assert [] == list(sut.links)

    async def test_names(self) -> None:
        name = PlaceName(name='The Place')
        sut = Place(
            id='P1',
            names=[name],
        )
        assert [name] == list(sut.names)

    async def test_coordinates(self) -> None:
        name = PlaceName(name='The Place')
        sut = Place(
            id='P1',
            names=[name],
        )
        coordinates = Point()
        sut.coordinates = coordinates
        assert coordinates == sut.coordinates


class TestSubject:
    async def test_name(self) -> None:
        assert isinstance(Subject.name(), str)
        assert '' != Subject.name()

    async def test_label(self) -> None:
        sut = Subject()
        assert isinstance(sut.label, str)
        assert '' != sut.label


class TestWitness:
    async def test_name(self) -> None:
        assert isinstance(Witness.name(), str)
        assert '' != Witness.name()

    async def test_label(self) -> None:
        sut = Witness()
        assert isinstance(sut.label, str)
        assert '' != sut.label


class TestBeneficiary:
    async def test_name(self) -> None:
        assert isinstance(Beneficiary.name(), str)
        assert '' != Beneficiary.name()

    async def test_label(self) -> None:
        sut = Beneficiary()
        assert isinstance(sut.label, str)
        assert '' != sut.label


class TestAttendee:
    async def test_name(self) -> None:
        assert isinstance(Attendee.name(), str)
        assert '' != Attendee.name()

    async def test_label(self) -> None:
        sut = Attendee()
        assert isinstance(sut.label, str)
        assert '' != sut.label


class TestPresence:
    async def test_person(self) -> None:
        person = Person()
        sut = Presence(person, PresenceRole(), Event(event_type=UnknownEventType))
        assert person == sut.person

    async def test_event(self) -> None:
        role = PresenceRole()
        sut = Presence(Person(), role, Event(event_type=UnknownEventType))
        assert role == sut.role

    async def test_role(self) -> None:
        event = Event(event_type=UnknownEventType)
        sut = Presence(Person(), PresenceRole(), event)
        assert event == sut.event


class TestEvent:
    async def test_id(self) -> None:
        event_id = 'E1'
        sut = Event(
            id=event_id,
            event_type=UnknownEventType,
        )
        assert event_id == sut.id

    async def test_place(self) -> None:
        place = Place(
            id='1',
            names=[PlaceName(name='one')],
        )
        sut = Event(event_type=UnknownEventType)
        sut.place = place
        assert place == sut.place
        assert sut in place.events
        sut.place = None
        assert sut.place is None
        assert sut not in place.events

    async def test_presences(self) -> None:
        person = Person(id='P1')
        sut = Event(event_type=UnknownEventType)
        presence = Presence(person, Subject(), sut)
        sut.presences.add(presence)
        assert [presence] == list(sut.presences)
        assert sut == presence.event
        sut.presences.remove(presence)
        assert [] == list(sut.presences)
        assert presence.event is None

    async def test_date(self) -> None:
        sut = Event(event_type=UnknownEventType)
        assert sut.date is None
        date = Date()
        sut.date = date
        assert date == sut.date

    async def test_files(self) -> None:
        sut = Event(event_type=UnknownEventType)
        assert [] == list(sut.files)

    async def test_citations(self) -> None:
        sut = Event(event_type=UnknownEventType)
        assert [] == list(sut.citations)

    async def test_description(self) -> None:
        sut = Event(event_type=UnknownEventType)
        assert sut.description is None

    async def test_private(self) -> None:
        sut = Event(event_type=UnknownEventType)
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_event_type(self) -> None:
        event_type = UnknownEventType
        sut = Event(event_type=event_type)
        assert event_type == sut.event_type

    async def test_associated_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        sut = Event(event_type=UnknownEventType)
        sut.files = [file1, file2, file1]  # type: ignore[assignment]
        citation = Citation(source=Source())
        citation.files = [file3, file4, file2]  # type: ignore[assignment]
        sut.citations = [citation]  # type: ignore[assignment]
        assert [file1 == file2, file3, file4], list(sut.associated_files)


class TestPersonName:
    async def test_person(self) -> None:
        person = Person(id='1')
        sut = PersonName(
            person=person,
            individual='Janet',
            affiliation='Not a Girl',
        )
        assert person == sut.person
        assert [sut] == list(person.names)

    async def test_locale(self) -> None:
        person = Person(id='1')
        sut = PersonName(
            person=person,
            individual='Janet',
            affiliation='Not a Girl',
        )
        assert sut.locale is None

    async def test_citations(self) -> None:
        person = Person(id='1')
        sut = PersonName(
            person=person,
            individual='Janet',
            affiliation='Not a Girl',
        )
        assert [] == list(sut.citations)

    async def test_individual(self) -> None:
        person = Person(id='1')
        individual = 'Janet'
        sut = PersonName(
            person=person,
            individual=individual,
            affiliation='Not a Girl',
        )
        assert individual == sut.individual

    async def test_affiliation(self) -> None:
        person = Person(id='1')
        affiliation = 'Not a Girl'
        sut = PersonName(
            person=person,
            individual='Janet',
            affiliation=affiliation,
        )
        assert affiliation == sut.affiliation


class TestPerson:
    async def test_parents(self) -> None:
        sut = Person(id='1')
        parent = Person(id='2')
        sut.parents.add(parent)
        assert [parent] == list(sut.parents)
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert [] == list(sut.parents)
        assert [] == list(parent.children)

    async def test_children(self) -> None:
        sut = Person(id='1')
        child = Person(id='2')
        sut.children.add(child)
        assert [child] == list(sut.children)
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert [] == list(sut.children)
        assert [] == list(child.parents)

    async def test_presences(self) -> None:
        event = Event(event_type=Birth)
        sut = Person(id='1')
        presence = Presence(sut, Subject(), event)
        sut.presences.add(presence)
        assert [presence] == list(sut.presences)
        assert sut == presence.person
        sut.presences.remove(presence)
        assert [] == list(sut.presences)
        assert presence.person is None

    async def test_names(self) -> None:
        sut = Person(id='1')
        name = PersonName(
            person=sut,
            individual='Janet',
            affiliation='Not a Girl',
        )
        assert [name] == list(sut.names)
        assert sut == name.person
        sut.names.remove(name)
        assert [] == list(sut.names)
        assert name.person is None

    async def test_id(self) -> None:
        person_id = 'P1'
        sut = Person(id=person_id)
        assert person_id == sut.id

    async def test_files(self) -> None:
        sut = Person(id='1')
        assert [] == list(sut.files)

    async def test_citations(self) -> None:
        sut = Person(id='1')
        assert [] == list(sut.citations)

    async def test_links(self) -> None:
        sut = Person(id='1')
        assert [] == list(sut.links)

    async def test_private(self) -> None:
        sut = Person(id='1')
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_name_with_names(self) -> None:
        sut = Person(id='P1')
        name = PersonName(
            person=sut,
            individual='Janet',
        )
        assert name == sut.name

    async def test_name_without_names(self) -> None:
        assert Person(id='P1').name is None

    async def test_alternative_names(self) -> None:
        sut = Person(id='P1')
        PersonName(
            person=sut,
            individual='Janet',
            affiliation='Not a Girl',
        )
        alternative_name = PersonName(
            person=sut,
            individual='Janet',
            affiliation='Still not a Girl',
        )
        assert [alternative_name] == list(sut.alternative_names)

    async def test_start(self) -> None:
        sut = Person(id='P1')
        start = Presence(sut, Subject(), Event(event_type=Birth))
        assert start == sut.start

    async def test_end(self) -> None:
        sut = Person(id='P1')
        end = Presence(sut, Subject(), Event(event_type=Burial))
        assert end == sut.end

    async def test_siblings_without_parents(self) -> None:
        sut = Person(id='person')
        assert [] == list(sut.siblings)

    async def test_siblings_with_one_common_parent(self) -> None:
        sut = Person(id='1')
        sibling = Person(id='2')
        parent = Person(id='3')
        parent.children = [sut, sibling]  # type: ignore[assignment]
        assert [sibling] == list(sut.siblings)

    async def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person(id='1')
        sibling = Person(id='2')
        parent = Person(id='3')
        parent.children = [sut, sibling]  # type: ignore[assignment]
        assert [sibling] == list(sut.siblings)

    async def test_associated_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        file5 = File(path=Path())
        file6 = File(path=Path())
        sut = Person(id='1')
        sut.files = [file1, file2, file1]  # type: ignore[assignment]
        citation = Citation(source=Source())
        citation.files = [file3, file4, file2]  # type: ignore[assignment]
        name = PersonName(
            person=sut,
            individual='Janet',
        )
        name.citations = [citation]  # type: ignore[assignment]
        event = Event(event_type=UnknownEventType)
        event.files = [file5, file6, file4]  # type: ignore[assignment]
        Presence(sut, Subject(), event)
        assert [file1, file2, file3, file4, file5, file6], list(sut.associated_files)


@one_to_one('one_right', 'betty.tests.model.test_ancestry._TestAncestry_OneToOne_Right', 'one_left')
class _TestAncestry_OneToOne_Left(Entity):
    one_right: '_TestAncestry_OneToOne_Right | None'


@one_to_one('one_left', 'betty.tests.model.test_ancestry._TestAncestry_OneToOne_Left', 'one_right')
class _TestAncestry_OneToOne_Right(Entity):
    one_left: '_TestAncestry_OneToOne_Left | None'


class TestAncestry:
    async def test_pickle(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add(left)
        unpickled_sut = dill.loads(dill.dumps(sut))
        assert 2 == len(unpickled_sut)
        assert left.id == unpickled_sut[_TestAncestry_OneToOne_Left][0].id
        assert right.id == unpickled_sut[_TestAncestry_OneToOne_Right][0].id

    async def test_add_(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add(left)
        assert left in sut
        assert right in sut

    async def test_add_unchecked_graph(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add_unchecked_graph(left)
        assert left in sut
        assert right not in sut
