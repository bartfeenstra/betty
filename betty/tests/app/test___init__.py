from typing import Type, List, Set

from betty.app import Extension, App, CyclicDependencyError
from betty.app.extension import ConfigurableExtension
from betty.asyncio import sync
from betty.config import Configuration as GenericConfiguration, ConfigurationError, DumpedConfiguration
from betty.project import ProjectExtensionConfiguration
from betty.tests import TestCase


class Tracker:
    async def track(self, carrier: List):
        raise NotImplementedError


class TrackableExtension(Extension, Tracker):
    async def track(self, carrier: List):
        carrier.append(self)


class NonConfigurableExtension(TrackableExtension):
    pass  # pragma: no cover


class ConfigurableExtensionConfiguration(GenericConfiguration):
    def __init__(self, check):
        super().__init__()
        self.check = check

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError
        if 'check' not in dumped_configuration:
            raise ConfigurationError
        self.check = dumped_configuration['check']

    def dump(self) -> DumpedConfiguration:
        return {
            'check': self.check
        }


class CyclicDependencyOneExtension(Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {CyclicDependencyTwoExtension}


class CyclicDependencyTwoExtension(Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {CyclicDependencyOneExtension}


class DependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class AlsoDependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class DependsOnNonConfigurableExtensionExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {DependsOnNonConfigurableExtensionExtension}


class ComesBeforeNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_before(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class ComesAfterNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class AppTest(TestCase):
    def test_extensions_with_one_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(NonConfigurableExtension))
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    def test_extensions_with_one_configurable_extension(self) -> None:
        check = 1337
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
                check=check,
            )))
            self.assertIsInstance(sut.extensions[ConfigurableExtension], ConfigurableExtension)
            self.assertEqual(check, sut.extensions[ConfigurableExtension]._configuration.check)

    @sync
    async def test_extensions_with_one_extension_with_single_chained_dependency(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(DependsOnNonConfigurableExtensionExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEqual(3, len(carrier))
            self.assertEqual(NonConfigurableExtension, type(carrier[0]))
            self.assertEqual(DependsOnNonConfigurableExtensionExtension, type(carrier[1]))
            self.assertEqual(DependsOnNonConfigurableExtensionExtensionExtension, type(carrier[2]))

    @sync
    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(DependsOnNonConfigurableExtensionExtension))
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEqual(3, len(carrier))
            self.assertEqual(NonConfigurableExtension, type(carrier[0]))
            self.assertIn(DependsOnNonConfigurableExtensionExtension, [
                type(extension) for extension in carrier])
            self.assertIn(AlsoDependsOnNonConfigurableExtensionExtension, [
                type(extension) for extension in carrier])

    def test_extensions_with_multiple_extensions_with_cyclic_dependencies(self) -> None:
        with self.assertRaises(CyclicDependencyError):
            with App() as sut:
                sut.project.configuration.extensions.add(ProjectExtensionConfiguration(CyclicDependencyOneExtension))
                sut.extensions

    @sync
    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(NonConfigurableExtension))
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEqual(2, len(carrier))
            self.assertEqual(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))
            self.assertEqual(NonConfigurableExtension, type(carrier[1]))

    @sync
    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEqual(1, len(carrier))
            self.assertEqual(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))

    @sync
    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(NonConfigurableExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEqual(2, len(carrier))
            self.assertEqual(NonConfigurableExtension, type(carrier[0]))
            self.assertEqual(ComesAfterNonConfigurableExtensionExtension, type(carrier[1]))

    @sync
    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
            carrier = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            self.assertEqual(1, len(carrier))
            self.assertEqual(ComesAfterNonConfigurableExtensionExtension, type(carrier[0]))

    def test_extensions_addition_to_configuration(self) -> None:
        with App() as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(NonConfigurableExtension))
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    def test_extensions_removal_from_configuration(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ProjectExtensionConfiguration(NonConfigurableExtension))
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            del sut.project.configuration.extensions[NonConfigurableExtension]
            self.assertNotIn(NonConfigurableExtension, sut.extensions)
