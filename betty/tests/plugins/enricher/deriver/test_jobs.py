from pytest_mock import MockerFixture

from betty.plugins.enricher.deriver.jobs import DeriveAncestry
from betty.project import Project
from betty.test_utils.job import do


class TestDeriveAncestry:
    async def test_do(self, mocker: MockerFixture, isolated_project: Project) -> None:
        m_derive = mocker.patch("betty.deriver.Deriver.derive")
        await do(DeriveAncestry(project=isolated_project))
        m_derive.assert_awaited_once()
