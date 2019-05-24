from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, File
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.anonymizer import Anonymizer
from betty.site import Site


class AnonymizerTest(TestCase):
    def assert_anonymized(self, person: Person):
        self.assertIsNone(person.individual_name)
        self.assertIsNone(person.family_name)
        self.assertCountEqual([], person.events)
        self.assertCountEqual([], person.files)

    def assert_not_anonymized(self, person: Person):
        self.assertIsNotNone(person.individual_name)
        self.assertIsNotNone(person.family_name)
        self.assertNotEqual([], sorted(person.events))
        self.assertNotEqual([], sorted(person.files))

    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = {}
            with Site(configuration) as site:
                with NamedTemporaryFile() as file_f:
                    person = Person('P0', 'Janet', 'Dough')
                    person.private = True
                    person.events.add(Event('E0', Event.Type.BIRTH))
                    person.files.add(File('D0', file_f.name))
                    site.ancestry.people[person.id] = person
                    parse(site)
                    self.assert_anonymized(person)

    def test_anonymize_should_anonymize_private_person(self):
        with NamedTemporaryFile() as file_f:
            person = Person('P0', 'Janet', 'Dough')
            person.private = True
            partner = Person('P1', 'Jenny', 'Donut')
            event = Event('E0', Event.Type.MARRIAGE)
            event.people.add(person, partner)
            file = File('D0', file_f.name)
            file.entities.add(person, partner)
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_anonymized(person)
            self.assertCountEqual([], event.people)
            self.assertCountEqual([], file.entities)

    def test_anonymize_should_not_anonymize_non_private_person(self):
        with NamedTemporaryFile() as file_f:
            person = Person('P0', 'Janet', 'Dough')
            person.events.add(Event('E0', Event.Type.BIRTH))
            person.files.add(File('D0', file_f.name))
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            sut = Anonymizer()
            sut.anonymize(ancestry)
            self.assert_not_anonymized(person)
