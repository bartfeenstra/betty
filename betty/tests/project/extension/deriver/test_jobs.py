from pytest_mock import MockerFixture

from betty.app import App
from betty.project import Project, ProjectContext
from betty.project.extension.deriver.jobs import DeriveAncestry
from betty.test_utils.job import do


class TestDeriveAncestry:
    async def test_do(
        self,
        mocker: MockerFixture,
        temporary_app: App,
    ) -> None:
        m_derive = mocker.patch("betty.deriver.Deriver.derive")
        async with (
            Project.new_temporary(temporary_app) as project,
            project,
        ):
            await do(ProjectContext(project), DeriveAncestry())
        m_derive.assert_awaited_once()
