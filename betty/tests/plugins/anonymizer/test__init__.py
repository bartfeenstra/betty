from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, Document
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.anonymizer import Anonymizer
from betty.site import Site


class AnonymizerTest(TestCase):
    def assert_anonymized(self, person: Person):
        self.assertIsNone(person.individual_name)
        self.assertIsNone(person.family_name)
        self.assertCountEqual([], person.events)
        self.assertCountEqual([], person.documents)

    def assert_not_anonymized(self, person: Person):
        self.assertIsNotNone(person.individual_name)
        self.assertIsNotNone(person.family_name)
        self.assertNotEqual([], sorted(person.events))
        self.assertNotEqual([], sorted(person.documents))

    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = {}
            with Site(configuration) as site:
                with NamedTemporaryFile() as document_f:
                    person = Person('P0', 'Janet', 'Dough')
                    person.private = True
                    person.events.add(Event('E0', Event.Type.BIRTH))
                    person.documents.add(Document('D0', document_f.name))
                    site.ancestry.people[person.id] = person
                    parse(site)
                    self.assert_anonymized(person)

    def test_anonymize_should_anonymize_private_person(self):
        with NamedTemporaryFile() as document_f:
            person = Person('P0', 'Janet', 'Dough')
            person.private = True
            partner = Person('P1', 'Jenny', 'Donut')
            event = Event('E0', Event.Type.MARRIAGE)
            event.people.add(person, partner)
            document = Document('D0', document_f.name)
            document.entities.add(person, partner)
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_anonymized(person)
            self.assertCountEqual([], event.people)
            self.assertCountEqual([], document.entities)

    def test_anonymize_should_not_anonymize_non_private_person(self):
        with NamedTemporaryFile() as document_f:
            person = Person('P0', 'Janet', 'Dough')
            person.events.add(Event('E0', Event.Type.BIRTH))
            person.documents.add(Document('D0', document_f.name))
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_not_anonymized(person)
