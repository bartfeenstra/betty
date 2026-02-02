import json
from pathlib import Path

import aiofiles
import pytest
from lxml import etree

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Unknown as UnknownPresenceRole
from betty.ancestry.source import Source
from betty.app import App
from betty.json.schema import JsonSchemaSchema
from betty.model import Entity
from betty.openapi.schema import SpecificationSchema
from betty.privacy import Privacy
from betty.project import Project
from betty.project.config import EntityTypeConfiguration, LocaleConfiguration
from betty.project.generate.jobs import (
    GenerateEntitiesHtml,
    GenerateEntitiesJson,
    GenerateEntityTypesHtml,
    GenerateEntityTypesJson,
    GenerateFavicon,
    GenerateJsonErrorResponses,
    GenerateJsonSchema,
    GenerateLocalizedPublicAssets,
    GenerateOpenApi,
    GenerateRobotsTxt,
    GenerateSitemap,
    GenerateStaticPublicAssets,
)
from betty.project.job import ProjectContext
from betty.string import kebab_case_to_lower_camel_case
from betty.test_utils.jinja2 import assert_betty_html, assert_betty_json
from betty.test_utils.job import do
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestGenerateEntityTypesHtml:
    @pytest.mark.parametrize(
        "entity_type",
        [
            Event,
            Person,
            Place,
            Source,
        ],
    )
    async def test_do(self, entity_type: type[Entity], isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.entity_types.add(
                EntityTypeConfiguration(
                    entity_type=entity_type, generate_html_list=True
                )
            )
            async with project:
                await do(ProjectContext(project), GenerateEntityTypesHtml())

                await assert_betty_html(
                    project, f"/{entity_type.plugin().id}/index.html"
                )

    async def test_do__with_pager(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.entity_types.add(
                EntityTypeConfiguration(entity_type=Place, generate_html_list=True)
            )
            place_one = Place(id="P1")
            place_two = Place(id="P2")
            project.ancestry.add(place_one, place_two)
            async with project:
                await do(ProjectContext(project), GenerateEntityTypesHtml(per_page=1))

                await assert_betty_html(project, "/place/page-2/index.html")


class TestGenerateEntityTypesJson:
    @pytest.mark.parametrize(
        "entity_type",
        [
            Citation,
            Enclosure,
            Event,
            File,
            Note,
            Person,
            PersonName,
            Presence,
            Place,
            Source,
        ],
    )
    async def test_do(self, entity_type: type[Entity], isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateEntityTypesJson())

            await assert_betty_json(
                project,
                f"/{entity_type.plugin().id}/index.json",
                f"{kebab_case_to_lower_camel_case(entity_type.plugin().id)}EntityCollectionResponse",
            )


class TestGenerateEntitiesHtml:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="ID"),
            Event(id="ID"),
            File(Path(__file__), id="ID"),
            Note(DUMMY_LOCALIZABLE, id="ID"),
            Person(id="ID"),
            Place(id="ID"),
            Source(id="ID"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesHtml())

                await assert_betty_html(
                    project, f"/{entity.plugin().id}/{entity.public_id}/index.html"
                )

    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source()),
            Citation(source=Source(), id="ID", privacy=Privacy.PRIVATE),
            Enclosure(enclosee=Place(), encloser=Place()),
            Event(),
            Event(id="ID", privacy=Privacy.PRIVATE),
            File(Path(__file__)),
            File(Path(__file__), id="ID", privacy=Privacy.PRIVATE),
            Note(DUMMY_LOCALIZABLE),
            Note(DUMMY_LOCALIZABLE, id="ID", privacy=Privacy.PRIVATE),
            Person(),
            Person(id="ID", privacy=Privacy.PRIVATE),
            PersonName(individual="Jane", person=Person()),
            Presence(Person(), UnknownPresenceRole(), Event()),
            Place(),
            Place(id="ID", privacy=Privacy.PRIVATE),
            Source(),
            Source(id="ID", privacy=Privacy.PRIVATE),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesHtml())

                assert not (
                    project.www_directory
                    / entity.plugin().id
                    / entity.public_id
                    / "index.html"
                ).exists()


class TestGenerateEntitiesJson:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="ID"),
            Event(id="ID"),
            File(Path(__file__), id="ID"),
            Note(DUMMY_LOCALIZABLE, id="ID"),
            Person(id="ID"),
            Place(id="ID"),
            Source(id="ID"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesJson())

                await assert_betty_json(
                    project,
                    f"/{entity.plugin().id}/{entity.public_id}/index.json",
                    f"{kebab_case_to_lower_camel_case(entity.plugin().id)}Entity",
                )

    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source()),
            Enclosure(enclosee=Place(), encloser=Place()),
            Event(),
            File(Path(__file__)),
            Note(DUMMY_LOCALIZABLE),
            Person(),
            PersonName(individual="Jane", person=Person()),
            Presence(Person(), UnknownPresenceRole(), Event()),
            Place(),
            Source(),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesJson())

                assert not (
                    project.www_directory
                    / entity.plugin().id
                    / entity.public_id
                    / "index.json"
                ).exists()


class TestGenerateSitemap:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateSitemap())

            schema_doc = etree.parse(
                Path(__file__).parent / "test_jobs_assets" / "sitemap.xsd"
            )
            schema = etree.XMLSchema(schema_doc)
            sitemap_doc = etree.parse(project.www_directory / "sitemap.xml")
            schema.validate(sitemap_doc)


class TestGenerateStaticPublicAssets:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.locales = [
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
            ]

            async with project:
                await do(ProjectContext(project), GenerateStaticPublicAssets())

                async with aiofiles.open(
                    await assert_betty_html(project, "/index.html")
                ) as f:
                    meta_redirect = (
                        '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
                    )
                    assert meta_redirect in await f.read()


class TestGenerateLocalizedPublicAssets:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.locales = [
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
            ]
            async with project:
                await do(
                    ProjectContext(project),
                    GenerateStaticPublicAssets(),
                    GenerateLocalizedPublicAssets(),
                )

                await assert_betty_html(project, "/nl/index.html")
                await assert_betty_html(project, "/en/index.html")


class TestGenerateRobotsTxt:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateRobotsTxt())

            assert (project.www_directory / "robots.txt").is_file()


class TestGenerateOpenApi:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateOpenApi())

            with open(project.www_directory / "api" / "index.json") as f:
                SpecificationSchema().validate(json.loads(f.read()))


class TestGenerateJsonSchema:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateJsonSchema())

            with open(project.www_directory / "schema.json") as f:
                JsonSchemaSchema().validate(json.loads(f.read()))


class TestGenerateFavicon:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateFavicon())

            assert (project.www_directory / "favicon.ico").is_file()


class TestGenerateJsonErrorResponses:
    async def test_do(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await do(ProjectContext(project), GenerateJsonErrorResponses())

            for code in [401, 403, 404]:
                await assert_betty_json(project, f".error/{code}.json", "errorResponse")
