import json as stdjson
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile

import html5lib
from lxml import etree

from betty import json
from betty.ancestry import Person, Place, Source, PlaceName, File, IdentifiableEvent, IdentifiableCitation, \
    IdentifiableSource, Birth
from betty.config import Configuration, LocaleConfiguration
from betty.asyncio import sync
from betty.generate import generate
from betty.app import App
from betty.tests import TestCase


class GenerateTestCase(TestCase):
    def setUp(self):
        self._output_directory = TemporaryDirectory()
        self.app = None

    def tearDown(self):
        self._output_directory.cleanup()

    def assert_betty_html(self, url_path: str) -> Path:
        file_path = self.app.configuration.www_directory_path / Path(url_path.lstrip('/'))
        self.assertTrue(file_path.exists(), '%s does not exist' % file_path)
        with open(file_path) as f:
            parser = html5lib.HTMLParser(strict=True)
            parser.parse(f)
        return file_path

    def assert_betty_json(self, url_path: str, schema_definition: str) -> str:
        file_path = self.app.configuration.www_directory_path / Path(url_path.lstrip('/'))
        self.assertTrue(file_path.exists(), '%s does not exist' % file_path)
        with open(file_path) as f:
            json.validate(stdjson.load(f), schema_definition, self.app)
        return file_path


class RenderTest(GenerateTestCase):
    def setUp(self):
        GenerateTestCase.setUp(self)
        configuration = Configuration(self._output_directory.name, 'https://ancestry.example.com')
        self.app = App(configuration)

    @sync
    async def test_front_page(self):
        await generate(self.app)
        self.assert_betty_html('/index.html')

    @sync
    async def test_files(self):
        await generate(self.app)
        self.assert_betty_html('/file/index.html')
        self.assert_betty_json('/file/index.json', 'fileCollection')

    @sync
    async def test_file(self):
        # @todo This fails somewhere in file.html.j2, very likely because of jinja2._filter_file()
        with NamedTemporaryFile() as f:
            file = File('FILE1', Path(f.name))
            self.app.ancestry.files[file.id] = file
            await generate(self.app)
            self.assert_betty_html('/file/%s/index.html' % file.id)
            self.assert_betty_json('/file/%s/index.json' % file.id, 'file')

    @sync
    async def test_places(self):
        await generate(self.app)
        self.assert_betty_html('/place/index.html')
        self.assert_betty_json('/place/index.json', 'placeCollection')

    @sync
    async def test_place(self):
        place = Place('PLACE1', [PlaceName('one')])
        self.app.ancestry.places[place.id] = place
        await generate(self.app)
        self.assert_betty_html('/place/%s/index.html' % place.id)
        self.assert_betty_json('/place/%s/index.json' % place.id, 'place')

    @sync
    async def test_people(self):
        await generate(self.app)
        self.assert_betty_html('/person/index.html')
        self.assert_betty_json('/person/index.json', 'personCollection')

    @sync
    async def test_person(self):
        person = Person('PERSON1')
        self.app.ancestry.people[person.id] = person
        await generate(self.app)
        self.assert_betty_html('/person/%s/index.html' % person.id)
        self.assert_betty_json('/person/%s/index.json' % person.id, 'person')

    @sync
    async def test_events(self):
        await generate(self.app)
        self.assert_betty_html('/event/index.html')
        self.assert_betty_json('/event/index.json', 'eventCollection')

    @sync
    async def test_event(self):
        event = IdentifiableEvent('EVENT1', Birth())
        self.app.ancestry.events[event.id] = event
        await generate(self.app)
        self.assert_betty_html('/event/%s/index.html' % event.id)
        self.assert_betty_json('/event/%s/index.json' % event.id, 'event')

    @sync
    async def test_citation(self):
        citation = IdentifiableCitation('CITATION1', Source('A Little Birdie'))
        self.app.ancestry.citations[citation.id] = citation
        await generate(self.app)
        self.assert_betty_html('/citation/%s/index.html' % citation.id)
        self.assert_betty_json('/citation/%s/index.json' %
                               citation.id, 'citation')

    @sync
    async def test_sources(self):
        await generate(self.app)
        self.assert_betty_html('/source/index.html')
        self.assert_betty_json('/source/index.json', 'sourceCollection')

    @sync
    async def test_source(self):
        source = IdentifiableSource('SOURCE1', 'A Little Birdie')
        self.app.ancestry.sources[source.id] = source
        await generate(self.app)
        self.assert_betty_html('/source/%s/index.html' % source.id)
        self.assert_betty_json('/source/%s/index.json' % source.id, 'source')


class MultilingualTest(GenerateTestCase):
    def setUp(self):
        GenerateTestCase.setUp(self)
        configuration = Configuration(self._output_directory.name, 'https://ancestry.example.com')
        configuration.locales.clear()
        configuration.locales['nl'] = LocaleConfiguration('nl')
        configuration.locales['en'] = LocaleConfiguration('en')
        self.app = App(configuration)

    @sync
    async def test_root_redirect(self):
        await generate(self.app)
        with open(self.assert_betty_html('/index.html')) as f:
            meta_redirect = '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            self.assertIn(meta_redirect, f.read())

    @sync
    async def test_public_localized_resource(self):
        await generate(self.app)
        with open(self.assert_betty_html('/nl/index.html')) as f:
            translation_link = '<a href="/en/index.html" hreflang="en" lang="en" rel="alternate">English</a>'
            self.assertIn(translation_link, f.read())
        with open(self.assert_betty_html('/en/index.html')) as f:
            translation_link = '<a href="/nl/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>'
            self.assertIn(translation_link, f.read())

    @sync
    async def test_entity(self):
        person = Person('PERSON1')
        self.app.ancestry.people[person.id] = person
        await generate(self.app)
        with open(self.assert_betty_html('/nl/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/en/person/%s/index.html" hreflang="en" lang="en" rel="alternate">English</a>' % person.id
            self.assertIn(translation_link, f.read())
        with open(self.assert_betty_html('/en/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/nl/person/%s/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>' % person.id
            self.assertIn(translation_link, f.read())


class ResourceOverrideTest(GenerateTestCase):
    @sync
    async def test(self):
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as assets_directory_path_str:
                assets_directory_path = Path(assets_directory_path_str)
                localized_assets_directory_path = Path(assets_directory_path) / 'public' / 'localized'
                localized_assets_directory_path.mkdir(parents=True)
                with open(str(localized_assets_directory_path / 'index.html.j2'), 'w') as f:
                    f.write('{% block page_content %}Betty was here{% endblock %}')
                configuration = Configuration(
                    output_directory_path, 'https://ancestry.example.com')
                configuration.assets_directory_path = assets_directory_path
                app = App(configuration)
                await generate(app)
                with open(configuration.www_directory_path / 'index.html') as f:
                    self.assertIn('Betty was here', f.read())


@unittest.skipIf(sys.platform == 'win32', 'lxml cannot be installed directly onto vanilla Windows.')
class SitemapRenderTest(GenerateTestCase):
    def setUp(self):
        GenerateTestCase.setUp(self)
        configuration = Configuration(self._output_directory.name, 'https://ancestry.example.com')
        self.app = App(configuration)

    @sync
    async def test_validate(self):
        await generate(self.app)
        with open(Path(__file__).parent / 'test_generate_assets' / 'sitemap.xsd') as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        with open(self.app.configuration.www_directory_path / 'sitemap.xml') as f:
            sitemap_doc = etree.parse(f)
        schema.validate(sitemap_doc)
