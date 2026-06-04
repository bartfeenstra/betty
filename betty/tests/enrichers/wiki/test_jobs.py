from pytest_mock import MockerFixture

from betty.enrichers.populate_links import PopulateLink
from betty.enrichers.wiki.jobs import PopulateEntity
from betty.entities.link import Link
from betty.extensions.wiki import Wiki
from betty.locale.localize import default_localizer
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.job import do


class TestPopulateEntity:
    async def test_do(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        entity = DummyEntityOne()
        async with isolated_project_factory(extensions=[Wiki]) as project:
            await do(PopulateEntity(entity, project=project))
        m_populate.assert_awaited_once_with(entity)

    async def test_do__with_link(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_populate = mocker.patch("betty.wiki.populator.Populator.populate")
        link = Link("https://en.wikipedia.org/wiki/Amsterdam")
        async with isolated_project_factory(extensions=[Wiki]) as project:
            await do(
                PopulateLink(
                    link,
                    http_client=await project.upstream.http_client,
                    localizers=[default_localizer],
                ),
                PopulateEntity(link, project=project),
            )
        m_populate.assert_awaited_once_with(link)
