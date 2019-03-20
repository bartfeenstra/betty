from os.path import join, dirname, abspath
from unittest import TestCase

from betty.ancestry import Ancestry
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
        self.assertEquals(place.label, 'Amsterdam')

    def test_place_should_include_coordinates(self):
        place = self.ancestry.places['P0000']
        self.assertEquals(place.coordinates.latitude, '52.366667')
        self.assertEquals(place.coordinates.longitude, '4.9')


class ParsePersonTest(GrampsTestCase):
    def test_person_should_include_individual_name(self):
        person = self.ancestry.people['I0000']
        self.assertEquals(person.individual_name, 'Jane')
        self.assertEquals(person.family_name, 'Doe')

    def test_person_should_include_birth(self):
        person = self.ancestry.people['I0000']
        self.assertEquals(person.birth.id, 'E0000')

    def test_person_should_include_death(self):
        person = self.ancestry.people['I0003']
        self.assertEquals(person.death.id, 'E0002')


class ParseFamilyTest(GrampsTestCase):
    def test_family_should_include_parents(self):
        family = self.ancestry.families['F0000']
        actual_parent_ids = [parent.id for parent in family.parents]
        self.assertCountEqual(actual_parent_ids, ['I0002', 'I0003'])

    def test_family_should_include_children(self):
        family = self.ancestry.families['F0000']
        actual_child_ids = [parent.id for parent in family.children]
        self.assertCountEqual(actual_child_ids, ['I0000', 'I0001'])


class ParseEventTest(GrampsTestCase):
    def test_event_should_include_place(self):
        event = self.ancestry.events['E0000']
        self.assertEquals(event.place.id, 'P0000')

    def test_event_should_include_date(self):
        event = self.ancestry.events['E0000']
        self.assertEquals(event.date.year, 1970)
        self.assertEquals(event.date.month, 1)
        self.assertEquals(event.date.day, 1)

    def test_event_should_include_people(self):
        event = self.ancestry.events['E0000']
        self.assertEquals(list(event.people)[0].id, 'I0000')
