"""
Plugins that can declare dependencies on other plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.plugin import ResolvableId, resolve_id
from betty.plugin.ordered import OrderedPluginDefinition, sort_ordered_plugin_graph

if TYPE_CHECKING:
    from collections.abc import Iterable, Set
    from graphlib import TopologicalSorter

    from betty.machine_name import MachineName, ResolvableMachineName
    from betty.service.plugin import PluginManager


class DependentPluginDefinition[BaseClsT = Any](OrderedPluginDefinition[BaseClsT]):
    """
    A definition of a plugin that can declare its dependency on other plugins.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        comes_before: Set[ResolvableId] | None = None,
        comes_after: Set[ResolvableId] | None = None,
        depends_on: Set[ResolvableId] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            plugin_id, comes_before=comes_before, comes_after=comes_after, **kwargs
        )
        self._depends_on = (
            set()
            if depends_on is None
            else {resolve_id(plugin) for plugin in depends_on}
        )
        self._comes_after.update(self._depends_on)

    @property
    def depends_on(self) -> Set[MachineName]:
        """
        The plugins this one depends on.

        All plugins will automatically be added to :py:meth:`betty.plugin.ordered.OrderedPluginDefinition.comes_after`.
        """
        return self._depends_on


async def expand_plugin_dependencies[
    DependentPluginDefinitionT: DependentPluginDefinition
](
    available_plugins: PluginManager[DependentPluginDefinitionT],
    plugins: Iterable[DependentPluginDefinitionT],
    /,
) -> Set[DependentPluginDefinitionT]:
    """
    Expand a collection of plugins to include their dependencies.
    """
    dependencies = set()
    for plugin in plugins:
        dependencies.add(plugin)
        dependencies.update(
            await expand_plugin_dependencies(
                available_plugins,
                [
                    await available_plugins[depends_on]
                    for depends_on in plugin.depends_on
                ],
            )
        )
    return dependencies


async def sort_dependent_plugin_graph[
    DependentPluginDefinitionT: DependentPluginDefinition
](
    available_plugins: PluginManager[DependentPluginDefinitionT],
    plugins: Iterable[DependentPluginDefinitionT],
    /,
) -> TopologicalSorter[MachineName]:
    """
    Sort a dependent plugin graph.
    """
    return await sort_ordered_plugin_graph(
        available_plugins, await expand_plugin_dependencies(available_plugins, plugins)
    )
