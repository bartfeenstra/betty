from betty.jobs.generate_robots_txt import GenerateRobotsTxt
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.job import do


class TestGenerateRobotsTxt:
    async def test_do(self, isolated_project: Project) -> None:
        await do(
            GenerateWwwDirectory(project=isolated_project),
            GenerateRobotsTxt(project=isolated_project),
        )

        assert (isolated_project.www_directory / "robots.txt").is_file()
