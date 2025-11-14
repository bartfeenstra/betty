from betty.app import App
from betty.project import Project
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)


class TestProjectDependentSelfFactory:
    async def test_requirement__with_global(self) -> None:
        assert await ProjectDependentSelfFactory.requirement(None) is not None

    async def test_requirement__with_app(self, temporary_app: App) -> None:
        assert await ProjectDependentSelfFactory.requirement(temporary_app) is not None

    async def test_requirement__with_project(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            assert await ProjectDependentSelfFactory.requirement(project) is None


class TestCallbackProjectDependentFactory:
    async def test_new_for_project(self, temporary_app: App) -> None:
        sut = CallbackProjectDependentFactory(lambda project: project)
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.new_for_project(project) is project
