from pathlib import Path
from unittest.mock import ANY, Mock

from pytest_mock import MockerFixture

from betty.anonymizer import anonymize, anonymize_person, anonymize_event, anonymize_file, anonymize_citation, \
    anonymize_source, AnonymousSource, AnonymousCitation
from betty.app import App
from betty.model import Entity
from betty.model.ancestry import Ancestry, Person, File, Source, Citation, PersonName, Presence, Event, Subject, \
    HasCitations
from betty.model.event_type import Birth


class TestAnonymousSource:
    def test_name(self) -> None:
        with App():
            assert isinstance(AnonymousSource().name, str)

    def test_replace(self) -> None:
        with App():
            ancestry = Ancestry()
            citations = [Citation(None, Source(None))]
            contains = [Source(None)]
            files = [Mock(File)]
            sut = AnonymousSource()
            other = Source(None)
            ancestry.add(other)
            other.citations = citations  # type: ignore[assignment]
            other.contains = contains  # type: ignore[assignment]
            other.files = files  # type: ignore[assignment]
            sut.replace(other, ancestry)
            assert citations == list(sut.citations)
            assert contains == list(sut.contains)
            assert files == list(sut.files)
            assert other not in ancestry


class TestAnonymousCitation:
    def test_location(self) -> None:
        source = Mock(Source)
        with App():
            assert isinstance(AnonymousCitation(source).location, str)

    def test_replace(self) -> None:
        class _HasCitations(HasCitations, Entity):
            pass
        ancestry = Ancestry()
        facts = [_HasCitations()]
        files = [File('F1', Path(__file__))]
        source = Mock(Source)
        sut = AnonymousCitation(source)
        other = Citation(None, source)
        ancestry.add(other)
        other.facts = facts  # type: ignore[assignment]
        other.files = files  # type: ignore[assignment]
        sut.replace(other, ancestry)
        assert facts == list(sut.facts)
        assert files == list(sut.files)
        assert other not in ancestry


class TestAnonymize:
    def test_with_public_person_should_not_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_person = mocker.patch('betty.anonymizer.anonymize_person')
        person = Person('P0')
        person.private = False
        ancestry = Ancestry()
        ancestry.add(person)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_person.assert_not_called()

    def test_with_private_person_should_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_person = mocker.patch('betty.anonymizer.anonymize_person')
        person = Person('P0')
        person.private = True
        ancestry = Ancestry()
        ancestry.add(person)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_person.assert_called_once_with(person)

    def test_with_public_event_should_not_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_event = mocker.patch('betty.anonymizer.anonymize_event')
        event = Event('E0', Birth)
        event.private = False
        ancestry = Ancestry()
        ancestry.add(event)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_event.assert_not_called()

    def test_with_private_event_should_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_event = mocker.patch('betty.anonymizer.anonymize_event')
        event = Event('E0', Birth)
        event.private = True
        ancestry = Ancestry()
        ancestry.add(event)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_event.assert_called_once_with(event)

    def test_with_public_file_should_not_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_file = mocker.patch('betty.anonymizer.anonymize_file')
        file = File('F0', Path(__file__))
        file.private = False
        ancestry = Ancestry()
        ancestry.add(file)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_file.assert_not_called()

    def test_with_private_file_should_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_file = mocker.patch('betty.anonymizer.anonymize_file')
        file = File('F0', Path(__file__))
        file.private = True
        ancestry = Ancestry()
        ancestry.add(file)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_file.assert_called_once_with(file)

    def test_with_public_source_should_not_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_source = mocker.patch('betty.anonymizer.anonymize_source')
        source = Source('S0', 'The Source')
        source.private = False
        ancestry = Ancestry()
        ancestry.add(source)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_source.assert_not_called()

    def test_with_private_source_should_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_source = mocker.patch('betty.anonymizer.anonymize_source')
        source = Source('S0', 'The Source')
        source.private = True
        ancestry = Ancestry()
        ancestry.add(source)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_source.assert_called_once_with(source, ancestry, ANY)

    def test_with_public_citation_should_not_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_citation = mocker.patch('betty.anonymizer.anonymize_citation')
        source = Source('The Source')
        citation = Citation('C0', source)
        citation.private = False
        ancestry = Ancestry()
        ancestry.add(citation)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_citation.assert_not_called()

    def test_with_private_citation_should_anonymize(self, mocker: MockerFixture) -> None:
        m_anonymize_citation = mocker.patch('betty.anonymizer.anonymize_citation')
        source = Source('The Source')
        citation = Citation('C0', source)
        citation.private = True
        ancestry = Ancestry()
        ancestry.add(citation)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_citation.assert_called_once_with(citation, ancestry, ANY)


class TestAnonymizePerson:
    def test_should_remove_citations(self) -> None:
        person = Person('P0')
        source = Source('The Source')
        citation = Citation(None, source)
        person.citations.add(citation)
        anonymize_person(person)
        assert 0 == len(person.citations)

    def test_should_remove_files(self) -> None:
        person = Person('P0')
        person.files.add(File('F0', Path(__file__)))
        anonymize_person(person)
        assert 0 == len(person.files)

    def test_should_remove_names(self) -> None:
        person = Person('P0')
        name = PersonName(person, 'Jane', 'Dough')
        source = Source('The Source')
        citation = Citation(None, source)
        name.citations.add(citation)
        anonymize_person(person)
        assert 0 == len(person.names)
        assert 0 == len(citation.facts)

    def test_should_remove_presences(self) -> None:
        person = Person('P0')
        event = Event(None, Birth)
        Presence(person, Subject(), event)
        anonymize_person(person)
        assert 0 == len(person.presences)
        assert 0 == len(event.presences)

    def test_should_remove_parents_without_public_descendants(self) -> None:
        person = Person('P0')
        person.private = True
        child = Person('P1')
        child.private = True
        person.children.add(child)
        parent = Person('P2')
        parent.private = True
        person.parents.add(parent)

        anonymize_person(person)
        assert [] == list(person.parents)

    def test_should_not_remove_parents_with_public_descendants(self) -> None:
        person = Person('P0')
        person.private = True
        child = Person('P1')
        child.private = False
        person.children.add(child)
        parent = Person('P2')
        parent.private = True
        person.parents.add(parent)

        anonymize_person(person)
        assert [parent] == list(person.parents)


class TestAnonymizeEvent:
    def test_should_remove_citations(self) -> None:
        event = Event(None, Birth)
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        event.citations.add(citation)
        anonymize_event(event)
        assert 0 == len(event.citations)

    def test_should_remove_files(self) -> None:
        event = Event(None, Birth)
        event.files.add(File('F0', Path(__file__)))
        anonymize_event(event)
        assert 0 == len(event.files)

    def test_should_remove_presences(self) -> None:
        event = Event(None, Birth)
        person = Person('P1')
        Presence(person, Subject(), event)
        anonymize_event(event)
        assert 0 == len(event.presences)


class TestAnonymizeFile:
    def test_should_remove_entity(self) -> None:
        file = File('F0', Path(__file__))
        file.entities.add(Person('P0'))
        anonymize_file(file)
        assert 0 == len(file.entities)


class TestAnonymizeSource:
    def test_should_remove_citations(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.add(source)
        citation = Citation(None, source)
        source.citations.add(citation)
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert 0 == len(source.citations)
        assert citation in anonymous_source.citations

    def test_should_remove_contained_by(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.add(source)
        contained_by = Source(None, 'The Source')
        source.contained_by = contained_by
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert source.contained_by is None

    def test_should_remove_contains(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.add(source)
        contains = Source(None, 'The Source')
        source.contains.add(contains)
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert 0 == len(source.contains)
        assert contains in anonymous_source.contains

    def test_should_remove_files(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.add(source)
        file = File('F0', Path(__file__))
        source.files.add(file)
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert 0 == len(source.files)
        assert file in anonymous_source.files


class TestAnonymizeCitation:
    def test_should_remove_facts(self) -> None:
        ancestry = Ancestry()
        source = Source('The Source')
        citation = Citation('C0', source)
        ancestry.add(citation)
        fact = PersonName(Person(None), 'Jane')
        citation.facts.add(fact)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, ancestry, anonymous_citation)
        assert 0 == len(citation.facts)
        assert fact in anonymous_citation.facts

    def test_should_remove_files(self) -> None:
        ancestry = Ancestry()
        source = Source('The Source')
        citation = Citation('C0', source)
        ancestry.add(citation)
        file = File('F0', Path(__file__))
        citation.files.add(file)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, ancestry, anonymous_citation)
        assert 0 == len(citation.files)
        assert file in anonymous_citation.files

    def test_should_remove_source(self) -> None:
        ancestry = Ancestry()
        source = Source('The Source')
        citation = Citation('C0', source)
        ancestry.add(citation)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, ancestry, anonymous_citation)
        assert citation.source is None
