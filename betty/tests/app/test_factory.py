from betty.app import App
from betty.app.factory import AppDependentSelfFactory, CallbackAppDependentFactory
from betty.project import Project


class TestAppDependentSelfFactory:
    async def test_requirement__with_global(self) -> None:
        assert await AppDependentSelfFactory.requirement(None) is not None

    async def test_requirement__with_app(self, isolated_app: App) -> None:
        assert await AppDependentSelfFactory.requirement(isolated_app) is None

    async def test_requirement__with_project(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            assert await AppDependentSelfFactory.requirement(project) is None


class TestCallbackAppDependentFactory:
    async def test_new_for_app(self, isolated_app: App) -> None:
        sut = CallbackAppDependentFactory(lambda app: app)
        assert await sut.new_for_app(isolated_app) is isolated_app
