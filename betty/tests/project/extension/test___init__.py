from abc import ABC, abstractmethod
from typing import Any
from typing_extensions import override

from betty.app import App
from betty.locale.localizable import Localizable, plain
from betty.plugin import PluginId
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension import (
    Extension,
    ListExtensions,
    ExtensionDispatcher,
    build_extension_type_graph,
    ExtensionTypeGraph,
)
import pytest
from pytest_mock import MockerFixture


class DummyExtension(Extension):
    @classmethod
    def plugin_id(cls) -> PluginId:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain(cls.__name__)


class TestExtension:
    async def test_depends_on(self) -> None:
        assert set() == Extension.depends_on()

    async def test_comes_after(self) -> None:
        assert set() == Extension.comes_after()

    async def test_comes_before(self) -> None:
        assert set() == Extension.comes_before()


class TestExtensionDispatcher:
    class _Multiplier(ABC):
        @abstractmethod
        async def multiply(self, term: int) -> Any:
            pass

    class _MultiplyingExtension(_Multiplier, DummyExtension):
        def __init__(self, project: Project, multiplier: int):
            super().__init__(project)
            self._multiplier = multiplier

        @override
        async def multiply(self, term: int) -> Any:
            return self._multiplier * term

    async def test(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            extensions = ListExtensions(
                [
                    [
                        self._MultiplyingExtension(project, 1),
                        self._MultiplyingExtension(project, 3),
                    ],
                    [
                        self._MultiplyingExtension(project, 2),
                        self._MultiplyingExtension(project, 4),
                    ],
                ]
            )
            sut = ExtensionDispatcher(extensions)
            actual_returned_somethings = await sut.dispatch(self._Multiplier)(3)
            expected_returned_somethings = [3, 9, 6, 12]
            assert expected_returned_somethings == actual_returned_somethings


class IsDependencyExtension(DummyExtension):
    pass


class HasDependencyExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginId]:
        return {IsDependencyExtension.plugin_id()}


class IsAndHasDependencyExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginId]:
        return {IsDependencyExtension.plugin_id()}


class ComesBeforeTargetExtension(DummyExtension):
    pass


class HasComesBeforeExtension(DummyExtension):
    @classmethod
    def comes_before(cls) -> set[PluginId]:
        return {ComesBeforeTargetExtension.plugin_id()}


class ComesAfterTargetExtension(DummyExtension):
    pass


class HasComesAfterExtension(DummyExtension):
    @classmethod
    def comes_after(cls) -> set[PluginId]:
        return {ComesAfterTargetExtension.plugin_id()}


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
