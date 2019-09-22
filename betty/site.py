import gettext
import logging
from collections import defaultdict, OrderedDict
from os.path import abspath, dirname, join
from typing import Type, Dict

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.event import EventDispatcher
from betty.fs import FileSystem
from betty.graph import tsort, Graph
from betty.locale import open_translations, Locale


class Site:
    def __init__(self, configuration: Configuration):
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._resources = FileSystem(
            join(dirname(abspath(__file__)), 'resources'))
        self._event_dispatcher = EventDispatcher()
        self._translations = defaultdict(gettext.NullTranslations)
        self._plugins = OrderedDict()
        self._init_plugins()
        self._init_event_listeners()
        self._init_resources()
        self._init_translations()

    def _init_plugins(self) -> None:
        def _extend_plugin_type_graph(graph: Graph, plugin_type: Type):
            dependencies = plugin_type.depends_on()
            # Ensure each plugin type appears in the graph, even if they're isolated.
            graph.setdefault(plugin_type, set())
            for dependency in dependencies:
                seen_dependency = dependency in graph
                graph[dependency].add(plugin_type)
                if not seen_dependency:
                    _extend_plugin_type_graph(graph, dependency)

        plugin_types_graph = defaultdict(set)
        # Add dependencies to the plugin graph.
        for plugin_type in self._configuration.plugins.keys():
            _extend_plugin_type_graph(plugin_types_graph, plugin_type)
        # Now all dependencies have been collected, extend the graph with optional plugin orders.
        for plugin_type in self._configuration.plugins.keys():
            for before in plugin_type.comes_before():
                if before in plugin_types_graph:
                    plugin_types_graph[plugin_type].add(before)
            for after in plugin_type.comes_after():
                if after in plugin_types_graph:
                    plugin_types_graph[after].add(plugin_type)

        for plugin_type in tsort(plugin_types_graph):
            plugin_configuration = self.configuration.plugins[
                plugin_type] if plugin_type in self.configuration.plugins else {}
            plugin = plugin_type.from_configuration_dict(
                self, plugin_configuration)
            self._plugins[plugin_type] = plugin

    def _init_event_listeners(self) -> None:
        for plugin in self._plugins.values():
            for event_name, listener in plugin.subscribes_to():
                self._event_dispatcher.add_listener(event_name, listener)

    def _init_resources(self) -> None:
        for plugin in self._plugins.values():
            if plugin.resource_directory_path is not None:
                self._resources.paths.appendleft(
                    plugin.resource_directory_path)
        if self._configuration.resources_directory_path:
            self._resources.paths.appendleft(
                self._configuration.resources_directory_path)

    def _init_translations(self) -> None:
        self._translations[Locale('en', 'US')] = gettext.NullTranslations()
        for locale in self._configuration.locales:
            for resources_path in reversed(self._resources.paths):
                translations = open_translations(locale, resources_path)
                if translations:
                    translations.add_fallback(self._translations[locale])
                    self._translations[locale] = translations
        try:
            self.translations[self._configuration.default_locale].install()
        except KeyError:
            logger = logging.getLogger()
            logger.debug('No translations found for default locale %s.' %
                         self._configuration.default_locale)

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    @property
    def plugins(self) -> Dict:
        return self._plugins

    @property
    def resources(self) -> FileSystem:
        return self._resources

    @property
    def event_dispatcher(self) -> EventDispatcher:
        return self._event_dispatcher

    @property
    def translations(self) -> Dict[Locale, gettext.NullTranslations]:
        return self._translations
