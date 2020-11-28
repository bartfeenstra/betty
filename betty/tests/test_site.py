from typing import List, Type, Set, Any

from voluptuous import Schema, Required

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.asyncio import sync
from betty.graph import CyclicGraphError
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.site import Site
from betty.tests import TestCase


class Tracker:
    async def track(self, carrier: List):
        raise NotImplementedError


class TrackablePlugin(Plugin, Tracker):
    async def track(self, carrier: List):
        carrier.append(self)


class NonConfigurablePlugin(TrackablePlugin):
    pass  # pragma: no cover


class ConfigurablePlugin(Plugin):
    configuration_schema: Schema = Schema({
        Required('check'): lambda x: x
    })

    def __init__(self, check):
        self.check = check

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(configuration['check'])


class CyclicDependencyOnePlugin(Plugin):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {CyclicDependencyTwoPlugin}


class CyclicDependencyTwoPlugin(Plugin):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {CyclicDependencyOnePlugin}


class DependsOnNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {NonConfigurablePlugin}


class AlsoDependsOnNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {NonConfigurablePlugin}


class DependsOnNonConfigurablePluginPluginPlugin(TrackablePlugin):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {DependsOnNonConfigurablePluginPlugin}


class ComesBeforeNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def comes_before(cls) -> Set[Type[Plugin]]:
        return {NonConfigurablePlugin}


class ComesAfterNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def comes_after(cls) -> Set[Type[Plugin]]:
        return {NonConfigurablePlugin}


class SiteTest(TestCase):
    _MINIMAL_CONFIGURATION_ARGS = {
        'output_directory_path': '/tmp/path/to/site',
        'base_url': 'https://example.com',
    }

    @sync
    async def test_ancestry_should_return(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with Site(configuration) as sut:
            self.assertIsInstance(sut.ancestry, Ancestry)

    @sync
    async def test_configuration_should_return(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with Site(configuration) as sut:
            self.assertEquals(configuration, sut.configuration)

    @sync
    async def test_with_one_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[NonConfigurablePlugin] = None
        async with Site(configuration) as sut:
            self.assertEquals(1, len(sut.plugins))
            self.assertIsInstance(
                sut.plugins[NonConfigurablePlugin], NonConfigurablePlugin)

    @sync
    async def test_with_one_configurable_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        check = 1337
        configuration.plugins[ConfigurablePlugin] = {
            'check': check,
        }
        async with Site(configuration) as sut:
            self.assertEquals(1, len(sut.plugins))
            self.assertIsInstance(
                sut.plugins[ConfigurablePlugin], ConfigurablePlugin)
            self.assertEquals(check, sut.plugins[ConfigurablePlugin].check)

    @sync
    async def test_with_one_plugin_with_single_chained_dependency(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[DependsOnNonConfigurablePluginPluginPlugin] = None
        async with Site(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(3, len(carrier))
            self.assertEquals(NonConfigurablePlugin, type(carrier[0]))
            self.assertEquals(DependsOnNonConfigurablePluginPlugin,
                              type(carrier[1]))
            self.assertEquals(
                DependsOnNonConfigurablePluginPluginPlugin, type(carrier[2]))

    @sync
    async def test_with_multiple_plugins_with_duplicate_dependencies(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[DependsOnNonConfigurablePluginPlugin] = None
        configuration.plugins[AlsoDependsOnNonConfigurablePluginPlugin] = None
        async with Site(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(3, len(carrier))
            self.assertEquals(NonConfigurablePlugin, type(carrier[0]))
            self.assertIn(DependsOnNonConfigurablePluginPlugin, [
                type(plugin) for plugin in carrier])
            self.assertIn(AlsoDependsOnNonConfigurablePluginPlugin, [
                type(plugin) for plugin in carrier])

    @sync
    async def test_with_multiple_plugins_with_cyclic_dependencies(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[CyclicDependencyOnePlugin] = None
        with self.assertRaises(CyclicGraphError):
            async with Site(configuration):
                pass

    @sync
    async def test_with_comes_before_with_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[NonConfigurablePlugin] = None
        configuration.plugins[ComesBeforeNonConfigurablePluginPlugin] = None
        async with Site(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurablePluginPlugin, type(carrier[0]))
            self.assertEquals(NonConfigurablePlugin, type(carrier[1]))

    @sync
    async def test_with_comes_before_without_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[ComesBeforeNonConfigurablePluginPlugin] = None
        async with Site(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(
                ComesBeforeNonConfigurablePluginPlugin, type(carrier[0]))

    @sync
    async def test_with_comes_after_with_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[ComesAfterNonConfigurablePluginPlugin] = None
        configuration.plugins[NonConfigurablePlugin] = None
        async with Site(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(2, len(carrier))
            self.assertEquals(NonConfigurablePlugin, type(carrier[0]))
            self.assertEquals(ComesAfterNonConfigurablePluginPlugin,
                              type(carrier[1]))

    @sync
    async def test_with_comes_after_without_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[ComesAfterNonConfigurablePluginPlugin] = None
        async with Site(configuration) as sut:
            carrier = []
            await sut.dispatcher.dispatch(Tracker, 'track')(carrier)
            self.assertEquals(1, len(carrier))
            self.assertEquals(ComesAfterNonConfigurablePluginPlugin,
                              type(carrier[0]))

    @sync
    async def test_resources_without_assets_directory_path(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        async with Site(configuration) as sut:
            self.assertEquals(1, len(sut.assets.paths))

    @sync
    async def test_resources_with_assets_directory_path(self):
        assets_directory_path = '/tmp/betty'
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.assets_directory_path = assets_directory_path
        async with Site(configuration) as sut:
            self.assertEquals(2, len(sut.assets.paths))
            self.assertEquals(assets_directory_path, sut.assets.paths[0])
