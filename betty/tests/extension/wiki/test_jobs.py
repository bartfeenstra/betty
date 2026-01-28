from pytest_mock import MockerFixture

from betty.ancestry.link import Link
from betty.app import App
from betty.extension.wiki import Wiki
from betty.extension.wiki.jobs import PopulateEntity
from betty.project import Project
from betty.project.job import ProjectContext
from betty.project.load.jobs import PopulateLink
from betty.test_utils.job import do
from betty.test_utils.model import DummyEntityOne


class TestPopulateEntity:
    async def test_do(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        entity = DummyEntityOne()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Wiki)
            async with project:
                await do(ProjectContext(project), PopulateEntity(entity))
        m_populate.assert_awaited_once_with(entity)

    async def test_do__with_link(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        link = Link("https://en.wikipedia.org/wiki/Amsterdam")
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Wiki)
            async with project:
                await do(
                    ProjectContext(project), PopulateLink(link), PopulateEntity(link)
                )
        m_populate.assert_awaited_once_with(link)
