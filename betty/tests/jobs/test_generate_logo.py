from betty.jobs.generate_logo import GenerateLogo
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.job import do


class TestGenerateLogo:
    async def test_do(self, isolated_project: Project) -> None:
        DummyEntityOne()
        await do(
            GenerateWwwDirectory(project=isolated_project),
            GenerateLogo(project=isolated_project),
        )
        assert (isolated_project.www_directory / "logo.png").is_file()
