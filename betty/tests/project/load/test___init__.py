from betty.app import App
from betty.project import Project
from betty.project.load import load


async def test_load__should_immutable_ancestry(isolated_app: App) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        await load(project)
        assert project.ancestry.immutable
