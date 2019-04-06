import gzip
from os.path import join, dirname, abspath
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Event
from betty.gramps import parse


class ExtractionTest(TestCase):
    def test_gramps_xml(self):
        with TemporaryDirectory() as working_directory_path:
            ancestry = parse(join(dirname(abspath(__file__)), 'resources', 'minimal.gramps'), working_directory_path)
            self.assertEquals('Dough', ancestry.people['I0000'].family_name)
            self.assertEquals('Janet', ancestry.people['I0000'].individual_name)

    def test_portable_gramps_xml_package(self):
        with TemporaryDirectory() as working_directory_path:
            ancestry = parse(join(dirname(abspath(__file__)), 'resources', 'minimal.gpkg'), working_directory_path)
            self.assertEquals('Dough', ancestry.people['I0000'].family_name)
            self.assertEquals('Janet', ancestry.people['I0000'].individual_name)
            self.assertEquals('1px', ancestry.documents['O0000'].description)


class GrampsTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Our main Gramps XML data is stored as an XML file, so edits are easier to track. Because that is not a native
        # Gramps format, we gzip it prior to using it in our Gramps API.
        cls.working_directory = TemporaryDirectory()
        with TemporaryDirectory() as gramps_working_directory_path:
            gramps_file_path = join(gramps_working_directory_path, 'data.gramps')
            with gzip.open(gramps_file_path, mode='w') as gramps_f:
                with open(join(dirname(abspath(__file__)), 'resources', 'data.xml'), mode='rb') as xml_f:
                    gramps_f.write(xml_f.read())
            cls.ancestry = parse(gramps_f.name, cls.working_directory.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.working_directory.cleanup()


class ParsePlaceTest(GrampsTestCase):
    def test_place_should_include_name(self):
        place = self.ancestry.places['P0000']
        self.assertEquals('Amsterdam', place.name)

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
    def test_family_should_set_parents(self):
        expected_parents = [self.ancestry.people['I0002'], self.ancestry.people['I0003']]
        children = [self.ancestry.people['I0000'], self.ancestry.people['I0001']]
        for child in children:
            self.assertCountEqual(expected_parents, child.parents)

    def test_family_should_set_children(self):
        parents = [self.ancestry.people['I0002'], self.ancestry.people['I0003']]
        expected_children = [self.ancestry.people['I0000'], self.ancestry.people['I0001']]
        for parent in parents:
            self.assertCountEqual(expected_children, parent.children)


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
