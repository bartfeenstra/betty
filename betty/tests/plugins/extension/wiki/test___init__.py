from __future__ import annotations

from typing import TYPE_CHECKING

from betty.plugins.enricher.wiki import Wiki

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestWiki:
    async def test_client(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(service_plugins=[Wiki]) as project:
            extensions = await project.extensions
            wikipedia = extensions[Wiki]
            await wikipedia.client
