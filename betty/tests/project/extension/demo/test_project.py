from __future__ import annotations

from betty.ancestry import Ancestry
from betty.project.extension.demo import Demo
from betty.project.extension.demo.project import create_project, load_ancestry
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.app import App


class TestCreateProject:
    async def test(self, new_temporary_app: App) -> None:
        async with create_project(new_temporary_app) as project:
            assert Demo.plugin_id() in await project.extensions


class TestLoadAncestry:
    async def test(self, new_temporary_app: App) -> None:
        ancestry = await Ancestry.new()
        await load_ancestry(ancestry)
        assert len(ancestry)
