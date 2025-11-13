from betty.app import App
from betty.project import Project
from betty.project.load import load


async def test_load__should_immutable_ancestry(temporary_app: App) -> None:
    async with Project.new_temporary(temporary_app) as project, project:
        await load(project)
        assert project.ancestry.immutable
