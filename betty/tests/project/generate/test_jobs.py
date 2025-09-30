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
from betty.locale.localizable import Plain
from betty.model import Entity
from betty.openapi import SpecificationSchema
from betty.project import Project, ProjectContext
from betty.project.config import LocaleConfiguration
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
from betty.string import kebab_case_to_lower_camel_case
from betty.test_utils.jinja2 import assert_betty_html, assert_betty_json
from betty.test_utils.job import do


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
    async def test_do(self, entity_type: type[Entity], new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateEntityTypesHtml())

            await assert_betty_html(project, f"/{entity_type.plugin.id}/index.html")


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
    async def test_do(self, entity_type: type[Entity], new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateEntityTypesJson())

            await assert_betty_json(
                project,
                f"/{entity_type.plugin.id}/index.json",
                f"{kebab_case_to_lower_camel_case(entity_type.plugin.id)}EntityCollectionResponse",
            )


class TestGenerateEntitiesHtml:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="ID"),
            Event(id="ID"),
            File(Path(__file__), id="ID"),
            Note(Plain(""), id="ID"),
            Person(id="ID"),
            Place(id="ID"),
            Source(id="ID"),
        ],
    )
    async def test_do(self, entity: Entity, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesHtml())

                await assert_betty_html(
                    project, f"/{entity.plugin.id}/{entity.id}/index.html"
                )

    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source()),
            Citation(source=Source(), id="ID", private=True),
            Enclosure(enclosee=Place(), encloser=Place()),
            Event(),
            Event(id="ID", private=True),
            File(Path(__file__)),
            File(Path(__file__), id="ID", private=True),
            Note(Plain("")),
            Note(Plain(""), id="ID", private=True),
            Person(),
            Person(id="ID", private=True),
            PersonName(individual="Jane", person=Person()),
            Presence(Person(), UnknownPresenceRole(), Event()),
            Place(),
            Place(id="ID", private=True),
            Source(),
            Source(id="ID", private=True),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesHtml())

                assert not (
                    project.configuration.www_directory_path
                    / entity.plugin.id
                    / entity.id
                    / "index.html"
                ).exists()


class TestGenerateEntitiesJson:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="ID"),
            Event(id="ID"),
            File(Path(__file__), id="ID"),
            Note(Plain(""), id="ID"),
            Person(id="ID"),
            Place(id="ID"),
            Source(id="ID"),
        ],
    )
    async def test_do(self, entity: Entity, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesJson())

                await assert_betty_json(
                    project,
                    f"/{entity.plugin.id}/{entity.id}/index.json",
                    f"{kebab_case_to_lower_camel_case(entity.plugin.id)}Entity",
                )

    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source()),
            Enclosure(enclosee=Place(), encloser=Place()),
            Event(),
            File(Path(__file__)),
            Note(Plain("")),
            Person(),
            PersonName(individual="Jane", person=Person()),
            Presence(Person(), UnknownPresenceRole(), Event()),
            Place(),
            Source(),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(entity)
            async with project:
                await do(ProjectContext(project), GenerateEntitiesJson())

                assert not (
                    project.configuration.www_directory_path
                    / entity.plugin.id
                    / entity.id
                    / "index.json"
                ).exists()


class TestGenerateSitemap:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateSitemap())

            schema_doc = etree.parse(
                Path(__file__).parent / "test_jobs_assets" / "sitemap.xsd"
            )
            schema = etree.XMLSchema(schema_doc)
            sitemap_doc = etree.parse(
                project.configuration.www_directory_path / "sitemap.xml"
            )
            schema.validate(sitemap_doc)


class TestGenerateStaticPublicAssets:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
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
                await do(ProjectContext(project), GenerateStaticPublicAssets())

                async with aiofiles.open(
                    await assert_betty_html(project, "/index.html")
                ) as f:
                    meta_redirect = (
                        '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
                    )
                    assert meta_redirect in await f.read()


class TestGenerateLocalizedPublicAssets:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
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
                await do(
                    ProjectContext(project),
                    GenerateStaticPublicAssets(),
                    GenerateLocalizedPublicAssets(),
                )

                await assert_betty_html(project, "/nl/index.html")
                await assert_betty_html(project, "/en/index.html")


class TestGenerateRobotsTxt:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateRobotsTxt())

            assert (project.configuration.www_directory_path / "robots.txt").is_file()


class TestGenerateOpenApi:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateOpenApi())

            with open(
                project.configuration.www_directory_path / "api" / "index.json"
            ) as f:
                SpecificationSchema().validate(json.loads(f.read()))


class TestGenerateJsonSchema:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateJsonSchema())

            with open(project.configuration.www_directory_path / "schema.json") as f:
                JsonSchemaSchema().validate(json.loads(f.read()))


class TestGenerateFavicon:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateFavicon())

            assert (project.configuration.www_directory_path / "favicon.ico").is_file()


class TestGenerateJsonErrorResponses:
    async def test_do(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await do(ProjectContext(project), GenerateJsonErrorResponses())

            for code in [401, 403, 404]:
                await assert_betty_json(project, f".error/{code}.json", "errorResponse")
