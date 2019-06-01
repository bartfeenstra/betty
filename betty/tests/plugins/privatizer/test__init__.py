from tempfile import TemporaryDirectory
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Ancestry, Person, Event, Date
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.privatizer import Privatizer
from betty.site import Site


class PrivatizerTest(TestCase):
    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Privatizer] = {}
            with Site(configuration) as site:
                person = Person('P0')
                person.events.add(Event('E0', Event.Type.BIRTH))
                site.ancestry.people[person.id] = person
                parse(site)
                self.assertTrue(person.private)

    @parameterized.expand([
        (True, None),
        (True, True),
        (False, False),
    ])
    def test_privatize_should_privatize_if_age_unknown_without_descendants(self, expected, private):
        person = Person('P0', 'Janet', 'Dough')
        person.private = private
        person.events.add(Event('E0', Event.Type.BIRTH))
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    def test_privatize_should_not_privatize_if_age_over_threshold(self):
        person = Person('P0', 'Janet', 'Dough')
        birth = Event('E0', Event.Type.BIRTH)
        birth.date = Date(1234, 5, 6)
        person.events.add(birth)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertFalse(person.private)

    def test_privatize_should_privatize_if_age_unknown_with_descendants_of_unknown_age(self, expected):
        person = Person('P0', 'Janet', 'Dough')
        person.events.add(Event('E0', Event.Type.BIRTH))
        child = Person('P1')
        child.events.add(Event('E1', Event.Type.BIRTH))
        person.children.add(child)
        grandchild = Person('P1')
        grandchild.events.add(Event('E2', Event.Type.BIRTH))
        child.children.add(grandchild)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    def test_privatize_should_not_privatize_if_age_unknown_with_child_over_age_threshold(self):
        person = Person('P0', 'Janet', 'Dough')
        person.events.add(Event('E0', Event.Type.BIRTH))
        child = Person('P1')
        child_birth = Event('E1', Event.Type.BIRTH)
        child_birth.date = Date(1234, 5, 6)
        child.events.add(child_birth)
        person.children.add(child)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertFalse(person.private)

    def test_privatize_should_not_privatize_if_age_unknown_with_grandchild_over_age_threshold(self):
        person = Person('P0', 'Janet', 'Dough')
        person.events.add(Event('E0', Event.Type.BIRTH))
        child = Person('P1')
        person.children.add(child)
        grandchild = Person('P1')
        grandchild_birth = Event('E1', Event.Type.BIRTH)
        grandchild_birth.date = Date(1234, 5, 6)
        grandchild.events.add(grandchild_birth)
        child.children.add(grandchild)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertFalse(person.private)

    def test_privatize_should_not_privatize_if_age_unknown_with_parent_death_over_age_threshold(self):
        person = Person('P0', 'Janet', 'Dough')
        person.events.add(Event('E0', Event.Type.BIRTH))
        parent = Person('P1')
        parent_death = Event('E1', Event.Type.DEATH)
        parent_death.date = Date(1234, 5, 6)
        parent.events.add(parent_death)
        person.parents.add(parent)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertFalse(person.private)

    def test_privatize_should_not_privatize_if_age_unknown_with_grandparent_death_over_age_threshold(self):
        person = Person('P0', 'Janet', 'Dough')
        person.events.add(Event('E0', Event.Type.BIRTH))
        parent = Person('P1')
        person.parents.add(parent)
        grandparent = Person('P2')
        grandparent_death = Event('E1', Event.Type.DEATH)
        grandparent_death.date = Date(1234, 5, 6)
        grandparent.events.add(grandparent_death)
        parent.parents.add(grandparent)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertFalse(person.private)

    def test_privatize_should_not_privatize_if_dead(self):
        person = Person('P0', 'Janet', 'Dough')
        person.events.add(Event('E0', Event.Type.DEATH))
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertFalse(person.private)
