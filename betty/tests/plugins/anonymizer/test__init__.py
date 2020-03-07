from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from betty.ancestry import Ancestry, Person, File, Source, Citation, PersonName, Presence, Event, IdentifiableEvent
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.anonymizer import Anonymizer, anonymize, anonymize_person, anonymize_event, anonymize_file, \
    anonymize_citation, anonymize_source
from betty.site import Site


class AnonymizeTest(TestCase):
    @patch('betty.plugins.anonymizer.anonymize_person')
    def test_with_public_person_should_not_anonymize(self, m_anonymize_person) -> None:
        person = Person('P0')
        person.private = False
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        anonymize(ancestry)
        m_anonymize_person.assert_not_called()

    @patch('betty.plugins.anonymizer.anonymize_person')
    def test_with_private_person_should_anonymize(self, m_anonymize_person) -> None:
        person = Person('P0')
        person.private = True
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        anonymize(ancestry)
        m_anonymize_person.assert_called_once_with(person)

    @patch('betty.plugins.anonymizer.anonymize_event')
    def test_with_public_event_should_not_anonymize(self, m_anonymize_event) -> None:
        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        event.private = False
        ancestry = Ancestry()
        ancestry.events[event.id] = event
        anonymize(ancestry)
        m_anonymize_event.assert_not_called()

    @patch('betty.plugins.anonymizer.anonymize_event')
    def test_with_private_event_should_anonymize(self, m_anonymize_event) -> None:
        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        event.private = True
        ancestry = Ancestry()
        ancestry.events[event.id] = event
        anonymize(ancestry)
        m_anonymize_event.assert_called_once_with(event)

    @patch('betty.plugins.anonymizer.anonymize_file')
    def test_with_public_file_should_not_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', __file__)
        file.private = False
        ancestry = Ancestry()
        ancestry.files[file.id] = file
        anonymize(ancestry)
        m_anonymize_file.assert_not_called()

    @patch('betty.plugins.anonymizer.anonymize_file')
    def test_with_private_file_should_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', __file__)
        file.private = True
        ancestry = Ancestry()
        ancestry.files[file.id] = file
        anonymize(ancestry)
        m_anonymize_file.assert_called_once_with(file)

    @patch('betty.plugins.anonymizer.anonymize_source')
    def test_with_public_source_should_not_anonymize(self, m_anonymize_source) -> None:
        source = Source('S0', 'The Source')
        source.private = False
        ancestry = Ancestry()
        ancestry.sources[source.id] = source
        anonymize(ancestry)
        m_anonymize_source.assert_not_called()

    @patch('betty.plugins.anonymizer.anonymize_source')
    def test_with_private_source_should_anonymize(self, m_anonymize_source) -> None:
        source = Source('S0', 'The Source')
        source.private = True
        ancestry = Ancestry()
        ancestry.sources[source.id] = source
        anonymize(ancestry)
        m_anonymize_source.assert_called_once_with(source)

    @patch('betty.plugins.anonymizer.anonymize_citation')
    def test_with_public_citation_should_not_anonymize(self, m_anonymize_citation) -> None:
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        citation.private = False
        ancestry = Ancestry()
        ancestry.citations[citation.id] = citation
        anonymize(ancestry)
        m_anonymize_citation.assert_not_called()

    @patch('betty.plugins.anonymizer.anonymize_citation')
    def test_with_private_citation_should_anonymize(self, m_anonymize_citation) -> None:
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        citation.private = True
        ancestry = Ancestry()
        ancestry.citations[citation.id] = citation
        anonymize(ancestry)
        m_anonymize_citation.assert_called_once_with(citation)


class AnonymizePersonTest(TestCase):
    def test_should_remove_citations(self) -> None:
        person = Person('P0')
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
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
        person.names.append(PersonName('Jane', 'Doughh'))
        anonymize_person(person)
        self.assertEquals(0, len(person.names))

    def test_should_remove_presences(self) -> None:
        person = Person('P0')
        person.presences.append(Presence(Presence.Role.SUBJECT))
        anonymize_person(person)
        self.assertEquals(0, len(person.presences))

    def test_should_remove_parents_without_public_descendants(self) -> None:
        person = Person('P0')
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
        event = Event(Event.Type.BIRTH)
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        event.citations.append(citation)
        anonymize_event(event)
        self.assertEquals(0, len(event.citations))

    def test_should_remove_files(self) -> None:
        event = Event(Event.Type.BIRTH)
        event.files.append(File('F0', __file__))
        anonymize_event(event)
        self.assertEquals(0, len(event.files))

    def test_should_remove_presences(self) -> None:
        event = Event(Event.Type.BIRTH)
        event.presences.append(Presence(Presence.Role.SUBJECT))
        anonymize_event(event)
        self.assertEquals(0, len(event.presences))


class AnonymizeFileTest(TestCase):
    def test_should_remove_resources(self) -> None:
        file = File('F0', __file__)
        file.resources.append(Person('P0'))
        anonymize_file(file)
        self.assertEquals(0, len(file.resources))


class AnonymizeSourceTest(TestCase):
    def test_should_remove_citations(self) -> None:
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        source.citations.append(citation)
        anonymize_source(source)
        self.assertEquals(0, len(source.citations))

    def test_should_remove_contained_by(self) -> None:
        source = Source('S0', 'The Source')
        contained_by = Source('S1', 'The Source')
        source.contained_by = contained_by
        anonymize_source(source)
        self.assertIsNone(source.contained_by)

    def test_should_remove_contains(self) -> None:
        source = Source('S0', 'The Source')
        contains = Source('S1', 'The Source')
        source.contains.append(contains)
        anonymize_source(source)
        self.assertEquals(0, len(source.contains))

    def test_should_remove_files(self) -> None:
        source = Source('S0', 'The Source')
        source.files.append(File('F0', __file__))
        anonymize_source(source)
        self.assertEquals(0, len(source.files))


class AnonymizeCitationTest(TestCase):
    def test_should_remove_facts(self) -> None:
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        citation.facts.append(PersonName('Jane'))
        anonymize_citation(citation)
        self.assertEquals(0, len(citation.facts))

    def test_should_remove_files(self) -> None:
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        citation.files.append(File('F0', __file__))
        anonymize_citation(citation)
        self.assertEquals(0, len(citation.files))

    def test_should_remove_source(self) -> None:
        source = Source('S0', 'The Source')
        citation = Citation('C0', source)
        anonymize_citation(citation)
        self.assertIsNone(citation.source)


class AnonymizerTest(TestCase):
    def test_post_parse(self) -> None:
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = {}
            site = Site(configuration)
            person = Person('P0')
            person.private = True
            person.names.append(PersonName('Jane', 'Dough'))
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertEquals(0, len(person.names))
