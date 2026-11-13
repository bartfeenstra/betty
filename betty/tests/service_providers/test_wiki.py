from __future__ import annotations

from typing import TYPE_CHECKING

from betty.project import Project
from betty.service_providers.wiki import Wiki

if TYPE_CHECKING:
    from betty.test_utils.conftest import NewIsolatedProject


class TestWiki:
    async def test_client(self, new_isolated_project: NewIsolatedProject) -> None:
        async with new_isolated_project() as project:
            Project.service_providers.add_init_plugins(project, Wiki)
            async with project:
                wiki = await project.service_providers[Wiki]
                assert await wiki.client is await wiki.client

    async def test_populator(self, new_isolated_project: NewIsolatedProject) -> None:
        async with new_isolated_project() as project:
            Project.service_providers.add_init_plugins(project, Wiki)
            async with project:
                wiki = await project.service_providers[Wiki]
                assert await wiki.populator is await wiki.populator
