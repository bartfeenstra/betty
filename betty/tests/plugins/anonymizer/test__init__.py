from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, File, Presence
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.anonymizer import Anonymizer, anonymize, anonymize_person
from betty.site import Site


class AnonymizerTestCase(TestCase):
    def assert_anonymized(self, person: Person):
        self.assertIsNone(person.name)
        self.assertIsNone(person.alternative_names)
        self.assertCountEqual([], person.presences)
        self.assertCountEqual([], person.files)

    def assert_not_anonymized(self, person: Person):
        self.assertIsNotNone(person.name)
        self.assertGreater(0, len(person.alternative_names))
        self.assertNotEqual([], sorted(person.presences))
        self.assertNotEqual([], sorted(person.files))


class AnonymizeTest(AnonymizerTestCase):
    def test_anonymize_should_anonymize_private_person(self):
        with NamedTemporaryFile() as file_f:
            person = Person('P0')
            person.private = True
            partner = Person('P1')
            person_presence = Presence(Presence.Role.SUBJECT)
            person_presence.person = person
            partner_presence = Presence(Presence.Role.SUBJECT)
            partner_presence.person = partner
            event = Event('E0', Event.Type.MARRIAGE)
            event.presences = [person_presence, partner_presence]
            file = File('D0', file_f.name)
            file.entities.add(person, partner)
            ancestry = Ancestry()
            ancestry.people[person.id] = person
            anonymize(ancestry)
            self.assert_anonymized(person)
            self.assertCountEqual([], event.presences)
            self.assertCountEqual([], file.entities)

    def test_anonymize_should_not_anonymize_public_person(self):
        with NamedTemporaryFile() as file_f:
            person = Person('P0')
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = Event('E0', Event.Type.BIRTH)
            person.presences.add(presence)
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


class AnonymizePersonTest(AnonymizerTestCase):
    def test_anonymize_person_should_anonymize_parents_if_private_without_public_descendants(self):
        person = Person('P0')
        person.private = True
        child = Person('P1')
        child.private = True
        person.children.add(child)
        parent = Person('P2')
        parent.private = True
        person.parents.add(parent)

        anonymize_person(person)
        self.assertCountEqual([], person.parents)

    def test_anonymize_person_should_anonymize_parents_if_private_with_public_descendants(self):
        person = Person('P0')
        person.private = True
        child = Person('P1')
        child.private = False
        person.children.add(child)
        parent = Person('P2')
        parent.private = True
        person.parents.add(parent)

        anonymize_person(person)
        self.assertCountEqual([parent], person.parents)

    def test_anonymize_person_should_anonymize_parents_if_public_without_public_descendants(self):
        person = Person('P0')
        person.private = False
        child = Person('P1')
        child.private = True
        person.children.add(child)
        parent = Person('P2')
        parent.private = True
        person.parents.add(parent)

        anonymize_person(person)
        self.assertCountEqual([parent], person.parents)

    def test_anonymize_person_should_anonymize_parents_if_public_with_public_descendants(self):
        person = Person('P0')
        person.private = False
        child = Person('P1')
        child.private = False
        person.children.add(child)
        parent = Person('P2')
        parent.private = True
        person.parents.add(parent)

        anonymize_person(person)
        self.assertCountEqual([parent], person.parents)


class AnonymizerTest(AnonymizerTestCase):
    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Anonymizer] = {}
            site = Site(configuration)
            with NamedTemporaryFile() as file_f:
                person = Person('P0')
                person.private = True
                presence = Presence(Presence.Role.SUBJECT)
                presence.event = Event('E0', Event.Type.BIRTH)
                person.presences.add(presence)
                person.files.add(File('D0', file_f.name))
                site.ancestry.people[person.id] = person
                parse(site)
                self.assert_anonymized(person)
