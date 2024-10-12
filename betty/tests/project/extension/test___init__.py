from graphlib import TopologicalSorter

from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.event_dispatcher import EventHandlerRegistry
from betty.plugin import PluginIdentifier
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension import sort_extension_type_graph, Extension
from betty.test_utils.project.extension import DummyExtension


class _DummyEntrypointExtension(DummyExtension):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {_DependencyExtension}

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        return {_EnabledComesAfterExtension, _DisabledComesAfterExtension}


class _DependencyExtension(DummyExtension):
    pass


class _EnabledComesAfterExtension(DummyExtension):
    pass


class _DisabledComesAfterExtension(DummyExtension):
    pass


class TestExtension:
    async def test_project_with___init__(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = DummyExtension(project)
            assert sut.project is project

    async def test_project_with_new(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            assert sut.project is project

    async def test_register_event_handlers(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            sut.register_event_handlers(EventHandlerRegistry())


class TestSortExtensionTypeGraph:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(
                _DummyEntrypointExtension,
                _DependencyExtension,
                _EnabledComesAfterExtension,
                _DisabledComesAfterExtension,
            ),
        )
        sorter = TopologicalSorter[type[Extension]]()
        await sort_extension_type_graph(
            sorter, [_DummyEntrypointExtension, _EnabledComesAfterExtension]
        )
        assert list(sorter.static_order()) == [
            _DependencyExtension,
            _EnabledComesAfterExtension,
            _DummyEntrypointExtension,
        ]
