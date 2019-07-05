from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, File
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.anonymizer import Anonymizer, anonymize
from betty.site import Site


class AnonymizerTestCase(TestCase):
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


class AnonymizeTest(AnonymizerTestCase):
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
            anonymize(ancestry)
            self.assert_anonymized(person)
            self.assertCountEqual([], event.people)
            self.assertCountEqual([], file.entities)

    def test_anonymize_should_not_anonymize_public_person(self):
        with NamedTemporaryFile() as file_f:
            person = Person('P0', 'Janet', 'Dough')
            person.events.add(Event('E0', Event.Type.BIRTH))
            person.files.add(File('D0', file_f.name))
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            anonymize(ancestry)
            self.assert_not_anonymized(person)

    def test_anonymize_should_anonymize_people_without_public_descendants(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = True
        ancestry.people[person.id] = person
        child = Person('P1')
        child.private = True
        person.children.add(child)
        ancestry.people[child.id] = child
        grandchild = Person('P2')
        grandchild.private = True
        child.children.add(grandchild)
        ancestry.people[grandchild.id] = grandchild
        great_grandchild = Person('P3')
        great_grandchild.private = True
        grandchild.children.add(great_grandchild)
        ancestry.people[great_grandchild.id] = great_grandchild

        anonymize(ancestry)
        self.assertCountEqual([], person.children)
        self.assertCountEqual([], child.children)
        self.assertCountEqual([], grandchild.children)

    def test_anonymize_should_not_anonymize_people_with_public_descendants(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = True
        ancestry.people[person.id] = person
        child = Person('P1')
        child.private = True
        person.children.add(child)
        ancestry.people[child.id] = child
        grandchild = Person('P2')
        grandchild.private = True
        child.children.add(grandchild)
        ancestry.people[grandchild.id] = grandchild
        great_grandchild = Person('P3')
        great_grandchild.private = False
        grandchild.children.add(great_grandchild)
        ancestry.people[great_grandchild.id] = great_grandchild

        anonymize(ancestry)
        self.assertCountEqual([child], person.children)
        self.assertCountEqual([grandchild], child.children)
        self.assertCountEqual([great_grandchild], grandchild.children)


class AnonymizerTest(AnonymizerTestCase):
    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = {}
            site = Site(configuration)
            with NamedTemporaryFile() as file_f:
                person = Person('P0', 'Janet', 'Dough')
                person.private = True
                person.events.add(Event('E0', Event.Type.BIRTH))
                person.files.add(File('D0', file_f.name))
                site.ancestry.people[person.id] = person
                parse(site)
                self.assert_anonymized(person)
