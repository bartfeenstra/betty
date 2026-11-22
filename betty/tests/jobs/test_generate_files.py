from betty.entities.file import File
from betty.jobs.generate_entity import GenerateEntity, GenerateEntityType
from betty.jobs.generate_files import GenerateFiles, url
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.job import do


def test_url() -> None:
    file = File(__file__, id="my-first-file")
    assert url(file) == "betty-static:///file/my-first-file/file/test_generate_files.py"


class TestGenerateFiles:
    async def test_do__without_files(self, isolated_project: Project) -> None:
        await do(GenerateFiles(www_directory=isolated_project.www_directory))

    async def test_do(self, isolated_project: Project) -> None:
        file = File(__file__, id="my-first-file")
        await do(
            GenerateWwwDirectory(project=isolated_project),
            GenerateEntityType(File, project=isolated_project),
            GenerateEntity(file, project=isolated_project),
            GenerateFiles(file, www_directory=isolated_project.www_directory),
        )
        assert (
            isolated_project.www_directory
            / "file"
            / "my-first-file"
            / "file"
            / "test_generate_files.py"
        ).is_file()
