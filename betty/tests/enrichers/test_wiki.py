from __future__ import annotations

from typing import TYPE_CHECKING

from betty.enrichers.wiki import Wiki, WikiData
from betty.entities.link import Link
from betty.load import load
from betty.project import Project
from betty.test_utils.data import DataTestBase

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import NewIsolatedProject


class TestWiki:
    async def test_enrich(
        self, mocker: MockerFixture, new_isolated_project: NewIsolatedProject
    ) -> None:
        m_populate_ancestry = mocker.patch(
            "betty.jobs.populate_wiki_entity.PopulateWikiEntity.do"
        )

        async with new_isolated_project() as project:
            Project.enrichers.add_init_plugins(project, Wiki)
            async with project:
                entity = Link("https://example.com")
                project.ancestry.add(entity)
                await load(project)

            m_populate_ancestry.assert_awaited_once()


class TestWikiData(DataTestBase[WikiData]):
    sut_cls = WikiData
