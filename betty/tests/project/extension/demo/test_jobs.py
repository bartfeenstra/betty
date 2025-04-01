from betty.fetch import Fetcher
from betty.project import Project, ProjectContext
from betty.project.extension.demo.jobs import LoadAncestry
from betty.test_utils.conftest import NewTemporaryAppFactory
from betty.test_utils.job import do
from betty.test_utils.project.extension.demo.project import (
    demo_project_fetcher,  # noqa F401
)


class TestLoadAncestry:
    async def test_do(
        self,
        demo_project_fetcher: Fetcher,  # noqa F811
        new_temporary_app_factory: NewTemporaryAppFactory,
    ) -> None:
        async with (
            new_temporary_app_factory(fetcher=demo_project_fetcher) as app,
            app,
            Project.new_temporary(app) as project,
            project,
        ):
            await do(ProjectContext(project), LoadAncestry())
            assert len(project.ancestry)
