from betty.jobs.generate_favicon import GenerateFavicon
from betty.project import Project
from betty.test_utils.job import do


class TestGenerateFavicon:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateFavicon(project=isolated_project))

        assert (isolated_project.www_directory / "favicon.ico").is_file()
