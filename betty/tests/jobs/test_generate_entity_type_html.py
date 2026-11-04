import pytest

from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.entity import Entity
from betty.jobs.generate_entity_type import GenerateEntityType
from betty.jobs.generate_entity_type_html import GenerateEntityTypeHtml
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.jinja import assert_betty_html
from betty.test_utils.job import do


class TestGenerateEntityTypeHtml:
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
        async with (
            isolated_project_factory(
                generate_entity_list_html=[entity_type]
            ) as project,
            project,
        ):
            await do(
                GenerateWwwDirectory(project=project),
                GenerateEntityType(entity_type, project=project),
                GenerateEntityTypeHtml(entity_type, project=project),
            )

            await assert_betty_html(project, f"/{entity_type.definition.id}/index.html")

    async def test_do__with_pager(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with Project.new_isolated(per_page=1) as project, project:
            place_one = Place(id="my-first-place")
            place_two = Place(id="my-second-place")
            project.ancestry.add(place_one, place_two)
            await do(
                GenerateWwwDirectory(project=project),
                GenerateEntityType(Place, project=project),
                GenerateEntityTypeHtml(Place, project=project),
            )

            await assert_betty_html(project, "/place/page--2/index.html")
