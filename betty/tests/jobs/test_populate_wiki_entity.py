from pytest_mock import MockerFixture

from betty.entities.link import Link
from betty.jobs.populate_link import PopulateLink
from betty.jobs.populate_wiki_entity import PopulateWikiEntity
from betty.localizer import default_localizer
from betty.project import Project
from betty.service_providers.wiki import Wiki
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.job import do


class TestPopulateWikiEntity:
    async def test_do(
        self, mocker: MockerFixture, new_isolated_project: NewIsolatedProject
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        entity = DummyEntityOne()
        async with new_isolated_project() as project:
            Project.service_providers.add_init_plugins(project, Wiki)
            async with project:
                await do(PopulateWikiEntity(entity, project=project))
        m_populate.assert_awaited_once_with(entity)

    async def test_do__with_link(
        self, mocker: MockerFixture, new_isolated_project: NewIsolatedProject
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        link = Link("https://en.wikipedia.org/wiki/Amsterdam")
        async with new_isolated_project() as project:
            Project.service_providers.add_init_plugins(project, Wiki)
            async with project:
                await do(
                    PopulateLink(
                        link,
                        http_client=await project.upstream.http_client,
                        localizers=[default_localizer],
                    ),
                    PopulateWikiEntity(link, project=project),
                )
        m_populate.assert_awaited_once_with(link)
