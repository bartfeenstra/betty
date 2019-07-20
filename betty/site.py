from collections import defaultdict
from os.path import abspath, dirname, join
from typing import Type, Dict

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.event import EventDispatcher
from betty.fs import FileSystem
from betty.graph import tsort, Graph


class Site:
    def __init__(self, configuration: Configuration):
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._resources = FileSystem(
            join(dirname(abspath(__file__)), 'resources'))
        if configuration.resources_directory_path:
            self._resources.paths.appendleft(
                configuration.resources_directory_path)
        self._event_dispatcher = EventDispatcher()
        self._plugins = {}
        self._init_plugins()

    def _init_plugins(self):
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
            for event_name, listener in plugin.subscribes_to():
                self._event_dispatcher.add_listener(event_name, listener)
            if plugin.resource_directory_path is not None:
                self._resources.paths.appendleft(
                    plugin.resource_directory_path)

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def configuration(self):
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
