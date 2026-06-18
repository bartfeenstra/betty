import pytest

from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.entity import Entity
from betty.jobs.generate_entity_types_html import GenerateEntityTypesHtml
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.jinja import assert_betty_html
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
