from __future__ import annotations

from typing import TYPE_CHECKING

from betty.project import Project
from betty.project.extension.demo import Demo
from betty.project.extension.demo.project import create_project, load_ancestry
from betty.app import App
from betty.test_utils.project.extension.demo.project import demo_project_fetcher  # noqa F401


if TYPE_CHECKING:
    from betty.fetch import Fetcher


class TestCreateProject:
    async def test(self, new_temporary_app: App) -> None:
        async with create_project(new_temporary_app) as project:
            assert Demo.plugin_id() in await project.extensions


class TestLoadAncestry:
    async def test(
        self,
        demo_project_fetcher: Fetcher,  # noqa F811
    ) -> None:
        async with (
            App.new_temporary(fetcher=demo_project_fetcher) as app,
            app,
            Project.new_temporary(app) as project,
            project,
        ):
            await load_ancestry(project)
            assert len(project.ancestry)
