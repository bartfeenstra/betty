from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, Document, Date
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.anonymizer import Anonymizer
from betty.site import Site


class AnonymizerTest(TestCase):
    def assert_anonymized(self, person: Person):
        self.assertTrue(person.private)
        self.assertIsNone(person.individual_name)
        self.assertIsNone(person.family_name)
        self.assertCountEqual([], person.events)
        self.assertCountEqual([], person.documents)

    def assert_not_anonymized(self, person: Person):
        self.assertIsNone(person.individual_name)
        self.assertIsNone(person.family_name)
        self.assertNotEqual([], sorted(person.events))
        self.assertNotEqual([], sorted(person.documents))

    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = {}
            with Site(configuration) as site:
                with NamedTemporaryFile() as document_f:
                    person = Person('P0')
                    person.events.add(Event('E0', Event.Type.BIRTH))
                    person.documents.add(Document('D0', document_f.name))
                    site.ancestry.people[person.id] = person
                    parse(site)
                    self.assert_anonymized(person)

    def test_anonymize_should_anonymize_if_age_unknown_without_descendants(self):
        with NamedTemporaryFile() as f:
            person = Person('P0')
            person.events.add(Event('E0', Event.Type.BIRTH))
            person.documents.add(Document('D0', f.name))
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_anonymized(person)

    def test_anonymize_should_not_anonymize_if_age_over_threshold(self):
        with NamedTemporaryFile() as document_f:
            person = Person('P0)')
            birth = Event('E0', Event.Type.BIRTH)
            birth.date = Date(1234, 5, 6)
            person.events.add(birth)
            person.documents.add(Document('D0', document_f.name))
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_not_anonymized(person)

    def test_anonymize_should_anonymize_if_age_unknown_with_descendants_of_unknown_age(self):
        with NamedTemporaryFile() as document_f:
            person = Person('P0')
            person.events.add(Event('E0', Event.Type.BIRTH))
            person.documents.add(Document('D0', document_f.name))
            descendant = Person('P1')
            person.children.add(descendant)
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_anonymized(person)

    def test_anonymize_should_not_anonymize_if_age_unknown_with_descendants_over_age_threshold(self):
        with NamedTemporaryFile() as document_f:
            person = Person('P0')
            person.events.add(Event('E0', Event.Type.BIRTH))
            person.documents.add(Document('D0', document_f.name))
            descendant = Person('P1')
            descendant_birth = Event('E1', Event.Type.BIRTH)
            descendant_birth.date = Date(1234, 5, 6)
            descendant.events.add(descendant_birth)
            person.children.add(descendant)
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_not_anonymized(person)

    def test_anonymize_should_not_anonymize_if_dead(self):
        with NamedTemporaryFile() as document_f:
            person = Person('P0')
            person.events.add(Event('E0', Event.Type.DEATH))
            person.documents.add(Document('D0', document_f.name))
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_not_anonymized(person)
