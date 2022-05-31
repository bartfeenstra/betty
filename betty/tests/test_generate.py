import json as stdjson
import sys
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

import html5lib
from lxml import etree

from betty import json
from betty.app import App
from betty.generate import generate
from betty.model.ancestry import Person, Place, Source, PlaceName, File, Event, Citation
from betty.model.event_type import Birth
from betty.project import LocaleConfiguration


def assert_betty_html(app: App, url_path: str) -> Path:
    file_path = app.project.configuration.www_directory_path / Path(url_path.lstrip('/'))
    assert file_path.exists(), f'{file_path} does not exist'
    with open(file_path) as f:
        parser = html5lib.HTMLParser(strict=True)
        parser.parse(f)
    return file_path


def assert_betty_json(app: App, url_path: str, schema_definition: str) -> Path:
    file_path = app.project.configuration.www_directory_path / Path(url_path.lstrip('/'))
    assert file_path.exists(), f'{file_path} does not exist'
    with open(file_path) as f:
        json.validate(stdjson.load(f), schema_definition, app)
    return file_path


class TestGenerate:
    async def test_front_page(self):
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/index.html')

    async def test_translations(self):
        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            await generate(app)
            with open(assert_betty_html(app, '/nl/index.html')) as f:
                html = f.read()
                assert '<html lang="nl-NL"' in html
                assert 'Stop met zoeken' in html

    async def test_files(self):
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/file/index.html')
        assert_betty_json(app, '/file/index.json', 'fileCollection')

    async def test_file(self):
        with App() as app:
            with NamedTemporaryFile() as f:
                file = File('FILE1', Path(f.name))
                app.project.ancestry.entities.append(file)
                await generate(app)
            assert_betty_html(app, '/file/%s/index.html' % file.id)
            assert_betty_json(app, '/file/%s/index.json' % file.id, 'file')

    async def test_places(self):
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/place/index.html')
        assert_betty_json(app, '/place/index.json', 'placeCollection')

    async def test_place(self):
        with App() as app:
            place = Place('PLACE1', [PlaceName('one')])
            app.project.ancestry.entities.append(place)
            await generate(app)
        assert_betty_html(app, '/place/%s/index.html' % place.id)
        assert_betty_json(app, '/place/%s/index.json' % place.id, 'place')

    async def test_people(self):
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/person/index.html')
        assert_betty_json(app, '/person/index.json', 'personCollection')

    async def test_person(self):
        with App() as app:
            person = Person('PERSON1')
            app.project.ancestry.entities.append(person)
            await generate(app)
        assert_betty_html(app, '/person/%s/index.html' % person.id)
        assert_betty_json(app, '/person/%s/index.json' % person.id, 'person')

    async def test_events(self):
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/event/index.html')
        assert_betty_json(app, '/event/index.json', 'eventCollection')

    async def test_event(self):
        with App() as app:
            event = Event('EVENT1', Birth())
            app.project.ancestry.entities.append(event)
            await generate(app)
        assert_betty_html(app, '/event/%s/index.html' % event.id)
        assert_betty_json(app, '/event/%s/index.json' % event.id, 'event')

    async def test_citation(self):
        with App() as app:
            citation = Citation('CITATION1', Source('A Little Birdie'))
            app.project.ancestry.entities.append(citation)
            await generate(app)
        assert_betty_html(app, '/citation/%s/index.html' % citation.id)
        assert_betty_json(app, '/citation/%s/index.json' % citation.id, 'citation')

    async def test_sources(self):
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/source/index.html')
        assert_betty_json(app, '/source/index.json', 'sourceCollection')

    async def test_source(self):
        with App() as app:
            source = Source('SOURCE1', 'A Little Birdie')
            app.project.ancestry.entities.append(source)
            await generate(app)
        assert_betty_html(app, '/source/%s/index.html' % source.id)
        assert_betty_json(app, '/source/%s/index.json' % source.id, 'source')


class TestMultilingual:
    async def test_root_redirect(self):
        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        with app:
            await generate(app)
        with open(assert_betty_html(app, '/index.html')) as f:
            meta_redirect = '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            assert meta_redirect in f.read()

    async def test_public_localized_resource(self):
        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        with app:
            await generate(app)
        with open(assert_betty_html(app, '/nl/index.html')) as f:
            translation_link = '<a href="/en/index.html" hreflang="en" lang="en" rel="alternate">English</a>'
            assert translation_link in f.read()
        with open(assert_betty_html(app, '/en/index.html')) as f:
            translation_link = '<a href="/nl/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>'
            assert translation_link in f.read()

    async def test_entity(self):
        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        with app:
            person = Person('PERSON1')
            app.project.ancestry.entities.append(person)
            await generate(app)
        with open(assert_betty_html(app, '/nl/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/en/person/%s/index.html" hreflang="en" lang="en" rel="alternate">English</a>' % person.id
            assert translation_link in f.read()
        with open(assert_betty_html(app, '/en/person/%s/index.html' % person.id)) as f:
            translation_link = '<a href="/nl/person/%s/index.html" hreflang="nl" lang="nl" rel="alternate">Nederlands</a>' % person.id
            assert translation_link in f.read()


class TestResourceOverride:
    async def test(self):
        with App() as app:
            localized_assets_directory_path = Path(app.project.configuration.assets_directory_path) / 'public' / 'localized'
            localized_assets_directory_path.mkdir(parents=True)
            with open(str(localized_assets_directory_path / 'index.html.j2'), 'w') as f:
                f.write('{% block page_content %}Betty was here{% endblock %}')
            await generate(app)
        with open(app.project.configuration.www_directory_path / 'index.html') as f:
            assert 'Betty was here' in f.read()


@unittest.skipIf(sys.platform == 'win32', 'lxml cannot be installed directly onto vanilla Windows.')
class TestSitemapGenerate:
    async def test_validate(self):
        with App() as app:
            await generate(app)
        with open(Path(__file__).parent / 'test_generate_assets' / 'sitemap.xsd') as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        with open(app.project.configuration.www_directory_path / 'sitemap.xml') as f:
            sitemap_doc = etree.parse(f)
        schema.validate(sitemap_doc)
