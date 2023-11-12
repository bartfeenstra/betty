import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from aiofiles.os import makedirs

from betty.app import App
from betty.generate import generate
from betty.model.ancestry import Person, Place, Source, PlaceName, File, Event, Citation
from betty.model.event_type import Birth
from betty.project import LocaleConfiguration, EntityTypeConfiguration
from betty.tests import assert_betty_html, assert_betty_json


class TestGenerate:
    async def test_html_lang(self) -> None:
        app = App()
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        async with app:
            await generate(app)
            with open(assert_betty_html(app, '/nl/index.html', check_links=True)) as f:
                html = f.read()
                assert '<html lang="nl-NL"' in html

    async def test_root_redirect(self) -> None:
        app = App()
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        async with app:
            await generate(app)
        with open(assert_betty_html(app, '/index.html', check_links=True)) as f:
            meta_redirect = '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            assert meta_redirect in f.read()

    async def test_links(self) -> None:
        app = App()
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        async with app:
            await generate(app)
        with open(assert_betty_html(app, '/nl/index.html', check_links=True)) as f:
            html = f.read()
            assert '<link rel="canonical" href="https://example.com/nl/index.html" hreflang="nl-NL" type="text/html"/>' in html
            assert '<link rel="alternate" href="/en/index.html" hreflang="en-US" type="text/html"/>' in html
        with open(assert_betty_html(app, '/en/index.html', check_links=True)) as f:
            html = f.read()
            assert '<link rel="canonical" href="https://example.com/en/index.html" hreflang="en-US" type="text/html"/>' in html
            assert '<link rel="alternate" href="/nl/index.html" hreflang="nl-NL" type="text/html"/>' in html

    async def test_links_for_entity_pages(self) -> None:
        app = App()
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        async with app:
            person = Person(id='PERSON1')
            app.project.ancestry.add(person)
            await generate(app)
        with open(assert_betty_html(app, f'/nl/person/{person.id}/index.html', check_links=True)) as f:
            html = f.read()
        assert f'<link rel="canonical" href="https://example.com/nl/person/{person.id}/index.html" hreflang="nl-NL" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/en/person/{person.id}/index.html" hreflang="en-US" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/person/{person.id}/index.json" hreflang="und" type="application/json"/>' in html
        with open(assert_betty_html(app, f'/en/person/{person.id}/index.html', check_links=True)) as f:
            html = f.read()
        assert f'<link rel="canonical" href="https://example.com/en/person/{person.id}/index.html" hreflang="en-US" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/nl/person/{person.id}/index.html" hreflang="nl-NL" type="text/html"/>' in html
        assert f'<link rel="alternate" href="/person/{person.id}/index.json" hreflang="und" type="application/json"/>' in html

    async def test_files(self) -> None:
        async with App() as app:
            app.project.configuration.entity_types.append(EntityTypeConfiguration(File, True))
            await generate(app)
        assert_betty_html(app, '/file/index.html', check_links=True)
        assert_betty_json(app, '/file/index.json', 'fileCollection')

    async def test_file(self) -> None:
        async with App() as app:
            with NamedTemporaryFile() as f:
                file = File(
                    id='FILE1',
                    path=Path(f.name),
                )
                app.project.ancestry.add(file)
                await generate(app)
            assert_betty_html(app, '/file/%s/index.html' % file.id, check_links=True)
            assert_betty_json(app, '/file/%s/index.json' % file.id, 'file')

    async def test_places(self) -> None:
        async with App() as app:
            await generate(app)
        assert_betty_html(app, '/place/index.html', check_links=True)
        assert_betty_json(app, '/place/index.json', 'placeCollection')

    async def test_place(self) -> None:
        async with App() as app:
            place = Place(
                id='PLACE1',
                names=[PlaceName(name='one')],
            )
            app.project.ancestry.add(place)
            await generate(app)
        assert_betty_html(app, '/place/%s/index.html' % place.id, check_links=True)
        assert_betty_json(app, '/place/%s/index.json' % place.id, 'place')

    async def test_people(self) -> None:
        async with App() as app:
            await generate(app)
        assert_betty_html(app, '/person/index.html', check_links=True)
        assert_betty_json(app, '/person/index.json', 'personCollection')

    async def test_person(self) -> None:
        person = Person(id='PERSON1')
        app = App()
        app.project.ancestry.add(person)
        async with app:
            await generate(app)
        assert_betty_html(
            app,
            f'/person/{person.id}/index.html',
            check_links=True,
        )
        assert_betty_json(
            app,
            f'/person/{person.id}/index.json',
            'person',
        )

    async def test_events(self) -> None:
        async with App() as app:
            await generate(app)
        assert_betty_html(app, '/event/index.html', check_links=True)
        assert_betty_json(app, '/event/index.json', 'eventCollection')

    async def test_event(self) -> None:
        async with App() as app:
            event = Event(
                id='EVENT1',
                event_type=Birth,
            )
            app.project.ancestry.add(event)
            await generate(app)
        assert_betty_html(app, '/event/%s/index.html' % event.id, check_links=True)
        assert_betty_json(app, '/event/%s/index.json' % event.id, 'event')

    async def test_citation(self) -> None:
        async with App() as app:
            source = Source('A Little Birdie')
            citation = Citation(
                id='CITATION1',
                source=source,
            )
            app.project.ancestry.add(citation, source)
            await generate(app)
        assert_betty_html(app, '/citation/%s/index.html' % citation.id, check_links=True)
        assert_betty_json(app, '/citation/%s/index.json' % citation.id, 'citation')

    async def test_sources(self) -> None:
        async with App() as app:
            await generate(app)
        assert_betty_html(app, '/source/index.html', check_links=True)
        assert_betty_json(app, '/source/index.json', 'sourceCollection')

    async def test_source(self) -> None:
        async with App() as app:
            source = Source(
                id='SOURCE1',
                name='A Little Birdie',
            )
            app.project.ancestry.add(source)
            await generate(app)
        assert_betty_html(app, '/source/%s/index.html' % source.id, check_links=True)
        assert_betty_json(app, '/source/%s/index.json' % source.id, 'source')


class TestResourceOverride:
    async def test(self) -> None:
        async with App() as app:
            localized_assets_directory_path = Path(app.project.configuration.assets_directory_path) / 'public' / 'static'
            await makedirs(localized_assets_directory_path)
            with open(str(localized_assets_directory_path / 'index.html.j2'), 'w') as f:
                f.write('{% block page_content %}Betty was here{% endblock %}')
            await generate(app)
        with open(app.project.configuration.www_directory_path / 'index.html') as f:
            assert 'Betty was here' in f.read()


@pytest.mark.skipif(sys.platform == 'win32', reason='lxml cannot be installed directly onto vanilla Windows.')
class TestSitemapGenerate:
    async def test_validate(self) -> None:
        from lxml import etree

        async with App() as app:
            await generate(app)
        with open(Path(__file__).parent / 'test_generate_assets' / 'sitemap.xsd') as f:
            schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        with open(app.project.configuration.www_directory_path / 'sitemap.xml') as f:
            sitemap_doc = etree.parse(f)
        schema.validate(sitemap_doc)
