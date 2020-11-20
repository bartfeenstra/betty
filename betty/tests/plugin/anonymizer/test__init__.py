import gettext
from tempfile import TemporaryDirectory
from unittest.mock import patch, ANY, Mock

from betty.ancestry import Ancestry, Person, File, Source, Citation, PersonName, Presence, Event, IdentifiableEvent, \
    IdentifiableSource, IdentifiableCitation, Birth, Subject, HasCitations
from betty.config import Configuration
from betty.asyncio import sync
from betty.parse import parse
from betty.plugin.anonymizer import Anonymizer, anonymize, anonymize_person, anonymize_event, anonymize_file, \
    anonymize_citation, anonymize_source, AnonymousSource, AnonymousCitation
from betty.site import Site
from betty.tests import TestCase


class AnonymousSourceTest(TestCase):
    def test_name(self):
        self.assertIsInstance(AnonymousSource().name, str)

    def test_replace(self):
        citations = [Citation(Source())]
        contains = [Source()]
        files = [Mock(File)]
        sut = AnonymousSource()
        other = AnonymousSource()
        other.citations = citations
        other.contains = contains
        other.files = files
        sut.replace(other)
        self.assertEquals(citations, list(sut.citations))
        self.assertEquals(contains, list(sut.contains))
        self.assertEquals(files, list(sut.files))


class AnonymousCitationTest(TestCase):
    def test_location(self):
        source = Mock(Source)
        self.assertIsInstance(AnonymousCitation(source).location, str)

    def test_replace(self):
        facts = [HasCitations()]
        files = [File('F1', __file__)]
        source = Mock(Source)
        sut = AnonymousCitation(source)
        other = AnonymousCitation(source)
        other.facts = facts
        other.files = files
        sut.replace(other)
        self.assertEquals(facts, list(sut.facts))
        self.assertEquals(files, list(sut.files))


class AnonymizeTest(TestCase):
    def setUp(self) -> None:
        gettext.NullTranslations().install()

    @patch('betty.plugin.anonymizer.anonymize_person')
    def test_with_public_person_should_not_anonymize(self, m_anonymize_person) -> None:
        person = Person('P0')
        person.private = False
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        anonymize(ancestry)
        m_anonymize_person.assert_not_called()

    @patch('betty.plugin.anonymizer.anonymize_person')
    def test_with_private_person_should_anonymize(self, m_anonymize_person) -> None:
        person = Person('P0')
        person.private = True
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        anonymize(ancestry)
        m_anonymize_person.assert_called_once_with(person)

    @patch('betty.plugin.anonymizer.anonymize_event')
    def test_with_public_event_should_not_anonymize(self, m_anonymize_event) -> None:
        event = IdentifiableEvent('E0', Birth())
        event.private = False
        ancestry = Ancestry()
        ancestry.events[event.id] = event
        anonymize(ancestry)
        m_anonymize_event.assert_not_called()

    @patch('betty.plugin.anonymizer.anonymize_event')
    def test_with_private_event_should_anonymize(self, m_anonymize_event) -> None:
        event = IdentifiableEvent('E0', Birth())
        event.private = True
        ancestry = Ancestry()
        ancestry.events[event.id] = event
        anonymize(ancestry)
        m_anonymize_event.assert_called_once_with(event)

    @patch('betty.plugin.anonymizer.anonymize_file')
    def test_with_public_file_should_not_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', __file__)
        file.private = False
        ancestry = Ancestry()
        ancestry.files[file.id] = file
        anonymize(ancestry)
        m_anonymize_file.assert_not_called()

    @patch('betty.plugin.anonymizer.anonymize_file')
    def test_with_private_file_should_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', __file__)
        file.private = True
        ancestry = Ancestry()
        ancestry.files[file.id] = file
        anonymize(ancestry)
        m_anonymize_file.assert_called_once_with(file)

    @patch('betty.plugin.anonymizer.anonymize_source')
    def test_with_public_source_should_not_anonymize(self, m_anonymize_source) -> None:
        source = IdentifiableSource('S0', 'The Source')
        source.private = False
        ancestry = Ancestry()
        ancestry.sources[source.id] = source
        anonymize(ancestry)
        m_anonymize_source.assert_not_called()

    @patch('betty.plugin.anonymizer.anonymize_source')
    def test_with_private_source_should_anonymize(self, m_anonymize_source) -> None:
        source = IdentifiableSource('S0', 'The Source')
        source.private = True
        ancestry = Ancestry()
        ancestry.sources[source.id] = source
        anonymize(ancestry)
        m_anonymize_source.assert_called_once_with(source, ANY)

    @patch('betty.plugin.anonymizer.anonymize_citation')
    def test_with_public_citation_should_not_anonymize(self, m_anonymize_citation) -> None:
        source = Source('The Source')
        citation = IdentifiableCitation('C0', source)
        citation.private = False
        ancestry = Ancestry()
        ancestry.citations[citation.id] = citation
        anonymize(ancestry)
        m_anonymize_citation.assert_not_called()

    @patch('betty.plugin.anonymizer.anonymize_citation')
    def test_with_private_citation_should_anonymize(self, m_anonymize_citation) -> None:
        source = Source('The Source')
        citation = IdentifiableCitation('C0', source)
        citation.private = True
        ancestry = Ancestry()
        ancestry.citations[citation.id] = citation
        anonymize(ancestry)
        m_anonymize_citation.assert_called_once_with(citation, ANY)


class AnonymizePersonTest(TestCase):
    def test_should_remove_citations(self) -> None:
        person = Person('P0')
        source = Source('The Source')
        citation = Citation(source)
        person.citations.append(citation)
        anonymize_person(person)
        self.assertEquals(0, len(person.citations))

    def test_should_remove_files(self) -> None:
        person = Person('P0')
        person.files.append(File('F0', __file__))
        anonymize_person(person)
        self.assertEquals(0, len(person.files))

    def test_should_remove_names(self) -> None:
        person = Person('P0')
        name = PersonName('Jane', 'Dough')
        source = Source('The Source')
        citation = Citation(source)
        name.citations.append(citation)
        person.names.append(name)
        anonymize_person(person)
        self.assertEquals(0, len(person.names))
        self.assertEquals(0, len(citation.facts))

    def test_should_remove_presences(self) -> None:
        person = Person('P0')
        event = Event(Birth())
        Presence(person, Subject(), event)
        anonymize_person(person)
        self.assertEquals(0, len(person.presences))
        self.assertEquals(0, len(event.presences))

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
        self.assertCountEqual([], person.parents)

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
        self.assertCountEqual([parent], person.parents)


class AnonymizeEventTest(TestCase):
    def test_should_remove_citations(self) -> None:
        event = Event(Birth())
        source = Source('The Source')
        citation = Citation(source)
        event.citations.append(citation)
        anonymize_event(event)
        self.assertEquals(0, len(event.citations))

    def test_should_remove_files(self) -> None:
        event = Event(Birth())
        event.files.append(File('F0', __file__))
        anonymize_event(event)
        self.assertEquals(0, len(event.files))

    def test_should_remove_presences(self) -> None:
        event = Event(Birth())
        person = Person('P1')
        Presence(person, Subject(), event)
        anonymize_event(event)
        self.assertEquals(0, len(event.presences))


class AnonymizeFileTest(TestCase):
    def test_should_remove_resources(self) -> None:
        file = File('F0', __file__)
        file.resources.append(Person('P0'))
        anonymize_file(file)
        self.assertEquals(0, len(file.resources))


class AnonymizeSourceTest(TestCase):
    def setUp(self) -> None:
        gettext.NullTranslations().install()

    def test_should_remove_citations(self) -> None:
        source = IdentifiableSource('S0', 'The Source')
        citation = Citation(source)
        source.citations.append(citation)
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertEquals(0, len(source.citations))
        self.assertIn(citation, anonymous_source.citations)

    def test_should_remove_contained_by(self) -> None:
        source = IdentifiableSource('S0', 'The Source')
        contained_by = Source('The Source')
        source.contained_by = contained_by
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertIsNone(source.contained_by)

    def test_should_remove_contains(self) -> None:
        source = IdentifiableSource('S0', 'The Source')
        contains = Source('The Source')
        source.contains.append(contains)
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertEquals(0, len(source.contains))
        self.assertIn(contains, anonymous_source.contains)

    def test_should_remove_files(self) -> None:
        source = IdentifiableSource('S0', 'The Source')
        file = File('F0', __file__)
        source.files.append(file)
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertEquals(0, len(source.files))
        self.assertIn(file, anonymous_source.files)


class AnonymizeCitationTest(TestCase):
    def setUp(self) -> None:
        gettext.NullTranslations().install()

    def test_should_remove_facts(self) -> None:
        source = Source('The Source')
        citation = IdentifiableCitation('C0', source)
        fact = PersonName('Jane')
        citation.facts.append(fact)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, anonymous_citation)
        self.assertEquals(0, len(citation.facts))
        self.assertIn(fact, anonymous_citation.facts)

    def test_should_remove_files(self) -> None:
        source = Source('The Source')
        citation = IdentifiableCitation('C0', source)
        file = File('F0', __file__)
        citation.files.append(file)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, anonymous_citation)
        self.assertEquals(0, len(citation.files))
        self.assertIn(file, anonymous_citation.files)

    def test_should_remove_source(self) -> None:
        source = Source('The Source')
        citation = IdentifiableCitation('C0', source)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, anonymous_citation)
        self.assertIsNone(citation.source)


class AnonymizerTest(TestCase):
    @sync
    async def test_post_parse(self) -> None:
        person = Person('P0')
        person.private = True
        person.names.append(PersonName('Jane', 'Dough'))
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = None
            async with Site(configuration) as site:
                site.ancestry.people[person.id] = person
                await parse(site)
        self.assertEquals(0, len(person.names))
