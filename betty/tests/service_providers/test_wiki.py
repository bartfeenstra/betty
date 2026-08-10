from __future__ import annotations

from typing import TYPE_CHECKING

from betty.service_providers.wiki import Wiki

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestWiki:
    async def test_client(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(service_providers=[Wiki]) as project:
            wiki = await project.service_providers[Wiki]
            assert await wiki.client is await wiki.client

    async def test_populator(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(service_providers=[Wiki]) as project:
            wiki = await project.service_providers[Wiki]
            assert await wiki.populator is await wiki.populator
