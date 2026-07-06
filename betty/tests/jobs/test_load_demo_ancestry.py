import pytest

from betty.copyright_notice import CopyrightNotice
from betty.jobs.load_demo_ancestry import LoadDemoAncestry
from betty.license import License
from betty.project import Project
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestLoadDemoAncestry:
    async def test_do(self, isolated_project: Project) -> None:
        await do(
            LoadDemoAncestry(
                project=isolated_project,
                streetmix_copyright_notice=CopyrightNotice(),
                streetmix_license=License(),
            )
        )
        assert len(isolated_project.ancestry)
