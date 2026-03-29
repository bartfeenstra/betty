from __future__ import annotations

from typing import TYPE_CHECKING

from betty.load import load
from betty.plugins.enricher.wiki import Wiki
from betty.plugins.entity.link import Link

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import IsolatedProjectFactory


class TestWiki:
    async def test_enrich(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_populate_ancestry = mocker.patch(
            "betty.plugins.enricher.wiki.jobs.PopulateEntity.do"
        )

        async with isolated_project_factory(service_plugins=[Wiki]) as project:
            entity = Link("https://example.com")
            project.ancestry.add(entity)
            await load(project)

            m_populate_ancestry.assert_awaited_once()
