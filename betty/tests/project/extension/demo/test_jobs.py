from betty.project import Project, ProjectContext
from betty.project.extension.demo.jobs import LoadAncestry
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.job import do
from betty.test_utils.project.extension.demo.project import (
    demo_project_aioresponses,  # noqa: F401
)


class TestLoadAncestry:
    async def test_do(
        self,
        demo_project_aioresponses: None,  # noqa: F811
        isolated_app_factory: IsolatedAppFactory,
    ) -> None:
        async with (
            isolated_app_factory() as app,
            app,
            Project.new_isolated(app) as project,
            project,
        ):
            await do(ProjectContext(project), LoadAncestry())
            assert len(project.ancestry)
