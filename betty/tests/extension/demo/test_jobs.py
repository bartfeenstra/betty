import pytest

from betty.extension.demo import Demo
from betty.extension.demo.jobs import LoadAncestry
from betty.project import Project
from betty.project.job import ProjectContext
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestLoadAncestry:
    async def test_do(self, isolated_app_factory: IsolatedAppFactory) -> None:
        async with (
            isolated_app_factory() as app,
            app,
            Project.new_isolated(app) as project,
        ):
            project.configuration.extensions.enable(Demo)
            async with project:
                await do(ProjectContext(project), LoadAncestry())
                assert len(project.ancestry)
