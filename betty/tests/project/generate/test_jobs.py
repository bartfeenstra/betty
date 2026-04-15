import json
from pathlib import Path

import pytest
from lxml import etree

from betty.entity import Entity
from betty.json.schema import JsonSchemaSchema
from betty.openapi.schema import SpecificationSchema
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.event import Event
from betty.plugins.entity.file import File
from betty.plugins.entity.note import Note
from betty.plugins.entity.person import Person
from betty.plugins.entity.person_name import PersonName
from betty.plugins.entity.place import Place
from betty.plugins.entity.presence import Presence
from betty.plugins.entity.source import Source
from betty.plugins.role.unknown import Unknown as UnknownRole
from betty.privacy import Privacy
from betty.project import Project, ProjectEntityType, ProjectLocale
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
            entity_types=[
                ProjectEntityType(entity_type=entity_type, generate_html_list=True)
            ],
        ) as project:
            await do(GenerateEntityTypesHtml(project=project))

            await assert_betty_html(project, f"/{entity_type.plugin().id}/index.html")

    async def test_do__with_pager(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            entity_types=[
                ProjectEntityType(entity_type=Place, generate_html_list=True)
            ],
        ) as project:
            place_one = Place(id="P1")
            place_two = Place(id="P2")
            project.ancestry.add(place_one, place_two)
            await do(GenerateEntityTypesHtml(per_page=1, project=project))

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
            Citation(source=Source(), id="ID"),
            Event(id="ID"),
            File(Path(__file__), id="ID"),
            Note(DUMMY_LOCALIZABLE, id="ID"),
            Person(id="ID"),
            Place(id="ID"),
            Source(id="ID"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_project: Project) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesHtml(project=isolated_project))

        await assert_betty_html(
            isolated_project, f"/{entity.plugin().id}/{entity.public_id}/index.html"
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
            Presence(Person(), UnknownRole(), Event()),
            Place(),
            Place(id="ID", privacy=Privacy.PRIVATE),
            Source(),
            Source(id="ID", privacy=Privacy.PRIVATE),
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
    async def test_do(self, entity: Entity, isolated_project: Project) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesJson(project=isolated_project))

        await assert_betty_json(
            isolated_project,
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
            Presence(Person(), UnknownRole(), Event()),
            Place(),
            Source(),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, isolated_project: Project
    ) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesJson(project=isolated_project))

        assert not (
            isolated_project.www_directory
            / entity.plugin().id
            / entity.public_id
            / "index.json"
        ).exists()


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
