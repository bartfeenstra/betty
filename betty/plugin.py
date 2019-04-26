from collections import defaultdict
from importlib import import_module
from typing import Iterable, Callable, Tuple, Dict, Type, Any, Set, List

from betty.graph import tsort, Graph


class PluginError(BaseException):
    pass


class PluginNotFoundError(PluginError):
    pass


class Plugin:
    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls()

    @classmethod
    def depends_on(cls) -> Set[Type]:
        return set()

    def subscribes_to(self) -> Set[Tuple[str, Callable]]:
        return set()


def name(cls: Type):
    return '%s.%s' % (cls.__module__, cls.__name__)


def _normalize(plugin_definition):
    if isinstance(plugin_definition, str):
        return plugin_definition, {}
    plugin_definition.setdefault('configuration', {})
    return plugin_definition['type'], plugin_definition['configuration']


def _load(plugin_type_name) -> Type:
    plugin_module_name, plugin_class_name = plugin_type_name.rsplit('.', 1)
    try:
        module = import_module(plugin_module_name)
    except ImportError:
        raise PluginNotFoundError(
            'Could not find module "%s" for plugin "%s".' % (plugin_module_name, plugin_type_name))
    try:
        return getattr(module, plugin_class_name)
    except AttributeError:
        raise PluginNotFoundError('Could not find plugin "%s" in module "%s".' % (plugin_type_name, plugin_module_name))


def from_configuration_list(configuration: Iterable[Dict[str, Any]]) -> List[Plugin]:
    # Collect the plugin types, including dependencies.
    plugin_types_configuration = defaultdict(dict)
    plugin_types_graph = {}
    for plugin_definition in configuration:
        plugin_type_name, plugin_configuration = _normalize(plugin_definition)
        plugin_type = _load(plugin_type_name)
        plugin_types_configuration[plugin_type] = plugin_configuration
        _extend_plugin_type_graph(plugin_types_graph, plugin_type)

    # Instantiate plugins based on their configuration. We need a list to guarantee order.
    plugins = []
    for plugin_type in tsort(plugin_types_graph):
        plugins.append(plugin_type.from_configuration_dict(plugin_types_configuration[plugin_type]))
    return plugins


def _extend_plugin_type_graph(graph: Graph, plugin_type: Type):
    graph[plugin_type] = plugin_type.depends_on()
    for dependency in plugin_type.depends_on():
        if dependency not in graph:
            _extend_plugin_type_graph(graph, dependency)
