from typing import Dict, List
from unittest import TestCase

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.graph import CyclicGraphError
from betty.plugin import Plugin
from betty.site import Site

TRACKING_EVENT = '%s:tracking_event' % __file__


class TrackablePlugin(Plugin):
    def subscribes_to(self):
        return [
            (TRACKING_EVENT, self._track)
        ]

    def _track(self, tracker: List):
        tracker.append(self)


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


class SiteTest(TestCase):
    _MINIMAL_CONFIGURATION_ARGS = {
        'input_gramps_file_path': '/tmp/path/to/data.xml',
        'output_directory_path': '/tmp/path/to/site',
        'url': 'https://example.com',
    }

    def test_ancestry_should_return(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        sut = Site(ancestry, configuration)
        self.assertEquals(ancestry, sut.ancestry)

    def test_configuration_should_return(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        sut = Site(ancestry, configuration)
        self.assertEquals(configuration, sut.configuration)

    def test_with_one_plugin(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[NonConfigurablePlugin] = {}
        sut = Site(ancestry, configuration)
        self.assertEquals(1, len(sut.plugins))
        self.assertIsInstance(
            sut.plugins[NonConfigurablePlugin], NonConfigurablePlugin)

    def test_with_one_configurable_plugin(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        check = 1337
        configuration.plugins[ConfigurablePlugin] = {
            'check': check,
        }
        sut = Site(ancestry, configuration)
        self.assertEquals(1, len(sut.plugins))
        self.assertIsInstance(
            sut.plugins[ConfigurablePlugin], ConfigurablePlugin)
        self.assertEquals(check, sut.plugins[ConfigurablePlugin].check)

    def test_with_one_plugin_with_single_chained_dependency(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[DependsOnNonConfigurablePluginPluginPlugin] = {}
        sut = Site(ancestry, configuration)
        tracker = []
        sut.event_dispatcher.dispatch(TRACKING_EVENT, tracker)
        self.assertEquals(3, len(tracker))
        self.assertEquals(NonConfigurablePlugin, type(tracker[0]))
        self.assertEquals(
            DependsOnNonConfigurablePluginPlugin, type(tracker[1]))
        self.assertEquals(
            DependsOnNonConfigurablePluginPluginPlugin, type(tracker[2]))

    def test_with_multiple_plugins_with_duplicate_dependencies(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[DependsOnNonConfigurablePluginPlugin] = {}
        configuration.plugins[AlsoDependsOnNonConfigurablePluginPlugin] = {}
        sut = Site(ancestry, configuration)
        tracker = []
        sut.event_dispatcher.dispatch(TRACKING_EVENT, tracker)
        self.assertEquals(3, len(tracker))
        self.assertEquals(NonConfigurablePlugin, type(tracker[0]))
        self.assertIn(DependsOnNonConfigurablePluginPlugin,
                      [type(plugin) for plugin in tracker])
        self.assertIn(AlsoDependsOnNonConfigurablePluginPlugin,
                      [type(plugin) for plugin in tracker])

    def test_with_multiple_plugins_with_cyclic_dependencies(self):
        ancestry = Ancestry()
        configuration = Configuration(**self._MINIMAL_CONFIGURATION_ARGS)
        configuration.plugins[CyclicDependencyOnePlugin] = {}
        with self.assertRaises(CyclicGraphError):
            Site(ancestry, configuration)
