from __future__ import annotations

from typing import TYPE_CHECKING

from betty.extensions.wiki import Wiki

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestWiki:
    async def test_client(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(extensions=[Wiki]) as project:
            wiki = await project.extensions[Wiki]
            await wiki.client
