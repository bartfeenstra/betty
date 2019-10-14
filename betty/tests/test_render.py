from os import makedirs, path
from os.path import join, exists
from tempfile import TemporaryDirectory
from unittest import TestCase

import html5lib
from lxml import etree

from betty.ancestry import Person, Event, Place, Source, Presence
from betty.config import Configuration
from betty.render import render
from betty.site import Site


class RenderTestCase(TestCase):
    def setUp(self):
        self._outputDirectory = TemporaryDirectory()
        self.site = None

    def tearDown(self):
        self._outputDirectory.cleanup()

    def assert_page(self, path: str) -> str:
        file_path = join(
            self.site.configuration.www_directory_path, path.lstrip('/'))
        self.assertTrue(exists(file_path), '%s does not exist' % file_path)
        with open(file_path) as f:
            parser = html5lib.HTMLParser(strict=True)
            parser.parse(f)
        return file_path


class RenderTest(RenderTestCase):
    _outputDirectory = None
    site = None

    @classmethod
    def setUpClass(cls):
        cls._outputDirectory = TemporaryDirectory()
        configuration = Configuration(
            cls._outputDirectory.name, 'https://ancestry.example.com')
        cls.site = Site(configuration)

        place1 = Place('PLACE1', 'one')

        event1 = Event('EVENT1', Event.Type.BIRTH)
        event1.place = place1

        event1_person_1_presence = Presence(Presence.Role.SUBJECT)
        event1_person_1_presence.event = event1

        person1 = Person('PERSON1', 'Janet', 'Dough')
        person1.presences.add(event1_person_1_presence)

        source1 = Source('SOURCE1', 'A Little Birdie')

        places = [place1]
        cls.site.ancestry.places.update({place.id: place for place in places})
        events = [event1]
        cls.site.ancestry.events.update({event.id: event for event in events})
        people = [person1]
        cls.site.ancestry.people.update(
            {person.id: person for person in people})
        sources = [source1]
        cls.site.ancestry.sources.update(
            {source.id: source for source in sources})

        render(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._outputDirectory.cleanup()

    def assert_page(self, path: str):
        abspath = join(self.site.configuration.www_directory_path,
                       path.lstrip('/'), 'index.html')
        self.assertTrue(exists(abspath), '%s does not exist' % abspath)
        with open(abspath) as f:
            parser = html5lib.HTMLParser(strict=True)
            parser.parse(f)

    def test_front_page(self):
        self.assert_page('/')

    def test_places(self):
        self.assert_page('/place/')

    def test_place(self):
        place = self.site.ancestry.places['PLACE1']
        self.assert_page('/place/%s' % place.id)

    def test_people(self):
        self.assert_page('/person/')

    def test_person(self):
        person = self.site.ancestry.people['PERSON1']
        self.assert_page('/person/%s' % person.id)

    def test_events(self):
        self.assert_page('/event/')

    def test_event(self):
        event = self.site.ancestry.events['EVENT1']
        self.assert_page('/event/%s' % event.id)

    def test_sources(self):
        self.assert_page('/source/')

    def test_source(self):
        source = self.site.ancestry.sources['SOURCE1']
        self.assert_page('/source/%s' % source.id)

    def test_resource_override(self):
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as resources_directory_path:
                makedirs(join(resources_directory_path, 'public'))
                with open(join(resources_directory_path, 'public', 'index.html.j2'), 'w') as f:
                    f.write('{% block content %}Betty was here{% endblock %}')
                configuration = Configuration(
                    output_directory_path, 'https://ancestry.example.com')
                configuration.resources_directory_path = resources_directory_path
                site = Site(configuration)
                render(site)
                with open(join(configuration.www_directory_path, 'index.html')) as f:
                    self.assertIn('Betty was here', f.read())


class SitemapRenderTest(RenderTestCase):
    def setUp(self):
        RenderTestCase.setUp(self)
        configuration = Configuration(
            self._outputDirectory.name, 'https://ancestry.example.com')
        self.site = Site(configuration)

    def test_validate(self):

        render(self.site)
        with open(path.join(path.dirname(__file__), 'resources', 'sitemap.xsd')) as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        with open(path.join(self.site.configuration.www_directory_path, 'sitemap.xml')) as f:
            sitemap_doc = etree.parse(f)
        schema.validate(sitemap_doc)
