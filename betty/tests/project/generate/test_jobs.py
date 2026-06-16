import json
from pathlib import Path

import pytest
from lxml import etree

from betty.entities.citation import Citation
from betty.entities.enclosure import Enclosure
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.entity import Entity
from betty.json_schema import JsonSchemaSchema
from betty.openapi.schema import SpecificationSchema
from betty.privacy import Privacy
from betty.project import Project, ProjectLocale
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
from betty.roles.unknown import Unknown as UnknownRole
from betty.string import kebab_case_to_lower_camel_case
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.jinja import assert_betty_html, assert_betty_json
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
    async def test_do(
        self,
        entity_type: type[Entity],
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with isolated_project_factory(
            generate_entity_list_html=[entity_type]
        ) as project:
            await do(GenerateEntityTypesHtml(project=project))

            await assert_betty_html(project, f"/{entity_type.plugin().id}/index.html")

    async def test_do__with_pager(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            generate_entity_list_html=[Place],
        ) as project:
            place_one = Place(id="my-first-place")
            place_two = Place(id="my-second-place")
            project.ancestry.add(place_one, place_two)
            await do(GenerateEntityTypesHtml(per_page=1, project=project))

            await assert_betty_html(project, "/place/page--2/index.html")


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
    async def test_do(
        self, entity_type: type[Entity], isolated_project: Project
    ) -> None:
        await do(GenerateEntityTypesJson(project=isolated_project))

        await assert_betty_json(
            isolated_project,
            f"/{entity_type.plugin().id}/index.json",
            f"{kebab_case_to_lower_camel_case(entity_type.plugin().id)}EntityCollectionResponse",
        )


class TestGenerateEntitiesHtml:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="my-first-citation"),
            Event(id="my-first-event"),
            File(__file__, id="my-first-file"),
            Note(DUMMY_LOCALIZABLE, id="my-first-note"),
            Person(id="my-first-person"),
            Place(id="my-first-place"),
            Source(id="my-first-source"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_project: Project) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesHtml(project=isolated_project))

        await assert_betty_html(
            isolated_project, f"/{entity.plugin().id}/{entity.id}/index.html"
        )

    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source()),
            Citation(source=Source(), id="my-first-citation", privacy=Privacy.PRIVATE),
            Enclosure(enclosee=Place(), encloser=Place()),
            Event(),
            Event(id="my-first-event", privacy=Privacy.PRIVATE),
            File(__file__),
            File(__file__, id="my-first-file", privacy=Privacy.PRIVATE),
            Note(DUMMY_LOCALIZABLE),
            Note(DUMMY_LOCALIZABLE, id="my-first-note", privacy=Privacy.PRIVATE),
            Person(),
            Person(id="my-first-person", privacy=Privacy.PRIVATE),
            PersonName(individual="Jane", person=Person()),
            Presence(Person(), UnknownRole(), Event()),
            Place(),
            Place(id="my-first-place", privacy=Privacy.PRIVATE),
            Source(),
            Source(id="my-first-source", privacy=Privacy.PRIVATE),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, isolated_project: Project
    ) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesHtml(project=isolated_project))

        assert not (
            isolated_project.www_directory
            / entity.plugin().id
            / entity.id
            / "index.html"
        ).exists()


class TestGenerateEntitiesJson:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="my-first-citation"),
            Event(id="my-first-event"),
            File(__file__, id="my-first-file"),
            Note(DUMMY_LOCALIZABLE, id="my-first-note"),
            Person(id="my-first-person"),
            Place(id="my-first-place"),
            Source(id="my-first-source"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_project: Project) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesJson(project=isolated_project))

        await assert_betty_json(
            isolated_project,
            f"/{entity.plugin().id}/{entity.id}/index.json",
            f"{kebab_case_to_lower_camel_case(entity.plugin().id)}Entity",
        )


class TestGenerateSitemap:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateSitemap(project=isolated_project))

        schema_doc = etree.parse(
            Path(__file__).parent / "test_jobs_assets" / "sitemap.xsd"
        )
        schema = etree.XMLSchema(schema_doc)
        sitemap_doc = etree.parse(isolated_project.www_directory / "sitemap.xml")
        schema.validate(sitemap_doc)


class TestGenerateStaticPublicAssets:
    async def test_do(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        async with isolated_project_factory(
            locales=[
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
            ],
        ) as project:
            await do(GenerateStaticPublicAssets(project=project))

            with open(
                await assert_betty_html(project, "/index.html"), encoding="utf-8"
            ) as f:
                meta_redirect = (
                    '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
                )
                assert meta_redirect in f.read()


class TestGenerateLocalizedPublicAssets:
    async def test_do(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        async with isolated_project_factory(
            locales=[
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
            ],
        ) as project:
            await do(
                GenerateStaticPublicAssets(project=project),
                GenerateLocalizedPublicAssets(project=project),
            )

            await assert_betty_html(project, "/nl/index.html")
            await assert_betty_html(project, "/en/index.html")


class TestGenerateRobotsTxt:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateRobotsTxt(project=isolated_project))

        assert (isolated_project.www_directory / "robots.txt").is_file()


class TestGenerateOpenApi:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateOpenApi(project=isolated_project))

        with open(
            isolated_project.www_directory / "api" / "index.json", encoding="utf-8"
        ) as f:
            SpecificationSchema().validate(json.loads(f.read()))


class TestGenerateJsonSchema:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateJsonSchema(project=isolated_project))

        with open(
            isolated_project.www_directory / "schema.json", encoding="utf-8"
        ) as f:
            JsonSchemaSchema().validate(json.loads(f.read()))


class TestGenerateFavicon:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateFavicon(project=isolated_project))

        assert (isolated_project.www_directory / "favicon.ico").is_file()


class TestGenerateJsonErrorResponses:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateJsonErrorResponses(project=isolated_project))

        for code in [401, 403, 404]:
            await assert_betty_json(
                isolated_project, f".error/{code}.json", "errorResponse"
            )
