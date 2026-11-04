from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project, ProjectLocale
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.job import do


class TestGenerateWwwDirectory:
    async def test_do__monolingual(self, isolated_project: Project) -> None:
        await do(GenerateWwwDirectory(project=isolated_project))
        assert isolated_project.www_directory.is_dir()

    async def test_do__multilingual(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with (
            isolated_project_factory(
                locales=[
                    ProjectLocale("nl-NL"),
                    ProjectLocale("en-US", alias="en"),
                ],
            ) as project,
            project,
        ):
            await do(GenerateWwwDirectory(project=project))
            assert (project.www_directory / "en").is_dir()
            assert (project.www_directory / "nl-NL").is_dir()
