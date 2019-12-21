from os.path import join, dirname, abspath
from tempfile import TemporaryDirectory
from unittest import TestCase

from lxml import etree
from lxml.etree import XMLParser

from betty.ancestry import Event, Ancestry, PersonName
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.gramps import extract_xml_file, parse_xml_file, Gramps
from betty.site import Site


class ExtractXmlFileTest(TestCase):
    def test_gramps_xml(self):
        with TemporaryDirectory() as cache_directory_path:
            gramps_file_path = join(
                dirname(abspath(__file__)), 'resources', 'minimal.gramps')
            xml_file_path = extract_xml_file(
                gramps_file_path, cache_directory_path)
            with open(xml_file_path) as f:
                parser = XMLParser()
                etree.parse(f, parser)

    def test_portable_gramps_xml_package(self):
        with TemporaryDirectory() as cache_directory_path:
            gramps_file_path = join(
                dirname(abspath(__file__)), 'resources', 'minimal.gpkg')
            xml_file_path = extract_xml_file(
                gramps_file_path, cache_directory_path)
            with open(xml_file_path) as f:
                parser = XMLParser()
                etree.parse(f, parser)


class ParseXmlFileTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ancestry = Ancestry()
        parse_xml_file(cls.ancestry, join(
            dirname(abspath(__file__)), 'resources', 'data.xml'))

    def test_place_should_include_name(self):
        place = self.ancestry.places['P0000']
        names = place.names
        self.assertEquals(1, len(names))
        name = names[0]
        self.assertEquals('Amsterdam', name.name)

    def test_place_should_include_coordinates(self):
        place = self.ancestry.places['P0000']
        self.assertAlmostEquals(52.366667, place.coordinates.latitude)
        self.assertAlmostEquals(4.9, place.coordinates.longitude)

    def test_place_should_include_events(self):
        place = self.ancestry.places['P0000']
        event = self.ancestry.events['E0000']
        self.assertIn(event, place.events)

    def test_person_should_include_name(self):
        person = self.ancestry.people['I0000']
        expected = PersonName('Jane', 'Doe')
        self.assertEquals(expected, person.name)

    def test_person_should_include_alternative_names(self):
        person = self.ancestry.people['I0000']
        expected = [
            PersonName('Jane', 'Doh'),
            PersonName('Jen', 'Van Doughie'),
        ]
        self.assertEquals(expected, person.alternative_names)

    def test_person_should_include_birth(self):
        person = self.ancestry.people['I0000']
        self.assertEquals('E0000', person.start.id)

    def test_person_should_include_death(self):
        person = self.ancestry.people['I0003']
        self.assertEquals('E0002', person.end.id)

    def test_person_should_be_private(self):
        person = self.ancestry.people['I0003']
        self.assertTrue(person.private)

    def test_person_should_not_be_private(self):
        person = self.ancestry.people['I0002']
        self.assertFalse(person.private)

    def test_person_should_include_citation(self):
        person = self.ancestry.people['I0000']
        citation = self.ancestry.citations['C0000']
        self.assertIn(citation, person.citations)

    def test_family_should_set_parents(self):
        expected_parents = [self.ancestry.people['I0002'],
                            self.ancestry.people['I0003']]
        children = [self.ancestry.people['I0000'],
                    self.ancestry.people['I0001']]
        for child in children:
            self.assertCountEqual(expected_parents, child.parents)

    def test_family_should_set_children(self):
        parents = [self.ancestry.people['I0002'],
                   self.ancestry.people['I0003']]
        expected_children = [self.ancestry.people['I0000'],
                             self.ancestry.people['I0001']]
        for parent in parents:
            self.assertCountEqual(expected_children, parent.children)

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
        self.assertCountEqual(
            expected_people, [presence.person for presence in event.presences])

    def test_date_should_ignore_invalid_date(self):
        date = self.ancestry.events['E0001'].date
        self.assertIsNone(date)

    def test_date_should_ignore_invalid_date_parts(self):
        date = self.ancestry.events['E0002'].date
        self.assertIsNone(date.year)
        self.assertEquals(12, date.month)
        self.assertEquals(31, date.day)

    def test_date_should_ignore_calendar_format(self):
        self.assertIsNone(self.ancestry.events['E0005'].date)

    def test_date_should_parse_range(self):
        date = self.ancestry.events['E0006'].date
        self.assertEquals(1970, date.start.year)
        self.assertEquals(1, date.start.month)
        self.assertEquals(1, date.start.day)
        self.assertEquals(1999, date.end.year)
        self.assertEquals(12, date.end.month)
        self.assertEquals(31, date.end.day)

    def test_date_should_parse_before(self):
        date = self.ancestry.events['E0003'].date
        self.assertIsNone(date.start)
        self.assertEquals(1970, date.end.year)
        self.assertEquals(1, date.end.month)
        self.assertEquals(1, date.end.day)

    def test_date_should_parse_after(self):
        date = self.ancestry.events['E0004'].date
        self.assertIsNone(date.end)
        self.assertEquals(1970, date.start.year)
        self.assertEquals(1, date.start.month)
        self.assertEquals(1, date.start.day)

    def test_source_from_repository_should_include_name(self):
        source = self.ancestry.sources['R0000']
        self.assertEquals('Library of Alexandria', source.name)

    def test_source_from_repository_should_include_link(self):
        links = self.ancestry.sources['R0000'].links
        self.assertEquals(1, len(links))
        link = list(links)[0]
        self.assertEquals('https://alexandria.example.com', link.url)
        self.assertEquals('Library of Alexandria Catalogue', link.label)

    def test_source_from_source_should_include_title(self):
        source = self.ancestry.sources['S0000']
        self.assertEquals('A Whisper', source.name)

    def test_source_from_source_should_include_repository(self):
        source = self.ancestry.sources['S0000']
        containing_source = self.ancestry.sources['R0000']
        self.assertEquals(containing_source, source.contained_by)


class GrampsTest(TestCase):
    def test_parse_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Gramps] = {
                'file': join(dirname(abspath(__file__)), 'resources', 'minimal.gpkg')
            }
            site = Site(configuration)
            parse(site)
            self.assertEquals(
                'Dough', site.ancestry.people['I0000'].name.affiliation)
            self.assertEquals(
                'Janet', site.ancestry.people['I0000'].name.individual)
            self.assertEquals(
                '1px', site.ancestry.files['O0000'].description)
