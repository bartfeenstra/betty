from os.path import join, dirname, abspath
from unittest import TestCase

from betty.ancestry import Ancestry, Event
from betty.gramps import parse


class GrampsTestCase(TestCase):
    @property
    def ancestry(self) -> Ancestry:
        if not hasattr(self, '_ancestry'):
            self._ancestry = parse(
                join(dirname(abspath(__file__)), 'resources', 'data.xml'))
        return self._ancestry


class ParsePlaceTest(GrampsTestCase):
    def test_place_should_include_name(self):
        place = self.ancestry.places['P0000']
        self.assertEquals('Amsterdam', place.label)

    def test_place_should_include_coordinates(self):
        place = self.ancestry.places['P0000']
        self.assertAlmostEquals(52.366667, place.coordinates.latitude)
        self.assertAlmostEquals(4.9, place.coordinates.longitude)

    def test_place_should_include_events(self):
        place = self.ancestry.places['P0000']
        event = self.ancestry.events['E0000']
        self.assertIn(event, place.events)


class ParsePersonTest(GrampsTestCase):
    def test_person_should_include_individual_name(self):
        person = self.ancestry.people['I0000']
        self.assertEquals('Jane', person.individual_name)
        self.assertEquals('Doe', person.family_name)

    def test_person_should_include_birth(self):
        person = self.ancestry.people['I0000']
        self.assertEquals('E0000', person.birth.id)

    def test_person_should_include_death(self):
        person = self.ancestry.people['I0003']
        self.assertEquals('E0002', person.death.id)


class ParseFamilyTest(GrampsTestCase):
    def test_family_should_include_parents(self):
        family = self.ancestry.families['F0000']
        expected_parents = [self.ancestry.people['I0002'], self.ancestry.people['I0003']]
        self.assertCountEqual(expected_parents, family.parents)

    def test_family_should_include_children(self):
        family = self.ancestry.families['F0000']
        expected_children = [self.ancestry.people['I0000'], self.ancestry.people['I0001']]
        self.assertCountEqual(expected_children, family.children)


class ParseEventTest(GrampsTestCase):
    def test_event_should_be_birth(self):
        self.assertEquals(Event.Type.BIRTH, self.ancestry.events['E0000'].type)

    def test_event_should_be_death(self):
        self.assertEquals(Event.Type.DEATH, self.ancestry.events['E0002'].type)

    def test_event_should_include_place(self):
        event = self.ancestry.events['E0000']
        place = self.ancestry.places['P0000']
        self.assertEquals(place, event.place)

    def test_event_should_include_date(self):
        event = self.ancestry.events['E0000']
        self.assertEquals(1970, event.date.year)
        self.assertEquals(1, event.date.month)
        self.assertEquals(1, event.date.day)

    def test_event_should_include_people(self):
        event = self.ancestry.events['E0000']
        expected_people = [self.ancestry.people['I0000']]
        self.assertCountEqual(expected_people, event.people)
