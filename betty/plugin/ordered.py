"""
Plugins that can declare their order.
"""

from __future__ import annotations

from collections import defaultdict
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, Any

from typing_extensions import TypeVar

from betty.machine_name import MachineName
from betty.plugin import (
    PluginDefinition,
    PluginIdentifier,
    PluginRepository,
    resolve_id,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Set

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class OrderedPluginDefinition(PluginDefinition):
    """
    A definition of plugin that can declare its order with respect to other plugins.
    """

    def __init__(
        self,
        *,
        comes_before: Set[PluginIdentifier] | None = None,
        comes_after: Set[PluginIdentifier] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._comes_before = (
            set()
            if comes_before is None
            else {resolve_id(plugin) for plugin in comes_before}
        )
        self._comes_after = (
            set()
            if comes_after is None
            else {resolve_id(plugin) for plugin in comes_after}
        )

    @property
    def comes_before(self) -> Set[MachineName]:
        """
        Get the plugins that this plugin comes before.

        The returned plugins come after this plugin.
        """
        return self._comes_before

    @property
    def comes_after(self) -> Set[MachineName]:
        """
        Get the plugins that this plugin comes after.

        The returned plugins come before this plugin.
        """
        return self._comes_after


_OrderedPluginDefinitionT = TypeVar(
    "_OrderedPluginDefinitionT", bound=OrderedPluginDefinition
)


async def sort_ordered_plugin_graph(
    plugin_repository: PluginRepository[_OrderedPluginDefinitionT],
    plugins: Iterable[_OrderedPluginDefinitionT],
    /,
) -> TopologicalSorter[MachineName]:
    """
    Build a graph of the given plugins.
    """
    sorter = TopologicalSorter[MachineName]()
    plugins = sorted(plugins, key=lambda plugin: plugin.id)
    for plugin in plugins:
        sorter.add(plugin.id)
        for before_identifier in map(resolve_id, plugin.comes_before):
            before = plugin_repository[before_identifier]
            if before in plugins:
                sorter.add(before.id, plugin.id)
        for after_identifier in map(resolve_id, plugin.comes_after):
            after = plugin_repository[after_identifier]
            if after in plugins:
                sorter.add(plugin.id, after.id)
    return sorter


def get_comes_before(
    plugin_repository: PluginRepository[_OrderedPluginDefinitionT],
    origin: _OrderedPluginDefinitionT,
    /,
) -> Set[_OrderedPluginDefinitionT]:
    """
    Get all other plugins the given plugin comes before.
    """
    graph = defaultdict(set)
    for plugin in plugin_repository:
        for comes_before_id in plugin.comes_before:
            comes_before = plugin_repository[comes_before_id]
            graph[plugin].add(comes_before)
        for comes_after_id in plugin.comes_after:
            comes_after = plugin_repository[comes_after_id]
            graph[comes_after].add(plugin)
    return set(_collect_plugin_graph(graph, origin))


def get_comes_after(
    plugin_repository: PluginRepository[_OrderedPluginDefinitionT],
    origin: _OrderedPluginDefinitionT,
    /,
) -> Set[_OrderedPluginDefinitionT]:
    """
    Get all other plugins the given plugin comes after.
    """
    graph = defaultdict(set)
    for plugin in plugin_repository:
        for comes_after_id in plugin.comes_after:
            comes_after = plugin_repository[comes_after_id]
            graph[plugin].add(comes_after)
        for comes_before_id in plugin.comes_before:
            comes_before = plugin_repository[comes_before_id]
            graph[comes_before].add(plugin)
    return set(_collect_plugin_graph(graph, origin))


def _collect_plugin_graph(
    graph: Mapping[_PluginDefinitionT, Set[_PluginDefinitionT]],
    origin: _PluginDefinitionT,
) -> Iterator[_PluginDefinitionT]:
    yield from graph[origin]
    for target in graph[origin]:
        yield from _collect_plugin_graph(graph, target)
