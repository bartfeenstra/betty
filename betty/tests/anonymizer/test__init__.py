from gettext import NullTranslations
from unittest.mock import patch, ANY, Mock

from betty.app import App, AppExtensionConfiguration
from betty.asyncio import sync
from betty.anonymizer import anonymize, anonymize_person, anonymize_event, anonymize_file, anonymize_citation, \
    anonymize_source, AnonymousSource, AnonymousCitation, Anonymizer
from betty.load import load
from betty.locale import Translations
from betty.model import Entity
from betty.model.ancestry import Ancestry, Person, File, Source, Citation, PersonName, Presence, Event, Subject, \
    HasCitations
from betty.model.event_type import Birth
from betty.tests import TestCase


class AnonymousSourceTest(TestCase):
    def setUp(self) -> None:
        self._translations = Translations(NullTranslations())
        self._translations.install()

    def tearDown(self) -> None:
        self._translations.uninstall()

    def test_name(self):
        self.assertIsInstance(AnonymousSource().name, str)

    def test_replace(self):
        citations = [Citation(None, Source(None))]
        contains = [Source(None)]
        files = [Mock(File)]
        sut = AnonymousSource()
        other = AnonymousSource()
        other.citations = citations
        other.contains = contains
        other.files = files
        sut.replace(other)
        self.assertEqual(citations, list(sut.citations))
        self.assertEqual(contains, list(sut.contains))
        self.assertEqual(files, list(sut.files))


class AnonymousCitationTest(TestCase):
    def setUp(self) -> None:
        self._translations = Translations(NullTranslations())
        self._translations.install()

    def tearDown(self) -> None:
        self._translations.uninstall()

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
        self.assertEqual(facts, list(sut.facts))
        self.assertEqual(files, list(sut.files))


class AnonymizeTest(TestCase):
    def setUp(self) -> None:
        self._translations = Translations(NullTranslations())
        self._translations.install()

    def tearDown(self) -> None:
        self._translations.uninstall()

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
        event = Event('E0', Birth())
        event.private = False
        ancestry = Ancestry()
        ancestry.entities.append(event)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_event.assert_not_called()

    @patch('betty.anonymizer.anonymize_event')
    def test_with_private_event_should_anonymize(self, m_anonymize_event) -> None:
        event = Event('E0', Birth())
        event.private = True
        ancestry = Ancestry()
        ancestry.entities.append(event)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_event.assert_called_once_with(event)

    @patch('betty.anonymizer.anonymize_file')
    def test_with_public_file_should_not_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', __file__)
        file.private = False
        ancestry = Ancestry()
        ancestry.entities.append(file)
        anonymize(ancestry, AnonymousCitation(AnonymousSource()))
        m_anonymize_file.assert_not_called()

    @patch('betty.anonymizer.anonymize_file')
    def test_with_private_file_should_anonymize(self, m_anonymize_file) -> None:
        file = File('F0', __file__)
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
        m_anonymize_source.assert_called_once_with(source, ANY)

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
        m_anonymize_citation.assert_called_once_with(citation, ANY)


class AnonymizePersonTest(TestCase):
    def test_should_remove_citations(self) -> None:
        person = Person('P0')
        source = Source('The Source')
        citation = Citation(None, source)
        person.citations.append(citation)
        anonymize_person(person)
        self.assertEqual(0, len(person.citations))

    def test_should_remove_files(self) -> None:
        person = Person('P0')
        person.files.append(File('F0', __file__))
        anonymize_person(person)
        self.assertEqual(0, len(person.files))

    def test_should_remove_names(self) -> None:
        person = Person('P0')
        name = PersonName(person, 'Jane', 'Dough')
        source = Source('The Source')
        citation = Citation(None, source)
        name.citations.append(citation)
        anonymize_person(person)
        self.assertEqual(0, len(person.names))
        self.assertEqual(0, len(citation.facts))

    def test_should_remove_presences(self) -> None:
        person = Person('P0')
        event = Event(None, Birth())
        Presence(person, Subject(), event)
        anonymize_person(person)
        self.assertEqual(0, len(person.presences))
        self.assertEqual(0, len(event.presences))

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
        event = Event(None, Birth())
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        event.citations.append(citation)
        anonymize_event(event)
        self.assertEqual(0, len(event.citations))

    def test_should_remove_files(self) -> None:
        event = Event(None, Birth())
        event.files.append(File('F0', __file__))
        anonymize_event(event)
        self.assertEqual(0, len(event.files))

    def test_should_remove_presences(self) -> None:
        event = Event(None, Birth())
        person = Person('P1')
        Presence(person, Subject(), event)
        anonymize_event(event)
        self.assertEqual(0, len(event.presences))


class AnonymizeFileTest(TestCase):
    def test_should_remove_entity(self) -> None:
        file = File('F0', __file__)
        file.entities.append(Person('P0'))
        anonymize_file(file)
        self.assertEqual(0, len(file.entities))


class AnonymizeSourceTest(TestCase):
    def setUp(self) -> None:
        self._translations = Translations(NullTranslations())
        self._translations.install()

    def tearDown(self) -> None:
        self._translations.uninstall()

    def test_should_remove_citations(self) -> None:
        source = Source('S0', 'The Source')
        citation = Citation(None, source)
        source.citations.append(citation)
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertEqual(0, len(source.citations))
        self.assertIn(citation, anonymous_source.citations)

    def test_should_remove_contained_by(self) -> None:
        source = Source('S0', 'The Source')
        contained_by = Source(None, 'The Source')
        source.contained_by = contained_by
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertIsNone(source.contained_by)

    def test_should_remove_contains(self) -> None:
        source = Source('S0', 'The Source')
        contains = Source(None, 'The Source')
        source.contains.append(contains)
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertEqual(0, len(source.contains))
        self.assertIn(contains, anonymous_source.contains)

    def test_should_remove_files(self) -> None:
        source = Source('S0', 'The Source')
        file = File('F0', __file__)
        source.files.append(file)
        anonymous_source = AnonymousSource()
        anonymize_source(source, anonymous_source)
        self.assertEqual(0, len(source.files))
        self.assertIn(file, anonymous_source.files)


class AnonymizeCitationTest(TestCase):
    def setUp(self) -> None:
        self._translations = Translations(NullTranslations())
        self._translations.install()

    def tearDown(self) -> None:
        self._translations.uninstall()

    def test_should_remove_facts(self) -> None:
        source = Source('The Source')
        citation = Citation('C0', source)
        fact = PersonName(Person(None), 'Jane')
        citation.facts.append(fact)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, anonymous_citation)
        self.assertEqual(0, len(citation.facts))
        self.assertIn(fact, anonymous_citation.facts)

    def test_should_remove_files(self) -> None:
        source = Source('The Source')
        citation = Citation('C0', source)
        file = File('F0', __file__)
        citation.files.append(file)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, anonymous_citation)
        self.assertEqual(0, len(citation.files))
        self.assertIn(file, anonymous_citation.files)

    def test_should_remove_source(self) -> None:
        source = Source('The Source')
        citation = Citation('C0', source)
        anonymous_source = AnonymousSource()
        anonymous_citation = AnonymousCitation(anonymous_source)
        anonymize_citation(citation, anonymous_citation)
        self.assertIsNone(citation.source)


class AnonymizerTest(TestCase):
    @sync
    async def test_post_parse(self) -> None:
        person = Person('P0')
        person.private = True
        PersonName(person, 'Jane', 'Dough')
        async with App() as app:
            app.configuration.extensions.add(AppExtensionConfiguration(Anonymizer))
            app.ancestry.entities.append(person)
            await load(app)
        self.assertEqual(0, len(person.names))
