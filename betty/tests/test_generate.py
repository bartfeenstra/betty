import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import aiofiles
import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.generate import generate, GenerateSiteEvent, GenerationContext
from betty.model import (
    UserFacingEntity,
)
from betty.model.ancestry import Person, Place, Source, PlaceName, File, Event, Citation
from betty.model.event_type import Birth
from betty.plugin.static import StaticPluginRepository
from betty.project import (
    LocaleConfiguration,
    EntityTypeConfiguration,
    Project,
)
from betty.string import camel_case_to_kebab_case
from betty.test_utils.assets.templates import assert_betty_html, assert_betty_json
from betty.test_utils.model import DummyEntity


class ThirdPartyEntity(UserFacingEntity, DummyEntity):
    pass


class TestGenerate:
    async def test_html_lang(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            async with project:
                await generate(project)
                async with aiofiles.open(
                    await assert_betty_html(project, "/nl/index.html")
                ) as f:
                    html = await f.read()
                    assert '<html lang="nl-NL"' in html

    async def test_root_redirect(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.locales.replace(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
            )
            async with project:
                await generate(project)
                async with aiofiles.open(
                    await assert_betty_html(project, "/index.html")
                ) as f:
                    meta_redirect = (
                        '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
                    )
                    assert meta_redirect in await f.read()

    async def test_links(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.locales.replace(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
            )
            async with project:
                await generate(project)
                async with aiofiles.open(
                    await assert_betty_html(project, "/nl/index.html")
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
                    await assert_betty_html(project, "/en/index.html")
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

    async def test_links_for_entity_pages(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.locales.replace(
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
            project.ancestry.add(person)
            async with project:
                await generate(project)
                async with aiofiles.open(
                    await assert_betty_html(
                        project, f"/nl/person/{person.id}/index.html"
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
                        project, f"/en/person/{person.id}/index.html"
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

    async def test_third_party_entities(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(ThirdPartyEntity),
        )
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.entity_types.append(
                EntityTypeConfiguration(
                    entity_type=ThirdPartyEntity,
                    generate_html_list=True,
                )
            )
            async with project:
                await generate(project)
                await assert_betty_html(
                    project,
                    f"/{camel_case_to_kebab_case(ThirdPartyEntity.plugin_id())}/index.html",
                )
                await assert_betty_json(
                    project,
                    f"/{camel_case_to_kebab_case(ThirdPartyEntity.plugin_id())}/index.json",
                )

    async def test_third_party_entity(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(ThirdPartyEntity),
        )
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            entity = ThirdPartyEntity(
                id="ENTITY1",
            )
            project.ancestry.add(entity)
            async with project:
                await generate(project)
                await assert_betty_html(
                    project,
                    f"/{camel_case_to_kebab_case(ThirdPartyEntity.plugin_id())}/{entity.id}/index.html",
                )
                await assert_betty_json(
                    project,
                    f"/{camel_case_to_kebab_case(ThirdPartyEntity.plugin_id())}/{entity.id}/index.json",
                )

    async def test_files(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.entity_types.append(
                EntityTypeConfiguration(
                    entity_type=File,
                    generate_html_list=True,
                )
            )
            async with project:
                await generate(project)
                await assert_betty_html(project, "/file/index.html")
                await assert_betty_json(project, "/file/index.json", "fileCollection")

    async def test_file(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            with NamedTemporaryFile() as f:
                file = File(
                    id="FILE1",
                    path=Path(f.name),
                )
                project.ancestry.add(file)
                async with project:
                    await generate(project)
                    await assert_betty_html(project, "/file/%s/index.html" % file.id)
                    await assert_betty_json(project, "/file/%s/index.json" % file.id)

    async def test_places(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            await generate(project)
            await assert_betty_html(project, "/place/index.html")
            await assert_betty_json(project, "/place/index.json")

    async def test_place(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            place = Place(
                id="PLACE1",
                names=[PlaceName(name="one")],
            )
            project.ancestry.add(place)
            async with project:
                await generate(project)
                await assert_betty_html(project, "/place/%s/index.html" % place.id)
                await assert_betty_json(project, "/place/%s/index.json" % place.id)

    async def test_people(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            await generate(project)
            await assert_betty_html(project, "/person/index.html")
            await assert_betty_json(project, "/person/index.json")

    async def test_person(self) -> None:
        person = Person(id="PERSON1")
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.ancestry.add(person)
            async with project:
                await generate(project)
                await assert_betty_html(project, f"/person/{person.id}/index.html")
                await assert_betty_json(
                    project,
                    f"/person/{person.id}/index.json",
                )

    async def test_events(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            await generate(project)
            await assert_betty_html(project, "/event/index.html")
            await assert_betty_json(project, "/event/index.json", "eventCollection")

    async def test_event(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            event = Event(
                id="EVENT1",
                event_type=Birth(),
            )
            project.ancestry.add(event)
            async with project:
                await generate(project)
                await assert_betty_html(project, "/event/%s/index.html" % event.id)
                await assert_betty_json(
                    project, "/event/%s/index.json" % event.id, "event"
                )

    async def test_citation(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            source = Source("A Little Birdie")
            citation = Citation(
                id="CITATION1",
                source=source,
            )
            project.ancestry.add(citation, source)
            async with project:
                await generate(project)
                await assert_betty_html(
                    project, "/citation/%s/index.html" % citation.id
                )
                await assert_betty_json(
                    project, "/citation/%s/index.json" % citation.id
                )

    async def test_sources(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            await generate(project)
            await assert_betty_html(project, "/source/index.html")
            await assert_betty_json(project, "/source/index.json")

    async def test_source(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            source = Source(
                id="SOURCE1",
                name="A Little Birdie",
            )
            project.ancestry.add(source)
            async with project:
                await generate(project)
                await assert_betty_html(project, "/source/%s/index.html" % source.id)
                await assert_betty_json(project, "/source/%s/index.json" % source.id)


class TestResourceOverride:
    async def test(self) -> None:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            localized_assets_directory_path = (
                Path(project.configuration.assets_directory_path)
                / "public"
                / "localized"
            )
            localized_assets_directory_path.mkdir(parents=True)
            async with aiofiles.open(
                str(localized_assets_directory_path / "index.html.j2"), "w"
            ) as f:
                await f.write("{% block page_content %}Betty was here{% endblock %}")
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path / "index.html"
                ) as f:
                    assert "Betty was here" in await f.read()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="lxml cannot be installed directly onto vanilla Windows.",
)
class TestSitemapGenerate:
    async def test_validate(self) -> None:
        from lxml import etree

        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            await generate(project)
            schema_doc = etree.parse(
                Path(__file__).parent / "test_generate_assets" / "sitemap.xsd"
            )
            schema = etree.XMLSchema(schema_doc)
            sitemap_doc = etree.parse(
                project.configuration.www_directory_path / "sitemap.xml"
            )
            schema.validate(sitemap_doc)


class TestGenerateSiteEvent:
    async def test_job_context(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            job_context = GenerationContext(project)
            sut = GenerateSiteEvent(job_context)
            assert sut.project is project
            assert sut.job_context is job_context
