from __future__ import annotations

from typing import TYPE_CHECKING

from betty.project import Project
from betty.project.job import ProjectContext

if TYPE_CHECKING:
    from betty.app import App


class TestProjectContext:
    async def test_project(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = ProjectContext(project)
            assert sut.project is project
