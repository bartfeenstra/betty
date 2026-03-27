from pytest_mock import MockerFixture

from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.entity.link import Link
from betty.plugins.extension.wiki import Wiki
from betty.plugins.extension.wiki.jobs import PopulateEntity
from betty.project.load.jobs import PopulateLink
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.job import do
from betty.test_utils.model import DummyEntityOne


class TestPopulateEntity:
    async def test_do(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        entity = DummyEntityOne()
        async with isolated_project_factory(service_plugins=[Wiki]) as project:
            await do(PopulateEntity(entity, project=project))
        m_populate.assert_awaited_once_with(entity)

    async def test_do__with_link(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        link = Link("https://en.wikipedia.org/wiki/Amsterdam")
        async with isolated_project_factory(service_plugins=[Wiki]) as project:
            await do(
                PopulateLink(
                    link,
                    http_client=await project.upstream.http_client,
                    localizers=[DEFAULT_LOCALIZER],
                ),
                PopulateEntity(link, project=project),
            )
        m_populate.assert_awaited_once_with(link)
