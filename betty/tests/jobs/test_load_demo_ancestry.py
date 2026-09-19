import pytest
from pytest_mock import MockerFixture

from betty.copyright_notice import CopyrightNotice
from betty.jobs.load_demo_ancestry import LoadDemoAncestry
from betty.license import License
from betty.project import Project
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestLoadDemoAncestry:
    async def test_do(self, isolated_project: Project, mocker: MockerFixture) -> None:
        await do(
            LoadDemoAncestry(
                project=isolated_project,
                streetmix_copyright_notice=mocker.Mock(spec=CopyrightNotice),
                streetmix_license=mocker.Mock(spec=License),
            )
        )
        assert len(isolated_project.ancestry)
