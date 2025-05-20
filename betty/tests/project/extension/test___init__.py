from betty.app import App
from betty.event_dispatcher import EventHandlerRegistry
from betty.project import Project
from betty.test_utils.project.extension import DummyExtension


class TestExtension:
    async def test_project__with___init__(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = DummyExtension(project)
            assert sut.project is project

    async def test_project__with_new(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            assert sut.project is project

    async def test_register_event_handlers(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            sut.register_event_handlers(EventHandlerRegistry())
