from typing import Set, Type, Any

from betty.app import App
from betty.app.extension import Extension, ListExtensions, ExtensionDispatcher, build_extension_type_graph, \
    discover_extension_types
from betty.asyncio import sync
from betty.tests import TestCase


class ExtensionTest(TestCase):
    def test_depends_on(self):
        self.assertEqual(set(), Extension.depends_on())

    def test_comes_after(self):
        self.assertEqual(set(), Extension.comes_after())

    def test_comes_before(self):
        self.assertEqual(set(), Extension.comes_before())


class ExtensionDispatcherTest(TestCase):
    class _Multiplier:
        async def multiply(self, term: int) -> Any:
            raise NotImplementedError

    class _MultiplyingExtension(_Multiplier, Extension):
        def __init__(self, app: App, multiplier: int):
            super().__init__(app)
            self._multiplier = multiplier

        async def multiply(self, term: int) -> Any:
            return self._multiplier * term

    @sync
    async def test(self) -> None:
        with App() as app:
            extensions = ListExtensions([
                [self._MultiplyingExtension(app, 1), self._MultiplyingExtension(app, 3)],
                [self._MultiplyingExtension(app, 2), self._MultiplyingExtension(app, 4)]
            ])
            sut = ExtensionDispatcher(extensions)
            actual_returned_somethings = await sut.dispatch(self._Multiplier)(3)
            expected_returned_somethings = [3, 9, 6, 12]
            self.assertEqual(expected_returned_somethings, actual_returned_somethings)


class BuildExtensionTypeGraphTest(TestCase):
    def test_without_extension_types(self) -> None:
        self.assertEqual({}, build_extension_type_graph(set()))

    def test_with_isolated_extension_types(self) -> None:
        class IsolatedExtensionOne(Extension):
            pass

        class IsolatedExtensionTwo(Extension):
            pass
        extension_types = {
            IsolatedExtensionOne,
            IsolatedExtensionTwo,
        }
        expected = {
            IsolatedExtensionOne: set(),
            IsolatedExtensionTwo: set(),
        }
        self.assertEqual(expected, build_extension_type_graph(extension_types))

    def test_with_unknown_dependencies(self) -> None:
        class IsDependencyExtension(Extension):
            pass

        class HasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> Set[Type[Extension]]:
                return {IsDependencyExtension}
        extension_types = {
            HasDependencyExtension,
        }
        expected = {
            HasDependencyExtension: {IsDependencyExtension},
            IsDependencyExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))

    def test_with_known_dependencies(self) -> None:
        class IsDependencyExtension(Extension):
            pass

        class HasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> Set[Type[Extension]]:
                return {IsDependencyExtension}
        extension_types = {
            HasDependencyExtension,
            IsDependencyExtension,
        }
        expected = {
            HasDependencyExtension: {IsDependencyExtension},
            IsDependencyExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))

    def test_with_nested_dependencies(self) -> None:
        class IsDependencyExtension(Extension):
            pass

        class IsAndHasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> Set[Type[Extension]]:
                return {IsDependencyExtension}

        class HasDependencyExtension(Extension):
            @classmethod
            def depends_on(cls) -> Set[Type[Extension]]:
                return {IsAndHasDependencyExtension}
        extension_types = {
            HasDependencyExtension,
        }
        expected = {
            IsAndHasDependencyExtension: {IsDependencyExtension},
            HasDependencyExtension: {IsAndHasDependencyExtension},
            IsDependencyExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))

    def test_with_unknown_comes_after(self) -> None:
        class ComesBeforeExtension(Extension):
            pass

        class ComesAfterExtension(Extension):
            @classmethod
            def comes_after(cls) -> Set[Type[Extension]]:
                return {ComesBeforeExtension}
        extension_types = {
            ComesAfterExtension,
        }
        expected = {
            ComesAfterExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))

    def test_with_known_comes_after(self) -> None:
        class ComesBeforeExtension(Extension):
            pass

        class ComesAfterExtension(Extension):
            @classmethod
            def comes_after(cls) -> Set[Type[Extension]]:
                return {ComesBeforeExtension}
        extension_types = {
            ComesBeforeExtension,
            ComesAfterExtension,
        }
        expected = {
            ComesAfterExtension: {ComesBeforeExtension},
            ComesBeforeExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))

    def test_with_unknown_comes_before(self) -> None:
        class ComesAfterExtension(Extension):
            pass

        class ComesBeforeExtension(Extension):
            @classmethod
            def comes_before(cls) -> Set[Type[Extension]]:
                return {ComesAfterExtension}
        extension_types = {
            ComesBeforeExtension,
        }
        expected = {
            ComesBeforeExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))

    def test_with_known_comes_before(self) -> None:
        class ComesAfterExtension(Extension):
            pass

        class ComesBeforeExtension(Extension):
            @classmethod
            def comes_before(cls) -> Set[Type[Extension]]:
                return {ComesAfterExtension}
        extension_types = {
            ComesAfterExtension,
            ComesBeforeExtension,
        }
        expected = {
            ComesAfterExtension: {ComesBeforeExtension},
            ComesBeforeExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))


class DiscoverExtensionTypesTest(TestCase):
    def test(self):
        extension_types = discover_extension_types()
        self.assertLessEqual(1, len(extension_types))
        for extension_type in extension_types:
            self.assertTrue(issubclass(extension_type, Extension))
