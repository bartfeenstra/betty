from betty.jobs.generate_entity_type import GenerateEntityType
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.job import do


class TestGenerateEntityType:
    async def test_do(self, isolated_project: Project) -> None:
        await do(
            GenerateWwwDirectory(project=isolated_project),
            GenerateEntityType(DummyEntityOne, project=isolated_project),
        )
        assert (isolated_project.www_directory / DummyEntityOne.definition.id).is_dir()
