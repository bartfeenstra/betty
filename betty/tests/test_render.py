from os import makedirs, path
from os.path import join, exists
from tempfile import TemporaryDirectory
from unittest import TestCase

import html5lib
from lxml import etree

from betty.ancestry import Person, Event, Place, Source, LocalizedName
from betty.config import Configuration, LocaleConfiguration
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
    def setUp(self):
        RenderTestCase.setUp(self)
        configuration = Configuration(
            self._outputDirectory.name, 'https://ancestry.example.com')
        self.site = Site(configuration)

    def test_front_page(self):
        render(self.site)
        self.assert_page('/index.html')

    def test_places(self):
        render(self.site)
        self.assert_page('/place/index.html')

    def test_place(self):
        place = Place('PLACE1', [LocalizedName('one')])
        self.site.ancestry.places[place.id] = place
        render(self.site)
        self.assert_page('/place/%s/index.html' % place.id)

    def test_people(self):
        render(self.site)
        self.assert_page('/person/index.html')

    def test_person(self):
        person = Person('PERSON1', 'Janet', 'Dough')
        self.site.ancestry.people[person.id] = person
        render(self.site)
        self.assert_page('/person/%s/index.html' % person.id)

    def test_events(self):
        render(self.site)
        self.assert_page('/event/index.html')

    def test_event(self):
        event = Event('EVENT1', Event.Type.BIRTH)
        self.site.ancestry.events[event.id] = event
        render(self.site)
        self.assert_page('/event/%s/index.html' % event.id)

    def test_sources(self):
        render(self.site)
        self.assert_page('/source/index.html')

    def test_source(self):
        source = Source('SOURCE1', 'A Little Birdie')
        self.site.ancestry.sources[source.id] = source
        render(self.site)
        self.assert_page('/source/%s/index.html' % source.id)


class MultilingualTest(RenderTestCase):
    def setUp(self):
        RenderTestCase.setUp(self)
        configuration = Configuration(
            self._outputDirectory.name, 'https://ancestry.example.com')
        configuration.locales.clear()
        configuration.locales['nl'] = LocaleConfiguration('nl')
        configuration.locales['en'] = LocaleConfiguration('en')
        self.site = Site(configuration)

    def test_root_redirect(self):
        render(self.site)
        with open(self.assert_page('/index.html')) as f:
            meta_redirect = '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            self.assertIn(meta_redirect, f.read())

    def test_public_localized_resource(self):
        render(self.site)
        with open(self.assert_page('/nl/index.html')) as f:
            translation_link = '<a href="/en/index.html" hreflang="en" lang="en" rel="alternate">English</a>'
            self.assertIn(translation_link, f.read())
        with open(self.assert_page('/en/index.html')) as f:
            translation_link = '<a href="/nl/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>'
            self.assertIn(translation_link, f.read())

    def test_entity(self):
        person = Person('PERSON1')
        self.site.ancestry.people[person.id] = person
        render(self.site)
        with open(self.assert_page('/nl/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/en/person/%s/index.html" hreflang="en" lang="en" rel="alternate">English</a>' % person.id
            self.assertIn(translation_link, f.read())
        with open(self.assert_page('/en/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/nl/person/%s/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>' % person.id
            self.assertIn(translation_link, f.read())


class ResourceOverrideTest(RenderTestCase):
    def test(self):
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as resources_directory_path:
                makedirs(join(resources_directory_path, 'public', 'localized'))
                with open(join(resources_directory_path, 'public', 'localized', 'index.html.j2'), 'w') as f:
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
