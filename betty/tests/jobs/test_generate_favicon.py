from betty.jobs.generate_favicon import GenerateFavicon
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.job import do


class TestGenerateFavicon:
    async def test_do(self, isolated_project: Project) -> None:
        await do(
            GenerateWwwDirectory(project=isolated_project),
            GenerateFavicon(project=isolated_project),
        )

        assert (isolated_project.www_directory / "favicon.ico").is_file()
