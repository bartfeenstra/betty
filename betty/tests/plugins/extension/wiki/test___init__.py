from __future__ import annotations

from typing import TYPE_CHECKING

from betty.plugins.entity.link import Link
from betty.plugins.extension.wiki import Wiki
from betty.project import Project
from betty.project.load import load

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.app import App


class TestWiki:
    async def test_post_load(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_populate_ancestry = mocker.patch(
            "betty.plugins.extension.wiki.jobs.PopulateEntity.do"
        )

        async with Project.new_isolated(isolated_app) as project:
            entity = Link("https://example.com")
            project.ancestry.add(entity)
            project.configuration.extensions.add(Wiki)
            async with project:
                await load(project)

            m_populate_ancestry.assert_awaited_once()

    async def test_client(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Wiki)
            async with project:
                extensions = await project.extensions
                wikipedia = extensions[Wiki]
                await wikipedia.client
