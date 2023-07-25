import json as stdjson
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import html5lib
import pytest

from betty import json
from betty.app import App
from betty.generate import generate
from betty.model.ancestry import Person, Place, Source, PlaceName, File, Event, Citation
from betty.model.event_type import Birth
from betty.project import LocaleConfiguration, EntityTypeConfiguration


def assert_betty_html(app: App, url_path: str) -> Path:
    file_path = app.static_www_directory_path / Path(url_path.lstrip('/'))
    with open(file_path) as f:
        betty_html = f.read()
    html5lib.HTMLParser(strict=True).parse(betty_html)
    return file_path


def assert_betty_json(app: App, url_path: str, schema_definition: str) -> Path:
    file_path = app.project.configuration.www_directory_path / Path(url_path.lstrip('/'))
    with open(file_path) as f:
        betty_json = stdjson.load(f)
    json.validate(betty_json, schema_definition, app)
    return file_path


class TestGenerate:
    async def test_html_lang(self) -> None:
        app = App()
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        with app:
            await generate(app)
            with open(assert_betty_html(app, '/nl/index.html')) as f:
                html = f.read()
                assert '<html lang="nl-NL"' in html

    async def test_root_redirect(self) -> None:
        app = App()
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        with app:
            await generate(app)
        with open(assert_betty_html(app, '/index.html')) as f:
            meta_redirect = '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            assert meta_redirect in f.read()

    async def test_links(self) -> None:
        app = App()
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        with app:
            await generate(app)
        with open(assert_betty_html(app, '/nl/index.html')) as f:
            html = f.read()
            assert '<link rel="canonical" href="https://example.com/nl/index.html" hreflang="nl-NL" type="text/html"/>' in html
            assert '<link rel="alternate" href="/en/index.html" hreflang="en-US" type="text/html"/>' in html
        with open(assert_betty_html(app, '/en/index.html')) as f:
            html = f.read()
            assert '<link rel="canonical" href="https://example.com/en/index.html" hreflang="en-US" type="text/html"/>' in html
            assert '<link rel="alternate" href="/nl/index.html" hreflang="nl-NL" type="text/html"/>' in html

    async def test_links_for_entity_pages(self) -> None:
        app = App()
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        with app:
            person = Person('PERSON1')
            app.project.ancestry.add(person)
            await generate(app)
        with open(assert_betty_html(app, f'/nl/person/{person.id}/index.html')) as f:
            html = f.read()
        assert f'<link rel="canonical" href="https://example.com/nl/person/{person.id}/index.html" hreflang="nl-NL" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/nl/person/{person.id}/index.json" hreflang="nl-NL" type="application/json"/>' in html
        assert f'<link rel="alternate" href="/en/person/{person.id}/index.html" hreflang="en-US" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/en/person/{person.id}/index.json" hreflang="en-US" type="application/json"/>' in html
        with open(assert_betty_html(app, f'/en/person/{person.id}/index.html')) as f:
            html = f.read()
        assert f'<link rel="canonical" href="https://example.com/en/person/{person.id}/index.html" hreflang="en-US" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/en/person/{person.id}/index.json" hreflang="en-US" type="application/json"/>' in html
        assert f'<link rel="alternate" href="/nl/person/{person.id}/index.html" hreflang="nl-NL" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/nl/person/{person.id}/index.json" hreflang="nl-NL" type="application/json"/>' in html

    async def test_files(self) -> None:
        with App() as app:
            app.project.configuration.entity_types.append(EntityTypeConfiguration(File, True))
            await generate(app)
        assert_betty_html(app, '/file/index.html')
        assert_betty_json(app, '/file/index.json', 'fileCollection')

    async def test_file(self) -> None:
        with App() as app:
            with NamedTemporaryFile() as f:
                file = File('FILE1', Path(f.name))
                app.project.ancestry.add(file)
                await generate(app)
            assert_betty_html(app, '/file/%s/index.html' % file.id)
            assert_betty_json(app, '/file/%s/index.json' % file.id, 'file')

    async def test_places(self) -> None:
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/place/index.html')
        assert_betty_json(app, '/place/index.json', 'placeCollection')

    async def test_place(self) -> None:
        with App() as app:
            place = Place('PLACE1', [PlaceName('one')])
            app.project.ancestry.add(place)
            await generate(app)
        assert_betty_html(app, '/place/%s/index.html' % place.id)
        assert_betty_json(app, '/place/%s/index.json' % place.id, 'place')

    async def test_people(self) -> None:
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/person/index.html')
        assert_betty_json(app, '/person/index.json', 'personCollection')

    async def test_person(self) -> None:
        with App() as app:
            person = Person('PERSON1')
            app.project.ancestry.add(person)
            await generate(app)
        assert_betty_html(app, '/person/%s/index.html' % person.id)
        assert_betty_json(app, '/person/%s/index.json' % person.id, 'person')

    async def test_events(self) -> None:
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/event/index.html')
        assert_betty_json(app, '/event/index.json', 'eventCollection')

    async def test_event(self) -> None:
        with App() as app:
            event = Event('EVENT1', Birth)
            app.project.ancestry.add(event)
            await generate(app)
        assert_betty_html(app, '/event/%s/index.html' % event.id)
        assert_betty_json(app, '/event/%s/index.json' % event.id, 'event')

    async def test_citation(self) -> None:
        with App() as app:
            source = Source('A Little Birdie')
            citation = Citation('CITATION1', source)
            app.project.ancestry.add(citation, source)
            await generate(app)
        assert_betty_html(app, '/citation/%s/index.html' % citation.id)
        assert_betty_json(app, '/citation/%s/index.json' % citation.id, 'citation')

    async def test_sources(self) -> None:
        with App() as app:
            await generate(app)
        assert_betty_html(app, '/source/index.html')
        assert_betty_json(app, '/source/index.json', 'sourceCollection')

    async def test_source(self) -> None:
        with App() as app:
            source = Source('SOURCE1', 'A Little Birdie')
            app.project.ancestry.add(source)
            await generate(app)
        assert_betty_html(app, '/source/%s/index.html' % source.id)
        assert_betty_json(app, '/source/%s/index.json' % source.id, 'source')


class TestResourceOverride:
    async def test(self) -> None:
        with App() as app:
            localized_assets_directory_path = Path(app.project.configuration.assets_directory_path) / 'public' / 'static'
            localized_assets_directory_path.mkdir(parents=True)
            with open(str(localized_assets_directory_path / 'index.html.j2'), 'w') as f:
                f.write('{% block page_content %}Betty was here{% endblock %}')
            await generate(app)
        with open(app.project.configuration.www_directory_path / 'index.html') as f:
            assert 'Betty was here' in f.read()


@pytest.mark.skipif(sys.platform == 'win32', reason='lxml cannot be installed directly onto vanilla Windows.')
class TestSitemapGenerate:
    async def test_validate(self) -> None:
        from lxml import etree

        with App() as app:
            await generate(app)
        with open(Path(__file__).parent / 'test_generate_assets' / 'sitemap.xsd') as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        with open(app.project.configuration.www_directory_path / 'sitemap.xml') as f:
            sitemap_doc = etree.parse(f)
        schema.validate(sitemap_doc)
