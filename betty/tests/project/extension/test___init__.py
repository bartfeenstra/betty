import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.event_dispatcher import EventHandlerRegistry
from betty.plugin import PluginIdentifier
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension import (
    Extension,
    build_extension_type_graph,
    ExtensionTypeGraph,
)
from betty.test_utils.project.extension import DummyExtension


class IsDependencyExtension(DummyExtension):
    pass


class HasDependencyExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {IsDependencyExtension}


class IsAndHasDependencyExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {IsDependencyExtension}


class ComesBeforeTargetExtension(DummyExtension):
    pass


class HasComesBeforeExtension(DummyExtension):
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[Extension]]:
        return {ComesBeforeTargetExtension}


class ComesAfterTargetExtension(DummyExtension):
    pass


class HasComesAfterExtension(DummyExtension):
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        return {ComesAfterTargetExtension}


class IsolatedExtensionOne(DummyExtension):
    pass


class IsolatedExtensionTwo(DummyExtension):
    pass


class TestBuildExtensionTypeGraph:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(
                IsDependencyExtension,
                HasDependencyExtension,
                IsAndHasDependencyExtension,
                ComesBeforeTargetExtension,
                HasComesBeforeExtension,
                ComesAfterTargetExtension,
                HasComesAfterExtension,
                IsolatedExtensionOne,
                IsolatedExtensionTwo,
            ),
        )

    async def test_without_extension_types(self) -> None:
        assert await build_extension_type_graph(set()) == {}

    async def test_with_isolated_extension_types(self) -> None:
        extension_types = {
            IsolatedExtensionOne,
            IsolatedExtensionTwo,
        }
        expected: ExtensionTypeGraph = {
            IsolatedExtensionOne: set(),
            IsolatedExtensionTwo: set(),
        }
        assert expected == await build_extension_type_graph(extension_types)

    async def test_with_unknown_dependencies(self) -> None:
        extension_types = {
            HasDependencyExtension,
        }
        expected: ExtensionTypeGraph = {
            HasDependencyExtension: {IsDependencyExtension},
            IsDependencyExtension: set(),
        }
        assert expected == dict(await build_extension_type_graph(extension_types))

    async def test_with_known_dependencies(self) -> None:
        extension_types = {
            HasDependencyExtension,
            IsDependencyExtension,
        }
        expected: ExtensionTypeGraph = {
            HasDependencyExtension: {IsDependencyExtension},
            IsDependencyExtension: set(),
        }
        assert expected == dict(await build_extension_type_graph(extension_types))

    async def test_with_unknown_comes_after(self) -> None:
        extension_types = {
            HasComesAfterExtension,
        }
        expected: dict[type[Extension], set[type[Extension]]] = {
            HasComesAfterExtension: set(),
        }
        assert expected == dict(await build_extension_type_graph(extension_types))

    async def test_with_known_comes_after(self) -> None:
        extension_types = {
            ComesAfterTargetExtension,
            HasComesAfterExtension,
        }
        expected: ExtensionTypeGraph = {
            HasComesAfterExtension: {ComesAfterTargetExtension},
            ComesAfterTargetExtension: set(),
        }
        assert expected == dict(await build_extension_type_graph(extension_types))

    async def test_with_unknown_comes_before(self) -> None:
        extension_types = {
            HasComesBeforeExtension,
        }
        expected: dict[type[Extension], set[type[Extension]]] = {
            HasComesBeforeExtension: set(),
        }
        assert expected == dict(await build_extension_type_graph(extension_types))

    async def test_with_known_comes_before(self) -> None:
        extension_types = {
            ComesBeforeTargetExtension,
            HasComesBeforeExtension,
        }
        expected: ExtensionTypeGraph = {
            ComesBeforeTargetExtension: {HasComesBeforeExtension},
            HasComesBeforeExtension: set(),
        }
        assert expected == dict(await build_extension_type_graph(extension_types))


class TestExtension:
    async def test_project_with___init__(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = DummyExtension(project)
            assert sut.project is project

    async def test_project_with_new_for_project(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            assert sut.project is project

    async def test_register_event_handlers(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            sut.register_event_handlers(EventHandlerRegistry())
