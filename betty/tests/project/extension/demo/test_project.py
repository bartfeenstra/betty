from __future__ import annotations

from typing import TYPE_CHECKING

from betty.project import Project, ProjectContext
from betty.project.extension.demo import Demo
from betty.project.extension.demo.jobs import LoadAncestry
from betty.project.extension.demo.project import create_project
from betty.test_utils.job import do
from betty.test_utils.project.extension.demo.project import (
    demo_project_fetcher,  # noqa F401
)

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App
    from betty.fetch import Fetcher
    from betty.test_utils.conftest import NewTemporaryAppFactory


async def test_create_project(new_temporary_app: App, tmp_path: Path) -> None:
    project = await create_project(new_temporary_app, tmp_path)
    async with project:
        assert project.configuration.project_directory_path == tmp_path
        assert Demo in await project.extensions


async def test_load_ancestry(
    demo_project_fetcher: Fetcher,  # noqa F811
    new_temporary_app_factory: NewTemporaryAppFactory,
) -> None:
    async with (
        new_temporary_app_factory(fetcher=demo_project_fetcher) as app,
        app,
        Project.new_temporary(app) as project,
        project,
    ):
        context = ProjectContext(project)
        await do(context, LoadAncestry())

        assert len(project.ancestry)
