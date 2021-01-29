from typing import Set, Type
from betty.extension import Extension, build_extension_type_graph
from betty.tests import TestCase


class ExtensionTest(TestCase):
    def test_depends_on(self):
        self.assertEquals(set(), Extension.depends_on())

    def test_comes_after(self):
        self.assertEquals(set(), Extension.comes_after())

    def test_comes_before(self):
        self.assertEquals(set(), Extension.comes_before())


class BuildExtensionTypeGraphTest(TestCase):
    def test_without_extension_types(self) -> None:
        self.assertEquals({}, build_extension_type_graph(set()))

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
        self.assertEquals(expected, build_extension_type_graph(extension_types))

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
            IsDependencyExtension: {HasDependencyExtension},
            HasDependencyExtension: set(),
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
            IsDependencyExtension: {HasDependencyExtension},
            HasDependencyExtension: set(),
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
            IsDependencyExtension: {IsAndHasDependencyExtension},
            IsAndHasDependencyExtension: {HasDependencyExtension},
            HasDependencyExtension: set(),
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
            ComesBeforeExtension: {ComesAfterExtension},
            ComesAfterExtension: set(),
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
            ComesBeforeExtension: {ComesAfterExtension},
            ComesAfterExtension: set(),
        }
        self.assertDictEqual(expected, dict(build_extension_type_graph(extension_types)))
