from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.extension.demo import Demo
from betty.extension.demo.jobs import LoadAncestry
from betty.extension.demo.project import create_project
from betty.project import Project
from betty.project.job import ProjectContext
from betty.test_utils.job import do

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App
    from betty.test_utils.conftest import IsolatedAppFactory


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_create_project(isolated_app: App, tmp_path: Path) -> None:
    project = await create_project(isolated_app, tmp_path)
    async with project:
        assert project.project_directory_path == tmp_path
        assert Demo in await project.extensions


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_load_ancestry(isolated_app_factory: IsolatedAppFactory) -> None:
    async with isolated_app_factory() as app, app, Project.new_isolated(app) as project:
        project.configuration.extensions.enable(Demo)
        async with project:
            context = ProjectContext(project)
            await do(context, LoadAncestry())

            assert len(project.ancestry)
