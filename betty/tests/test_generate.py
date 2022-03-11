import json as stdjson
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile

import html5lib
from lxml import etree

from betty import json
from betty.app import App, LocaleConfiguration
from betty.asyncio import sync
from betty.generate import generate
from betty.model.ancestry import Person, Place, Source, PlaceName, File, Event, Citation
from betty.model.event_type import Birth
from betty.tests import TestCase


class GenerateTestCase(TestCase):
    def assert_betty_html(self, app: App, url_path: str) -> Path:
        file_path = app.configuration.www_directory_path / Path(url_path.lstrip('/'))
        self.assertTrue(file_path.exists(), '%s does not exist' % file_path)
        with open(file_path) as f:
            parser = html5lib.HTMLParser(strict=True)
            parser.parse(f)
        return file_path

    def assert_betty_json(self, app: App, url_path: str, schema_definition: str) -> Path:
        file_path = app.configuration.www_directory_path / Path(url_path.lstrip('/'))
        self.assertTrue(file_path.exists(), '%s does not exist' % file_path)
        with open(file_path) as f:
            json.validate(stdjson.load(f), schema_definition, app)
        return file_path


class GenerateTest(GenerateTestCase):
    @sync
    async def test_front_page(self):
        async with App() as app:
            await generate(app)
        self.assert_betty_html(app, '/index.html')

    @sync
    async def test_files(self):
        async with App() as app:
            await generate(app)
        self.assert_betty_html(app, '/file/index.html')
        self.assert_betty_json(app, '/file/index.json', 'fileCollection')

    @sync
    async def test_file(self):
        async with App() as app:
            with NamedTemporaryFile() as f:
                file = File('FILE1', Path(f.name))
                app.ancestry.entities.append(file)
                await generate(app)
            self.assert_betty_html(app, '/file/%s/index.html' % file.id)
            self.assert_betty_json(app, '/file/%s/index.json' % file.id, 'file')

    @sync
    async def test_places(self):
        async with App() as app:
            await generate(app)
        self.assert_betty_html(app, '/place/index.html')
        self.assert_betty_json(app, '/place/index.json', 'placeCollection')

    @sync
    async def test_place(self):
        async with App() as app:
            place = Place('PLACE1', [PlaceName('one')])
            app.ancestry.entities.append(place)
            await generate(app)
        self.assert_betty_html(app, '/place/%s/index.html' % place.id)
        self.assert_betty_json(app, '/place/%s/index.json' % place.id, 'place')

    @sync
    async def test_people(self):
        async with App() as app:
            await generate(app)
        self.assert_betty_html(app, '/person/index.html')
        self.assert_betty_json(app, '/person/index.json', 'personCollection')

    @sync
    async def test_person(self):
        async with App() as app:
            person = Person('PERSON1')
            app.ancestry.entities.append(person)
            await generate(app)
        self.assert_betty_html(app, '/person/%s/index.html' % person.id)
        self.assert_betty_json(app, '/person/%s/index.json' % person.id, 'person')

    @sync
    async def test_events(self):
        async with App() as app:
            await generate(app)
        self.assert_betty_html(app, '/event/index.html')
        self.assert_betty_json(app, '/event/index.json', 'eventCollection')

    @sync
    async def test_event(self):
        async with App() as app:
            event = Event('EVENT1', Birth())
            app.ancestry.entities.append(event)
            await generate(app)
        self.assert_betty_html(app, '/event/%s/index.html' % event.id)
        self.assert_betty_json(app, '/event/%s/index.json' % event.id, 'event')

    @sync
    async def test_citation(self):
        async with App() as app:
            citation = Citation('CITATION1', Source('A Little Birdie'))
            app.ancestry.entities.append(citation)
            await generate(app)
        self.assert_betty_html(app, '/citation/%s/index.html' % citation.id)
        self.assert_betty_json(app, '/citation/%s/index.json' %
                               citation.id, 'citation')

    @sync
    async def test_sources(self):
        async with App() as app:
            await generate(app)
        self.assert_betty_html(app, '/source/index.html')
        self.assert_betty_json(app, '/source/index.json', 'sourceCollection')

    @sync
    async def test_source(self):
        async with App() as app:
            source = Source('SOURCE1', 'A Little Birdie')
            app.ancestry.entities.append(source)
            await generate(app)
        self.assert_betty_html(app, '/source/%s/index.html' % source.id)
        self.assert_betty_json(app, '/source/%s/index.json' % source.id, 'source')


class MultilingualTest(GenerateTestCase):
    @sync
    async def test_root_redirect(self):
        app = App()
        app.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        async with app:
            await generate(app)
        with open(self.assert_betty_html(app, '/index.html')) as f:
            meta_redirect = '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            self.assertIn(meta_redirect, f.read())

    @sync
    async def test_public_localized_resource(self):
        app = App()
        app.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        async with app:
            await generate(app)
        with open(self.assert_betty_html(app, '/nl/index.html')) as f:
            translation_link = '<a href="/en/index.html" hreflang="en" lang="en" rel="alternate">English</a>'
            self.assertIn(translation_link, f.read())
        with open(self.assert_betty_html(app, '/en/index.html')) as f:
            translation_link = '<a href="/nl/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>'
            self.assertIn(translation_link, f.read())

    @sync
    async def test_entity(self):
        app = App()
        app.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        async with app:
            person = Person('PERSON1')
            app.ancestry.entities.append(person)
            await generate(app)
        with open(self.assert_betty_html(app, '/nl/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/en/person/%s/index.html" hreflang="en" lang="en" rel="alternate">English</a>' % person.id
            self.assertIn(translation_link, f.read())
        with open(self.assert_betty_html(app, '/en/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/nl/person/%s/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>' % person.id
            self.assertIn(translation_link, f.read())


class ResourceOverrideTest(GenerateTestCase):
    @sync
    async def test(self):
        with TemporaryDirectory() as assets_directory_path_str:
            assets_directory_path = Path(assets_directory_path_str)
            localized_assets_directory_path = Path(assets_directory_path) / 'public' / 'localized'
            localized_assets_directory_path.mkdir(parents=True)
            with open(str(localized_assets_directory_path / 'index.html.j2'), 'w') as f:
                f.write('{% block page_content %}Betty was here{% endblock %}')
            async with App() as app:
                app.configuration.assets_directory_path = assets_directory_path
                await generate(app)
        with open(app.configuration.www_directory_path / 'index.html') as f:
            self.assertIn('Betty was here', f.read())


@unittest.skipIf(sys.platform == 'win32', 'lxml cannot be installed directly onto vanilla Windows.')
class SitemapGenerateTest(GenerateTestCase):
    @sync
    async def test_validate(self):
        async with App() as app:
            await generate(app)
        with open(Path(__file__).parent / 'test_generate_assets' / 'sitemap.xsd') as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        with open(app.configuration.www_directory_path / 'sitemap.xml') as f:
            sitemap_doc = etree.parse(f)
        schema.validate(sitemap_doc)
