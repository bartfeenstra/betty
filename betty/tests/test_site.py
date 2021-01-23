from typing import List, Type, Set, Any, Dict, Optional

from voluptuous import Schema, Required, Invalid

from betty.ancestry import Ancestry
from betty.config import Configuration, ConfigurationValueError
from betty.asyncio import sync
from betty.graph import CyclicGraphError
from betty.extension import Extension, NO_CONFIGURATION
from betty.app import App
from betty.tests import TestCase


class Tracker:
    async def track(self, carrier: List):
        raise NotImplementedError


class TrackableExtension(Extension, Tracker):
    async def track(self, carrier: List):
        carrier.append(self)


class NonConfigurableExtension(TrackableExtension):
    pass  # pragma: no cover


class ConfigurableExtension(Extension):
    configuration_schema: Schema = Schema({
        Required('check'): lambda x: x
    })

    def __init__(self, check):
        self.check = check

    @classmethod
    def validate_configuration(cls, configuration: Optional[Dict]) -> Dict:
        try:
            return cls.configuration_schema(configuration)
        except Invalid as e:
            raise ConfigurationValueError(e)

    @classmethod
    def new_for_app(cls, app: App, configuration: Any = NO_CONFIGURATION):
        return cls(configuration['check'])


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


class SiteTest(TestCase):
    _MINIMAL_CONFIGURATION_ARGS = {
        'output_directory_path': '/tmp/path/to/site',
        'base_url': 'https://example.com',
    }

    @sync
    async def test_ancestry_should_return(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertIsInstance(sut.ancestry, Ancestry)

    @sync
    async def test_configuration_should_return(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertEquals(configuration, sut.configuration)

    @sync
    async def test_with_one_extension(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[NonConfigurableExtension] = None
        async with App(configuration) as sut:
            self.assertEquals(1, len(sut.extensions))
            self.assertIsInstance(
                sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    @sync
    async def test_with_one_configurable_extension(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        check = 1337
        configuration.extensions[ConfigurableExtension] = {
            'check': check,
        }
        async with App(configuration) as sut:
            self.assertEquals(1, len(sut.extensions))
            self.assertIsInstance(
                sut.extensions[ConfigurableExtension], ConfigurableExtension)
            self.assertEquals(check, sut.extensions[ConfigurableExtension].check)

    @sync
    async def test_with_one_extension_with_single_chained_dependency(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[DependsOnNonConfigurableExtensionExtensionExtension] = None
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
    async def test_with_multiple_extensions_with_duplicate_dependencies(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[DependsOnNonConfigurableExtensionExtension] = None
        configuration.extensions[AlsoDependsOnNonConfigurableExtensionExtension] = None
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
    async def test_with_multiple_extensions_with_cyclic_dependencies(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[CyclicDependencyOneExtension] = None
        with self.assertRaises(CyclicGraphError):
            async with App(configuration):
                pass

    @sync
    async def test_with_comes_before_with_other_extension(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[NonConfigurableExtension] = None
        configuration.extensions[ComesBeforeNonConfigurableExtensionExtension] = None
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))
            self.assertEquals(NonConfigurableExtension, type(carrier[1]))

    @sync
    async def test_with_comes_before_without_other_extension(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[ComesBeforeNonConfigurableExtensionExtension] = None
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurableExtensionExtension, type(carrier[0]))

    @sync
    async def test_with_comes_after_with_other_extension(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[ComesAfterNonConfigurableExtensionExtension] = None
        configuration.extensions[NonConfigurableExtension] = None
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(NonConfigurableExtension, type(carrier[0]))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[1]))

    @sync
    async def test_with_comes_after_without_other_extension(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.extensions[ComesAfterNonConfigurableExtensionExtension] = None
        async with App(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(ComesAfterNonConfigurableExtensionExtension,
                              type(carrier[0]))

    @sync
    async def test_resources_without_assets_directory_path(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with App(configuration) as sut:
            self.assertEquals(1, len(sut.assets.paths))

    @sync
    async def test_resources_with_assets_directory_path(self):
        assets_directory_path = '/tmp/betty'
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.assets_directory_path = assets_directory_path
        async with App(configuration) as sut:
            self.assertEquals(2, len(sut.assets.paths))
            self.assertEquals(assets_directory_path, sut.assets.paths[0])
