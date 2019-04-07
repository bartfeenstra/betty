from functools import total_ordering
from importlib import import_module
from typing import Iterable, Callable, Tuple, Dict, Type, Any


class PluginError(BaseException):
    pass


class PluginNotFoundError(PluginError):
    pass


class CyclicDependencyError(PluginError):
    pass


class Plugin:
    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls()

    @classmethod
    def depends_on(cls) -> Iterable[Type]:
        return []

    def subscribe(self) -> Iterable[Tuple[str, Callable]]:
        return []


@total_ordering
class PluginSorter:
    def __init__(self, plugin_type: Type[Plugin]):
        self._type = plugin_type

    @property
    def type(self) -> Type[Plugin]:
        return self._type

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._type == other._type

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self._type in other._type.depends_on() and other._type in self._type.depends_on():
            raise CyclicDependencyError
        return self._type in other._type.depends_on()

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if other._type in self._type.depends_on() and self._type in other._type.depends_on():
            raise CyclicDependencyError
        return other._type in self._type.depends_on()


def name(cls: Type):
    return '%s.%s' % (cls.__module__, cls.__name__)


def depends_on(plugin_type: Type[Plugin]):
    for dependency_type in plugin_type.depends_on():
        yield dependency_type
        yield from depends_on(dependency_type)


def from_configuration_list(configuration: Iterable[Dict[str, Any]]) -> Iterable[Plugin]:
    # @todo What structure do we want? Dictionaries are not sorted.
    # @todo The top-level structure must therefore be a list.
    # @todo Any list item is per plugin type.
    # @todo Any list item needs *at least* two pieces of information: the plugin type name, and its (optional) configuration.
    # @todo Let's do two keys: one for the plugin type name, and one for the config, which can be ommitted if the plugin takes no config, or for default config.
    # @todo
    # @todo

    # Collect the plugin types, including dependencies.
    plugin_type_names = configuration.keys()
    plugin_types = set()
    for plugin_type_name in plugin_type_names:
        plugin_module_name, plugin_class_name = plugin_type_name.rsplit('.', 1)
        try:
            module = import_module(plugin_module_name)
        except ModuleNotFoundError:
            raise PluginNotFoundError('Could not find module "%s" for plugin "%s".' % (plugin_module_name, plugin_type_name))
        try:
            plugin_type = getattr(module, plugin_class_name)
        except AttributeError:
            raise PluginNotFoundError('Could not find plugin "%s" in module "%s".' % (plugin_type_name, plugin_module_name))
        plugin_types.add(plugin_type)
        plugin_types.update(plugin_type.depends_on())

    # Sort plugins based on dependencies.
    plugin_sorters = sorted([PluginSorter(plugin_type) for plugin_type in plugin_types])
    sorted_plugin_types = [sorter.type for sorter in plugin_sorters]

    # Instantiate plugins based on their configuration.
    plugins = []
    for plugin_type in sorted_plugin_types:
        plugin_type_name = name(plugin_type)
        plugin_type_configuration = configuration[plugin_type_name] if plugin_type_name in configuration else {}
        plugins.append(plugin_type.from_configuration_dict(plugin_type_configuration))

    return plugins
