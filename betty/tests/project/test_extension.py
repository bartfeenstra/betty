from abc import ABC, abstractmethod
from typing import Any
from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension import (
    Extension,
    ListExtensions,
    ExtensionDispatcher,
    build_extension_type_graph,
    discover_extension_types,
    ExtensionTypeGraph,
)


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

    class _MultiplyingExtension(_Multiplier, Extension):
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


class TestBuildExtensionTypeGraph:
    async def test_without_extension_types(self) -> None:
        assert build_extension_type_graph(set()) == {}

    async def test_with_isolated_extension_types(self) -> None:
        class IsolatedExtensionOne(Extension):
            pass

        class IsolatedExtensionTwo(Extension):
            pass

        extension_types = {
            IsolatedExtensionOne,
            IsolatedExtensionTwo,
        }
        expected: ExtensionTypeGraph = {
            IsolatedExtensionOne: set(),
            IsolatedExtensionTwo: set(),
        }
        assert expected == build_extension_type_graph(extension_types)

    async def test_with_unknown_dependencies(self) -> None:
        class IsDependencyExtension(Extension):
            pass

        class HasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> set[type[Extension]]:
                return {IsDependencyExtension}

        extension_types = {
            HasDependencyExtension,
        }
        expected: ExtensionTypeGraph = {
            HasDependencyExtension: {IsDependencyExtension},
            IsDependencyExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))

    async def test_with_known_dependencies(self) -> None:
        class IsDependencyExtension(Extension):
            pass

        class HasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> set[type[Extension]]:
                return {IsDependencyExtension}

        extension_types = {
            HasDependencyExtension,
            IsDependencyExtension,
        }
        expected: ExtensionTypeGraph = {
            HasDependencyExtension: {IsDependencyExtension},
            IsDependencyExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))

    async def test_with_nested_dependencies(self) -> None:
        class IsDependencyExtension(Extension):
            pass

        class IsAndHasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> set[type[Extension]]:
                return {IsDependencyExtension}

        class HasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> set[type[Extension]]:
                return {IsAndHasDependencyExtension}

        extension_types = {
            HasDependencyExtension,
        }
        expected: ExtensionTypeGraph = {
            IsAndHasDependencyExtension: {IsDependencyExtension},
            HasDependencyExtension: {IsAndHasDependencyExtension},
            IsDependencyExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))

    async def test_with_unknown_comes_after(self) -> None:
        class ComesBeforeExtension(Extension):
            pass

        class ComesAfterExtension(Extension):
            @classmethod
            def comes_after(cls) -> set[type[Extension]]:
                return {ComesBeforeExtension}

        extension_types = {
            ComesAfterExtension,
        }
        expected: dict[type[Extension], set[type[Extension]]] = {
            ComesAfterExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))

    async def test_with_known_comes_after(self) -> None:
        class ComesBeforeExtension(Extension):
            pass

        class ComesAfterExtension(Extension):
            @classmethod
            def comes_after(cls) -> set[type[Extension]]:
                return {ComesBeforeExtension}

        extension_types = {
            ComesBeforeExtension,
            ComesAfterExtension,
        }
        expected: ExtensionTypeGraph = {
            ComesAfterExtension: {ComesBeforeExtension},
            ComesBeforeExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))

    async def test_with_unknown_comes_before(self) -> None:
        class ComesAfterExtension(Extension):
            pass

        class ComesBeforeExtension(Extension):
            @classmethod
            def comes_before(cls) -> set[type[Extension]]:
                return {ComesAfterExtension}

        extension_types = {
            ComesBeforeExtension,
        }
        expected: dict[type[Extension], set[type[Extension]]] = {
            ComesBeforeExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))

    async def test_with_known_comes_before(self) -> None:
        class ComesAfterExtension(Extension):
            pass

        class ComesBeforeExtension(Extension):
            @classmethod
            def comes_before(cls) -> set[type[Extension]]:
                return {ComesAfterExtension}

        extension_types = {
            ComesAfterExtension,
            ComesBeforeExtension,
        }
        expected: ExtensionTypeGraph = {
            ComesAfterExtension: {ComesBeforeExtension},
            ComesBeforeExtension: set(),
        }
        assert expected == dict(build_extension_type_graph(extension_types))


class TestDiscoverExtensionTypes:
    async def test(self) -> None:
        extension_types = discover_extension_types()
        assert len(extension_types) >= 1
        for extension_type in extension_types:
            assert issubclass(extension_type, Extension)
