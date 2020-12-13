from os.path import join, dirname, abspath
from tempfile import TemporaryDirectory
from typing import Optional

from parameterized import parameterized

from betty.ancestry import Ancestry, PersonName, Birth, Death, UnknownEventType
from betty.config import Configuration
from betty.asyncio import sync
from betty.locale import Date
from betty.parse import parse
from betty.path import rootname
from betty.plugin.gramps import parse_xml, Gramps, parse_gpkg, parse_gramps
from betty.site import Site
from betty.tests import TestCase


class ParseGrampsTest(TestCase):
    pass


class ParseGpkgTest(TestCase):
    pass


class ParseXmlTest(TestCase):
    @classmethod
    @sync
    async def setUpClass(cls) -> None:
        TestCase.setUpClass()
        # @todo Convert each test method to use self._parse(), so we can remove this shared XML file.
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with Site(configuration) as site:
                cls.ancestry = site.ancestry
                xml_file_path = join(dirname(abspath(__file__)), 'assets', 'data.xml')
                with open(xml_file_path) as f:
                    parse_xml(site, f.read(), rootname(xml_file_path))

    @sync
    async def _parse(self, xml: str) -> Ancestry:
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with Site(configuration) as site:
                with TemporaryDirectory() as tree_directory_path:
                    parse_xml(site, xml.strip(), tree_directory_path)
                    return site.ancestry

    def _parse_partial(self, xml: str) -> Ancestry:
        return self._parse("""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
  <header>
    <created date="2019-03-09" version="4.2.8"/>
    <researcher>
    </researcher>
  </header>
  %s
</database>
""" % xml)

    @sync
    async def test_parse_xml_with_string(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with Site(configuration) as site:
                gramps_file_path = join(dirname(abspath(__file__)), 'assets', 'minimal.xml')
                with open(gramps_file_path) as f:
                    parse_xml(site, f.read(), rootname(gramps_file_path))

    @sync
    async def test_parse_xml_with_file_path(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with Site(configuration) as site:
                gramps_file_path = join(dirname(abspath(__file__)), 'assets', 'minimal.xml')
                parse_xml(site, gramps_file_path, rootname(gramps_file_path))

    @sync
    async def test_parse_gramps(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with Site(configuration) as site:
                gramps_file_path = join(dirname(abspath(__file__)), 'assets', 'minimal.gramps')
                parse_gramps(site, gramps_file_path)

    @sync
    async def test_parse_gpkg(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with Site(configuration) as site:
                gramps_file_path = join(dirname(abspath(__file__)), 'assets', 'minimal.gpkg')
                parse_gpkg(site, gramps_file_path)

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
        self.assertIsInstance(self.ancestry.events['E0000'].type, Birth)

    def test_event_should_be_death(self):
        self.assertIsInstance(self.ancestry.events['E0002'].type, Death)

    def test_event_should_parse_unknown(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>SomeEventThatIUsedToKnow</type>
        <dateval val="0000-00-00" quality="calculated"/>
    </event>
</events>
""")
        self.assertIsInstance(ancestry.events['E0000'].type, UnknownEventType)

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

    def test_event_should_include_description(self):
        event = self.ancestry.events['E0008']
        self.assertEquals('Something happened!', event.description)

    @parameterized.expand([
        (Date(), '0000-00-00'),
        (Date(None, None, 1), '0000-00-01'),
        (Date(None, 1), '0000-01-00'),
        (Date(None, 1, 1), '0000-01-01'),
        (Date(1970), '1970-00-00'),
        (Date(1970, None, 1), '1970-00-01'),
        (Date(1970, 1), '1970-01-00'),
        (Date(1970, 1, 1), '1970-01-01'),
    ])
    def test_date_should_parse_parts(self, expected: Date, dateval_val: str):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="%s" quality="calculated"/>
    </event>
</events>
""" % dateval_val)
        self.assertEquals(expected, ancestry.events['E0000'].date)

    def test_date_should_ignore_calendar_format(self):
        self.assertIsNone(self.ancestry.events['E0005'].date)

    def test_date_should_parse_before(self):
        date = self.ancestry.events['E0003'].date
        self.assertIsNone(date.start)
        self.assertEquals(1970, date.end.year)
        self.assertEquals(1, date.end.month)
        self.assertEquals(1, date.end.day)
        self.assertTrue(date.end_is_boundary)
        self.assertFalse(date.end.fuzzy)

    def test_date_should_parse_after(self):
        date = self.ancestry.events['E0004'].date
        self.assertIsNone(date.end)
        self.assertEquals(1970, date.start.year)
        self.assertEquals(1, date.start.month)
        self.assertEquals(1, date.start.day)
        self.assertTrue(date.start_is_boundary)
        self.assertFalse(date.start.fuzzy)

    def test_date_should_parse_calculated(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" quality="calculated"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertEquals(1970, date.year)
        self.assertEquals(1, date.month)
        self.assertEquals(1, date.day)
        self.assertFalse(date.fuzzy)

    def test_date_should_parse_estimated(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" quality="estimated"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertEquals(1970, date.year)
        self.assertEquals(1, date.month)
        self.assertEquals(1, date.day)
        self.assertTrue(date.fuzzy)

    def test_date_should_parse_about(self):
        date = self.ancestry.events['E0007'].date
        self.assertEquals(1970, date.year)
        self.assertEquals(1, date.month)
        self.assertEquals(1, date.day)
        self.assertTrue(date.fuzzy)

    def test_daterange_should_parse(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertEquals(1970, date.start.year)
        self.assertEquals(1, date.start.month)
        self.assertEquals(1, date.start.day)
        self.assertFalse(date.start.fuzzy)
        self.assertTrue(date.start_is_boundary)
        self.assertEquals(1999, date.end.year)
        self.assertEquals(12, date.end.month)
        self.assertEquals(31, date.end.day)
        self.assertTrue(date.end_is_boundary)
        self.assertFalse(date.end.fuzzy)

    def test_daterange_should_parse_calculated(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31" quality="calculated"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertFalse(date.start.fuzzy)
        self.assertFalse(date.end.fuzzy)

    def test_daterange_should_parse_estimated(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31" quality="estimated"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertTrue(date.start.fuzzy)
        self.assertTrue(date.end.fuzzy)

    def test_datespan_should_parse(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertEquals(1970, date.start.year)
        self.assertEquals(1, date.start.month)
        self.assertEquals(1, date.start.day)
        self.assertFalse(date.start.fuzzy)
        self.assertEquals(1999, date.end.year)
        self.assertEquals(12, date.end.month)
        self.assertEquals(31, date.end.day)
        self.assertFalse(date.end.fuzzy)

    def test_datespan_should_parse_calculated(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31" quality="calculated"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertFalse(date.start.fuzzy)
        self.assertFalse(date.end.fuzzy)

    def test_datespan_should_parse_estimated(self):
        ancestry = self._parse_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31" quality="estimated"/>
    </event>
</events>
""")
        date = ancestry.events['E0000'].date
        self.assertTrue(date.start.fuzzy)
        self.assertTrue(date.end.fuzzy)

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

    def test_source_from_source_should_include_author(self):
        source = self.ancestry.sources['S0000']
        self.assertEquals('A Little Birdie', source.author)

    def test_source_from_source_should_include_publisher(self):
        source = self.ancestry.sources['S0000']
        self.assertEquals('Somewhere over the rainbow', source.publisher)

    def test_source_from_source_should_include_repository(self):
        source = self.ancestry.sources['S0000']
        containing_source = self.ancestry.sources['R0000']
        self.assertEquals(containing_source, source.contained_by)

    @parameterized.expand([
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_person_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._parse_partial("""
<people>
    <person handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="I0000">
        <gender>U</gender>
        <attribute type="betty:privacy" value="%s"/>
    </person>
</people>
""" % attribute_value)
        person = ancestry.people['I0000']
        self.assertEquals(expected, person.private)

    @parameterized.expand([
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_event_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._parse_partial("""
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
        <attribute type="betty:privacy" value="%s"/>
    </event>
</events>
""" % attribute_value)
        event = ancestry.events['E0000']
        self.assertEquals(expected, event.private)

    @parameterized.expand([
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_file_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._parse_partial("""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:privacy" value="%s"/>
    </object>
</objects>
""" % attribute_value)
        file = ancestry.files['O0000']
        self.assertEquals(expected, file.private)

    @parameterized.expand([
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_source_from_source_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._parse_partial("""
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
        <srcattribute type="betty:privacy" value="%s"/>
    </source>
</sources>
""" % attribute_value)
        source = ancestry.sources['S0000']
        self.assertEquals(expected, source.private)

    @parameterized.expand([
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_citation_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._parse_partial("""
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000">
        <confidence>2</confidence>
        <sourceref hlink="_e1dd686b04813540eb3503a342b"/>
        <srcattribute type="betty:privacy" value="%s"/>
    </citation>
</citations>
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
    </source>
</sources>
""" % attribute_value)
        citation = ancestry.citations['C0000']
        self.assertEquals(expected, citation.private)


class GrampsTest(TestCase):
    @sync
    async def test_parse_event(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Gramps] = {
                'file': join(dirname(abspath(__file__)), 'assets', 'minimal.gpkg')
            }
            async with Site(configuration) as site:
                await parse(site)
            self.assertEquals(
                'Dough', site.ancestry.people['I0000'].name.affiliation)
            self.assertEquals(
                'Janet', site.ancestry.people['I0000'].name.individual)
            self.assertEquals(
                '1px', site.ancestry.files['O0000'].description)
