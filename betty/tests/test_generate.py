import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import aiofiles
import pytest

from betty.app import App
from betty.app.extension import Extension
from betty.generate import generate
from betty.locale import Str
from betty.model import (
    Entity,
    get_entity_type_name,
    UserFacingEntity,
    EntityTypeProvider,
)
from betty.model.ancestry import Person, Place, Source, PlaceName, File, Event, Citation
from betty.model.event_type import Birth
from betty.project import (
    LocaleConfiguration,
    EntityTypeConfiguration,
    ExtensionConfiguration,
)
from betty.string import camel_case_to_kebab_case
from betty.tests import assert_betty_html, assert_betty_json


class _ThirdPartyEntity(Entity, UserFacingEntity):
    @classmethod
    def entity_type_label(cls) -> Str:
        return Str.plain(cls.__name__)

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str.plain(cls.__name__)


class _ThirdPartyExtension(Extension, EntityTypeProvider):
    async def entity_types(self) -> set[type[Entity]]:
        return {_ThirdPartyEntity}


class TestGenerate:
    async def test_html_lang(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        await generate(new_temporary_app)
        async with aiofiles.open(
            await assert_betty_html(
                new_temporary_app, "/nl/index.html", check_links=True
            )
        ) as f:
            html = await f.read()
            assert '<html lang="nl-NL"' in html

    async def test_root_redirect(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.locales.replace(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
        )
        await generate(new_temporary_app)
        async with aiofiles.open(
            await assert_betty_html(new_temporary_app, "/index.html", check_links=True)
        ) as f:
            meta_redirect = (
                '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
            )
            assert meta_redirect in await f.read()

    async def test_links(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.locales.replace(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
        )
        await generate(new_temporary_app)
        async with aiofiles.open(
            await assert_betty_html(
                new_temporary_app, "/nl/index.html", check_links=True
            )
        ) as f:
            html = await f.read()
            assert (
                '<link rel="canonical" href="https://example.com/nl/index.html" hreflang="nl-NL" type="text/html">'
                in html
            )
            assert (
                '<link rel="alternate" href="/en/index.html" hreflang="en-US" type="text/html">'
                in html
            )
        async with aiofiles.open(
            await assert_betty_html(
                new_temporary_app, "/en/index.html", check_links=True
            )
        ) as f:
            html = await f.read()
            assert (
                '<link rel="canonical" href="https://example.com/en/index.html" hreflang="en-US" type="text/html">'
                in html
            )
            assert (
                '<link rel="alternate" href="/nl/index.html" hreflang="nl-NL" type="text/html">'
                in html
            )

    async def test_links_for_entity_pages(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.locales.replace(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
        )
        person = Person(id="PERSON1")
        new_temporary_app.project.ancestry.add(person)
        await generate(new_temporary_app)
        async with aiofiles.open(
            await assert_betty_html(
                new_temporary_app,
                f"/nl/person/{person.id}/index.html",
                check_links=True,
            )
        ) as f:
            html = await f.read()
        assert (
            f'<link rel="canonical" href="https://example.com/nl/person/{person.id}/index.html" hreflang="nl-NL" type="text/html">'
            in html
        )
        assert (
            f'<link rel="alternate" href="/en/person/{person.id}/index.html" hreflang="en-US" type="text/html">'
            in html
        )
        assert (
            f'<link rel="alternate" href="/person/{person.id}/index.json" hreflang="und" type="application/json">'
            in html
        )
        async with aiofiles.open(
            await assert_betty_html(
                new_temporary_app,
                f"/en/person/{person.id}/index.html",
                check_links=True,
            )
        ) as f:
            html = await f.read()
        assert (
            f'<link rel="canonical" href="https://example.com/en/person/{person.id}/index.html" hreflang="en-US" type="text/html">'
            in html
        )
        assert (
            f'<link rel="alternate" href="/nl/person/{person.id}/index.html" hreflang="nl-NL" type="text/html">'
            in html
        )
        assert (
            f'<link rel="alternate" href="/person/{person.id}/index.json" hreflang="und" type="application/json">'
            in html
        )

    async def test_third_party_entities(self, new_temporary_app: App) -> None:
        entity_type = _ThirdPartyEntity
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(_ThirdPartyExtension)
        )
        new_temporary_app.project.configuration.entity_types.append(
            EntityTypeConfiguration(
                entity_type=entity_type,
                generate_html_list=True,
            )
        )
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app,
            f"/{camel_case_to_kebab_case(get_entity_type_name(entity_type))}/index.html",
            check_links=True,
        )
        await assert_betty_json(
            new_temporary_app,
            f"/{camel_case_to_kebab_case(get_entity_type_name(entity_type))}/index.json",
        )

    async def test_third_party_entity(self, new_temporary_app: App) -> None:
        entity_type = _ThirdPartyEntity
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(_ThirdPartyExtension)
        )
        entity = _ThirdPartyEntity(
            id="ENTITY1",
        )
        new_temporary_app.project.ancestry.add(entity)
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app,
            f"/{camel_case_to_kebab_case(get_entity_type_name(entity_type))}/{entity.id}/index.html",
            check_links=True,
        )
        await assert_betty_json(
            new_temporary_app,
            f"/{camel_case_to_kebab_case(get_entity_type_name(entity_type))}/{entity.id}/index.json",
        )

    async def test_files(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.entity_types.append(
            EntityTypeConfiguration(
                entity_type=File,
                generate_html_list=True,
            )
        )
        await generate(new_temporary_app)
        await assert_betty_html(new_temporary_app, "/file/index.html", check_links=True)
        await assert_betty_json(new_temporary_app, "/file/index.json", "fileCollection")

    async def test_file(self, new_temporary_app: App) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="FILE1",
                path=Path(f.name),
            )
            new_temporary_app.project.ancestry.add(file)
            await generate(new_temporary_app)
            await assert_betty_html(
                new_temporary_app, "/file/%s/index.html" % file.id, check_links=True
            )
            await assert_betty_json(new_temporary_app, "/file/%s/index.json" % file.id)

    async def test_places(self, new_temporary_app: App) -> None:
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/place/index.html", check_links=True
        )
        await assert_betty_json(new_temporary_app, "/place/index.json")

    async def test_place(self, new_temporary_app: App) -> None:
        place = Place(
            id="PLACE1",
            names=[PlaceName(name="one")],
        )
        new_temporary_app.project.ancestry.add(place)
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/place/%s/index.html" % place.id, check_links=True
        )
        await assert_betty_json(new_temporary_app, "/place/%s/index.json" % place.id)

    async def test_people(self, new_temporary_app: App) -> None:
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/person/index.html", check_links=True
        )
        await assert_betty_json(new_temporary_app, "/person/index.json")

    async def test_person(self, new_temporary_app: App) -> None:
        person = Person(id="PERSON1")
        new_temporary_app.project.ancestry.add(person)
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app,
            f"/person/{person.id}/index.html",
            check_links=True,
        )
        await assert_betty_json(
            new_temporary_app,
            f"/person/{person.id}/index.json",
        )

    async def test_events(self, new_temporary_app: App) -> None:
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/event/index.html", check_links=True
        )
        await assert_betty_json(
            new_temporary_app, "/event/index.json", "eventCollection"
        )

    async def test_event(self, new_temporary_app: App) -> None:
        event = Event(
            id="EVENT1",
            event_type=Birth,
        )
        new_temporary_app.project.ancestry.add(event)
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/event/%s/index.html" % event.id, check_links=True
        )
        await assert_betty_json(
            new_temporary_app, "/event/%s/index.json" % event.id, "event"
        )

    async def test_citation(self, new_temporary_app: App) -> None:
        source = Source("A Little Birdie")
        citation = Citation(
            id="CITATION1",
            source=source,
        )
        new_temporary_app.project.ancestry.add(citation, source)
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/citation/%s/index.html" % citation.id, check_links=True
        )
        await assert_betty_json(
            new_temporary_app, "/citation/%s/index.json" % citation.id
        )

    async def test_sources(self, new_temporary_app: App) -> None:
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/source/index.html", check_links=True
        )
        await assert_betty_json(new_temporary_app, "/source/index.json")

    async def test_source(self, new_temporary_app: App) -> None:
        source = Source(
            id="SOURCE1",
            name="A Little Birdie",
        )
        new_temporary_app.project.ancestry.add(source)
        await generate(new_temporary_app)
        await assert_betty_html(
            new_temporary_app, "/source/%s/index.html" % source.id, check_links=True
        )
        await assert_betty_json(new_temporary_app, "/source/%s/index.json" % source.id)


class TestResourceOverride:
    async def test(self, new_temporary_app: App) -> None:
        localized_assets_directory_path = (
            Path(new_temporary_app.project.configuration.assets_directory_path)
            / "public"
            / "localized"
        )
        localized_assets_directory_path.mkdir(parents=True)
        async with aiofiles.open(
            str(localized_assets_directory_path / "index.html.j2"), "w"
        ) as f:
            await f.write("{% block page_content %}Betty was here{% endblock %}")
        await generate(new_temporary_app)
        async with aiofiles.open(
            new_temporary_app.project.configuration.www_directory_path / "index.html"
        ) as f:
            assert "Betty was here" in await f.read()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="lxml cannot be installed directly onto vanilla Windows.",
)
class TestSitemapGenerate:
    async def test_validate(self, new_temporary_app: App) -> None:
        from lxml import etree

        await generate(new_temporary_app)
        schema_doc = etree.parse(
            Path(__file__).parent / "test_generate_assets" / "sitemap.xsd"
        )
        schema = etree.XMLSchema(schema_doc)
        sitemap_doc = etree.parse(
            new_temporary_app.project.configuration.www_directory_path / "sitemap.xml"
        )
        schema.validate(sitemap_doc)
