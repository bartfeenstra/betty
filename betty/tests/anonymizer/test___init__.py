from pathlib import Path
from unittest.mock import patch, ANY, Mock

from betty.anonymizer import anonymize, anonymize_person, anonymize_event, anonymize_file, anonymize_citation, \
    anonymize_source, AnonymousSource, AnonymousCitation, Anonymizer
from betty.app import App
from betty.load import load
from betty.model import Entity
from betty.model.ancestry import Ancestry, Person, File, Source, Citation, PersonName, Presence, Event, Subject, \
    HasCitations
from betty.model.event_type import Birth
from betty.project import ExtensionConfiguration


class TestAnonymousSource:
    def test_name(self):
        with App():
            assert isinstance(AnonymousSource().name, str)

    def test_replace(self):
        with App():
            ancestry = Ancestry()
            citations = [Citation(None, Source(None))]
            contains = [Source(None)]
            files = [Mock(File)]
            sut = AnonymousSource()
            other = Source(None)
            ancestry.entities.append(other)
            other.citations = citations  # type: ignore
            other.contains = contains  # type: ignore
            other.files = files  # type: ignore
            sut.replace(other, ancestry)
            assert citations == list(sut.citations)
            assert contains == list(sut.contains)
            assert files == list(sut.files)
            assert other not in ancestry.entities


class TestAnonymousCitation:
    def test_location(self):
        source = Mock(Source)
        with App():
            assert isinstance(AnonymousCitation(source).location, str)

    def test_replace(self):
        class _HasCitations(HasCitations, Entity):
            pass
        ancestry = Ancestry()
        facts = [_HasCitations()]
        files = [File('F1', Path(__file__))]
        source = Mock(Source)
        sut = AnonymousCitation(source)
        other = Citation(None, source)
        ancestry.entities.append(other)
        other.facts = facts  # type: ignore
        other.files = files  # type: ignore
        sut.replace(other, ancestry)
        assert facts == list(sut.facts)
        assert files == list(sut.files)
        assert other not in ancestry.entities


class TestAnonymize:
    @patch('betty.anonymizer.anonymize_person')
    def test_with_public_person_should_not_anonymize(self, m_anonymize_person) -> None:
        person = Person('P0')
        person.private = False
        ancestry = Ancestry()
        ancestry.entities.append(person)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_person.assert_not_called()

    @patch('betty.anonymizer.anonymize_person')
    def test_with_private_person_should_anonymize(self, m_anonymize_person) -> None:
        person = Person('P0')
        person.private = True
        ancestry = Ancestry()
        ancestry.entities.append(person)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_person.assert_called_once_with(person)

    @patch('betty.anonymizer.anonymize_event')
    def test_with_public_event_should_not_anonymize(self, m_anonymize_event) -> None:
        event = Event('E0', Birth)
        event.private = False
        ancestry = Ancestry()
        ancestry.entities.append(event)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_event.assert_not_called()

    @patch('betty.anonymizer.anonymize_event')
    def test_with_private_event_should_anonymize(self, m_anonymize_event) -> None:
        event = Event('E0', Birth)
        event.private = True
        ancestry = Ancestry()
        ancestry.entities.append(event)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_event.assert_called_once_with(event)

    @patch('betty.anonymizer.anonymize_file')
    def test_with_public_file_should_not_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', Path(__file__))
        file.private = False
        ancestry = Ancestry()
        ancestry.entities.append(file)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_file.assert_not_called()

    @patch('betty.anonymizer.anonymize_file')
    def test_with_private_file_should_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', Path(__file__))
        file.private = True
        ancestry = Ancestry()
        ancestry.entities.append(file)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_file.assert_called_once_with(file)

    @patch('betty.anonymizer.anonymize_source')
    def test_with_public_source_should_not_anonymize(self, m_anonymize_source) -> None:
        source = Source('S0', 'The Source')
        source.private = False
        ancestry = Ancestry()
        ancestry.entities.append(source)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_source.assert_not_called()

    @patch('betty.anonymizer.anonymize_source')
    def test_with_private_source_should_anonymize(self, m_anonymize_source) -> None:
        source = Source('S0', 'The Source')
        source.private = True
        ancestry = Ancestry()
        ancestry.entities.append(source)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_source.assert_called_once_with(source, ancestry, ANY)

    @patch('betty.anonymizer.anonymize_citation')
    def test_with_public_citation_should_not_anonymize(self, m_anonymize_citation) -> None:
        source = Source('The Source')
        citation = Citation('C0', source)
        citation.private = False
        ancestry = Ancestry()
        ancestry.entities.append(citation)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_citation.assert_not_called()

    @patch('betty.anonymizer.anonymize_citation')
    def test_with_private_citation_should_anonymize(self, m_anonymize_citation) -> None:
        source = Source('The Source')
        citation = Citation('C0', source)
        citation.private = True
        ancestry = Ancestry()
        ancestry.entities.append(citation)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_citation.assert_called_once_with(citation, ancestry, ANY)


class TestAnonymizePerson:
    def test_should_remove_citations(self) -> None:
        person = Person('P0')
        source = Source('The Source')
        citation = Citation(None, source)
        person.citations.append(citation)
        anonymize_person(person)
        assert 0 == len(person.citations)

    def test_should_remove_files(self) -> None:
        person = Person('P0')
        person.files.append(File('F0', Path(__file__)))
        anonymize_person(person)
        assert 0 == len(person.files)

    def test_should_remove_names(self) -> None:
        person = Person('P0')
        name = PersonName(person, 'Jane', 'Dough')
        source = Source('The Source')
        citation = Citation(None, source)
        name.citations.append(citation)
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
        person.children.append(child)
        parent = Person('P2')
        parent.private = True
        person.parents.append(parent)

        anonymize_person(person)
        assert [] == list(person.parents)

    def test_should_not_remove_parents_with_public_descendants(self) -> None:
        person = Person('P0')
        person.private = True
        child = Person('P1')
        child.private = False
        person.children.append(child)
        parent = Person('P2')
        parent.private = True
        person.parents.append(parent)

        anonymize_person(person)
        assert [parent] == list(person.parents)


class TestAnonymizeEvent:
    def test_should_remove_citations(self) -> None:
        event = Event(None, Birth)
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        event.citations.append(citation)
        anonymize_event(event)
        assert 0 == len(event.citations)

    def test_should_remove_files(self) -> None:
        event = Event(None, Birth)
        event.files.append(File('F0', Path(__file__)))
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
        file.entities.append(Person('P0'))
        anonymize_file(file)
        assert 0 == len(file.entities)


class TestAnonymizeSource:
    def test_should_remove_citations(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.entities.append(source)
        citation = Citation(None, source)
        source.citations.append(citation)
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert 0 == len(source.citations)
        assert citation in anonymous_source.citations

    def test_should_remove_contained_by(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.entities.append(source)
        contained_by = Source(None, 'The Source')
        source.contained_by = contained_by
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert source.contained_by is None

    def test_should_remove_contains(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.entities.append(source)
        contains = Source(None, 'The Source')
        source.contains.append(contains)
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert 0 == len(source.contains)
        assert contains in anonymous_source.contains

    def test_should_remove_files(self) -> None:
        ancestry = Ancestry()
        source = Source('S0', 'The Source')
        ancestry.entities.append(source)
        file = File('F0', Path(__file__))
        source.files.append(file)
        anonymous_source = AnonymousSource()
        anonymize_source(source, ancestry, anonymous_source)
        assert 0 == len(source.files)
        assert file in anonymous_source.files


class TestAnonymizeCitation:
    def test_should_remove_facts(self) -> None:
        ancestry = Ancestry()
        source = Source('The Source')
        citation = Citation('C0', source)
        ancestry.entities.append(citation)
        fact = PersonName(Person(None), 'Jane')
        citation.facts.append(fact)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, ancestry, anonymous_citation)
        assert 0 == len(citation.facts)
        assert fact in anonymous_citation.facts

    def test_should_remove_files(self) -> None:
        ancestry = Ancestry()
        source = Source('The Source')
        citation = Citation('C0', source)
        ancestry.entities.append(citation)
        file = File('F0', Path(__file__))
        citation.files.append(file)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, ancestry, anonymous_citation)
        assert 0 == len(citation.files)
        assert file in anonymous_citation.files

    def test_should_remove_source(self) -> None:
        ancestry = Ancestry()
        source = Source('The Source')
        citation = Citation('C0', source)
        ancestry.entities.append(citation)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, ancestry, anonymous_citation)
        assert citation.source is None


class TestAnonymizer:
    async def test_post_parse(self) -> None:
        person = Person('P0')
        person.private = True
        PersonName(person, 'Jane', 'Dough')
        with App() as app:
            app.project.configuration.extensions.add(ExtensionConfiguration(Anonymizer))
            app.project.ancestry.entities.append(person)
            await load(app)
        assert 0 == len(person.names)
