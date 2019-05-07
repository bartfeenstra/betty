from typing import Dict
from unittest import TestCase

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.event import Event
from betty.graph import CyclicGraphError
from betty.plugin import Plugin
from betty.site import Site


class TrackingEvent(Event):
    def __init__(self):
        self.tracker = []


class TrackablePlugin(Plugin):
    def subscribes_to(self):
        return [
            (TrackingEvent, self._track)
        ]

    def _track(self, event: TrackingEvent):
        event.tracker.append(self)


class NonConfigurablePlugin(TrackablePlugin):
    pass


class ConfigurablePlugin(Plugin):
    def __init__(self, check):
        self.check = check

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(configuration['check'])


class CyclicDependencyOnePlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {CyclicDependencyTwoPlugin}


class CyclicDependencyTwoPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {CyclicDependencyOnePlugin}


class DependsOnNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def depends_on(cls):
        return {NonConfigurablePlugin}


class AlsoDependsOnNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def depends_on(cls):
        return {NonConfigurablePlugin}


class DependsOnNonConfigurablePluginPluginPlugin(TrackablePlugin):
    @classmethod
    def depends_on(cls):
        return {DependsOnNonConfigurablePluginPlugin}


class ComesBeforeNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def comes_before(cls):
        return {NonConfigurablePlugin}


class ComesAfterNonConfigurablePluginPlugin(TrackablePlugin):
    @classmethod
    def comes_after(cls):
        return {NonConfigurablePlugin}


class SiteTest(TestCase):
    _MINIMAL_CONFIGURATION_ARGS = {
        'output_directory_path': '/tmp/path/to/site',
        'url': 'https://example.com',
    }

    def test_ancestry_should_return(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        sut = Site(configuration)
        self.assertIsInstance(sut.ancestry, Ancestry)

    def test_configuration_should_return(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        sut = Site(configuration)
        self.assertEquals(configuration, sut.configuration)

    def test_with_one_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[NonConfigurablePlugin] = {}
        sut = Site(configuration)
        self.assertEquals(1, len(sut.plugins))
        self.assertIsInstance(
            sut.plugins[NonConfigurablePlugin], NonConfigurablePlugin)

    def test_with_one_configurable_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        check = 1337
        configuration.plugins[ConfigurablePlugin] = {
            'check': check,
        }
        sut = Site(configuration)
        self.assertEquals(1, len(sut.plugins))
        self.assertIsInstance(
            sut.plugins[ConfigurablePlugin], ConfigurablePlugin)
        self.assertEquals(check, sut.plugins[ConfigurablePlugin].check)

    def test_with_one_plugin_with_single_chained_dependency(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[DependsOnNonConfigurablePluginPluginPlugin] = {}
        sut = Site(configuration)
        event = TrackingEvent()
        sut.event_dispatcher.dispatch(event)
        self.assertEquals(3, len(event.tracker))
        self.assertEquals(NonConfigurablePlugin, type(event.tracker[0]))
        self.assertEquals(DependsOnNonConfigurablePluginPlugin,
                          type(event.tracker[1]))
        self.assertEquals(
            DependsOnNonConfigurablePluginPluginPlugin, type(event.tracker[2]))

    def test_with_multiple_plugins_with_duplicate_dependencies(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[DependsOnNonConfigurablePluginPlugin] = {}
        configuration.plugins[AlsoDependsOnNonConfigurablePluginPlugin] = {}
        sut = Site(configuration)
        event = TrackingEvent()
        sut.event_dispatcher.dispatch(event)
        self.assertEquals(3, len(event.tracker))
        self.assertEquals(NonConfigurablePlugin, type(event.tracker[0]))
        self.assertIn(DependsOnNonConfigurablePluginPlugin, [
            type(plugin) for plugin in event.tracker])
        self.assertIn(AlsoDependsOnNonConfigurablePluginPlugin, [
            type(plugin) for plugin in event.tracker])

    def test_with_multiple_plugins_with_cyclic_dependencies(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[CyclicDependencyOnePlugin] = {}
        with self.assertRaises(CyclicGraphError):
            Site(configuration)

    def test_with_comes_before_with_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[NonConfigurablePlugin] = {}
        configuration.plugins[ComesBeforeNonConfigurablePluginPlugin] = {}
        sut = Site(configuration)
        event = TrackingEvent()
        sut.event_dispatcher.dispatch(event)
        self.assertEquals(2, len(event.tracker))
        self.assertEquals(
            ComesBeforeNonConfigurablePluginPlugin, type(event.tracker[0]))
        self.assertEquals(NonConfigurablePlugin, type(event.tracker[1]))

    def test_with_comes_before_without_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[ComesBeforeNonConfigurablePluginPlugin] = {}
        sut = Site(configuration)
        event = TrackingEvent()
        sut.event_dispatcher.dispatch(event)
        self.assertEquals(1, len(event.tracker))
        self.assertEquals(
            ComesBeforeNonConfigurablePluginPlugin, type(event.tracker[0]))

    def test_with_comes_after_with_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[ComesAfterNonConfigurablePluginPlugin] = {}
        configuration.plugins[NonConfigurablePlugin] = {}
        sut = Site(configuration)
        event = TrackingEvent()
        sut.event_dispatcher.dispatch(event)
        self.assertEquals(2, len(event.tracker))
        self.assertEquals(NonConfigurablePlugin, type(event.tracker[0]))
        self.assertEquals(ComesAfterNonConfigurablePluginPlugin,
                          type(event.tracker[1]))

    def test_with_comes_after_without_other_plugin(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[ComesAfterNonConfigurablePluginPlugin] = {}
        sut = Site(configuration)
        event = TrackingEvent()
        sut.event_dispatcher.dispatch(event)
        self.assertEquals(1, len(event.tracker))
        self.assertEquals(ComesAfterNonConfigurablePluginPlugin,
                          type(event.tracker[0]))

    def test_resources_without_resources_path(self):
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        sut = Site(configuration)
        self.assertEquals(1, len(sut.resources.paths))

    def test_resources_with_resources_path(self):
        resources_path = '/tmp/betty'
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.resources_path = resources_path
        sut = Site(configuration)
        self.assertEquals(2, len(sut.resources.paths))
        self.assertEquals(resources_path, sut.resources.paths[0])
