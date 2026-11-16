from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project, ProjectLocale
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.job import do


class TestGenerateWwwDirectory:
    async def test_do__monolingual(self, isolated_project: Project) -> None:
        await do(GenerateWwwDirectory(project=isolated_project))
        assert isolated_project.www_directory.is_dir()

    async def test_do__multilingual(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with new_isolated_project() as project:
            project.locales = [
                ProjectLocale("nl-NL"),
                ProjectLocale("en-US", alias="en"),
            ]
            async with project:
                await do(GenerateWwwDirectory(project=project))
                assert (project.www_directory / "en").is_dir()
                assert (project.www_directory / "nl-NL").is_dir()
