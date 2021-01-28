from pathlib import Path
from typing import List, Type, Set, Dict

from voluptuous import Schema, Required, Invalid

from betty import extension
from betty.ancestry import Ancestry
from betty.config import Configuration, ConfigurationError, ExtensionConfiguration
from betty.asyncio import sync
from betty.graph import CyclicGraphError
from betty.app import App
from betty.tests import TestCase


class Tracker:
    async def track(self, carrier: List):
        raise NotImplementedError


class TrackableExtension(extension.Extension, Tracker):
    async def track(self, carrier: List):
        carrier.append(self)


class NonConfigurableExtension(TrackableExtension):
    pass  # pragma: no cover


class ConfigurableExtensionConfiguration(extension.Configuration):
    def __init__(self, check):
        super().__init__()
        self.check = check


class ConfigurableExtension(extension.ConfigurableExtension):
    configuration_schema: Schema = Schema({
        Required('check'): lambda x: x
    }, lambda configuration_dict: ConfigurableExtensionConfiguration(**configuration_dict))

    @classmethod
    def default_configuration(cls) -> extension.Configuration:
        return ConfigurableExtensionConfiguration(None)

    @classmethod
    def configuration_from_dict(cls, configuration_dict: Dict) -> ConfigurableExtensionConfiguration:
        try:
            return cls.configuration_schema(configuration_dict)
        except Invalid as e:
            raise ConfigurationError(e)

    @classmethod
    def configuration_to_dict(cls, configuration: ConfigurableExtensionConfiguration) -> Dict:
        return {
            'check': configuration.check
        }


class CyclicDependencyOneExtension(extension.Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[extension.Extension]]:
        return {CyclicDependencyTwoExtension}


class CyclicDependencyTwoExtension(extension.Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[extension.Extension]]:
        return {CyclicDependencyOneExtension}


class DependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[extension.Extension]]:
        return {NonConfigurableExtension}


class AlsoDependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[extension.Extension]]:
        return {NonConfigurableExtension}


class DependsOnNonConfigurableExtensionExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[extension.Extension]]:
        return {DependsOnNonConfigurableExtensionExtension}


class ComesBeforeNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_before(cls) -> Set[Type[extension.Extension]]:
        return {NonConfigurableExtension}


class ComesAfterNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_after(cls) -> Set[Type[extension.Extension]]:
        return {NonConfigurableExtension}


class AppTest(TestCase):
    _MINIMAL_CONFIGURATION_ARGS = {
        'output_directory_path': '/tmp/path/to/site',
        'base_url': 'https://example.com',
    }

    @sync
    async def test_ancestry(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertIsInstance(sut.ancestry, Ancestry)

    @sync
    async def test_configuration(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertEquals(configuration, sut.configuration)

    @sync
    async def test_extensions_with_one_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
        async with App(configuration) as sut:
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_extensions_with_one_configurable_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        check = 1337
        configuration.extensions.add(ExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
            check=check,
        )))
        async with App(configuration) as sut:
            self.assertIsInstance(sut.extensions[ConfigurableExtension], ConfigurableExtension)
            self.assertEquals(check, sut.extensions[ConfigurableExtension]._configuration.check)

    @sync
    async def test_extensions_with_one_extension_with_single_chained_dependency(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(DependsOnNonConfigurableExtensionExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(3, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertEquals(DependsOnNonConfigurableExtensionExtension,
                              type(carrier[1]))
            self.assertEquals(
                DependsOnNonConfigurableExtensionExtensionExtension, type(carrier[2]))

    @sync
    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(DependsOnNonConfigurableExtensionExtension))
        configuration.extensions.add(ExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(3, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertIn(DependsOnNonConfigurableExtensionExtension, [
                type(extension) for extension in carrier])
            self.assertIn(AlsoDependsOnNonConfigurableExtensionExtension, [
                type(extension) for extension in carrier])

    @sync
    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(CyclicDependencyOneExtension))
        with self.assertRaises(CyclicGraphError):
            async with App(configuration) as sut:
                sut.extensions

    @sync
    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
        configuration.extensions.add(ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))
            self.assertEquals(NonConfigurableExtension, type(carrier[1]))

    @sync
    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))

    @sync
    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
        configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[1]))

    @sync
    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[0]))

    @sync
    async def test_extensions_addition_to_configuration(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
            self.assertIsInstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_extensions_removal_from_configuration(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
        async with App(configuration) as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            del configuration.extensions[NonConfigurableExtension]
            self.assertNotIn(NonConfigurableExtension, sut.extensions)

    @sync
    async def test_assets_without_assets_directory_path(self) -> None:
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertEquals(1, len(sut.assets.paths))

    @sync
    async def test_assets_with_assets_directory_path(self) -> None:
        assets_directory_path = Path('/tmp/betty')
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.assets_directory_path = assets_directory_path
        async with App(configuration) as sut:
            self.assertEquals(2, len(sut.assets.paths))
            self.assertEquals((assets_directory_path, None), sut.assets.paths[0])
