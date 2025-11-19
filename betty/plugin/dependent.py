"""
Plugins that can declare dependencies on other plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from betty.plugin import PluginIdentifier, PluginRepository, resolve_id
from betty.plugin.ordered import OrderedPluginDefinition, sort_ordered_plugin_graph

if TYPE_CHECKING:
    from collections.abc import Iterable, Set
    from graphlib import TopologicalSorter

    from betty.machine_name import MachineName


class DependentPluginDefinition(OrderedPluginDefinition):
    """
    A definition of a plugin that can declare its dependency on other plugins.
    """

    def __init__(
        self,
        *,
        depends_on: Set[PluginIdentifier] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
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


_DependentPluginDefinitionT = TypeVar(
    "_DependentPluginDefinitionT", bound=DependentPluginDefinition
)


async def expand_plugin_dependencies(
    plugin_repository: PluginRepository[_DependentPluginDefinitionT],
    plugins: Iterable[_DependentPluginDefinitionT],
    /,
) -> Set[_DependentPluginDefinitionT]:
    """
    Expand a collection of plugins to include their dependencies.
    """
    dependencies = set()
    for plugin in plugins:
        dependencies.add(plugin)
        dependencies.update(
            await expand_plugin_dependencies(
                plugin_repository,
                [plugin_repository.get(depends_on) for depends_on in plugin.depends_on],
            )
        )
    return dependencies


async def sort_dependent_plugin_graph(
    plugin_repository: PluginRepository[_DependentPluginDefinitionT],
    plugins: Iterable[_DependentPluginDefinitionT],
    /,
) -> TopologicalSorter[MachineName]:
    """
    Sort a dependent plugin graph.
    """
    return await sort_ordered_plugin_graph(
        plugin_repository, await expand_plugin_dependencies(plugin_repository, plugins)
    )
