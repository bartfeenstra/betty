from __future__ import annotations

from typing import TYPE_CHECKING

from betty.plugins.entity.link import Link
from betty.plugins.extension.wiki import Wiki
from betty.project.load import load

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import IsolatedProjectFactory


class TestWiki:
    async def test_post_load(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_populate_ancestry = mocker.patch(
            "betty.plugins.extension.wiki.jobs.PopulateEntity.do"
        )

        async with isolated_project_factory(service_plugins=[Wiki]) as project:
            entity = Link("https://example.com")
            project.ancestry.add(entity)
            await load(project)

            m_populate_ancestry.assert_awaited_once()

    async def test_client(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(service_plugins=[Wiki]) as project:
            extensions = await project.extensions
            wikipedia = extensions[Wiki]
            await wikipedia.client
