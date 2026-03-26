"""
Plugins that can declare their order.
"""

from __future__ import annotations

from collections.abc import Set
from typing import TYPE_CHECKING, Any, final

from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import PluginDefinition, ResolvablePluginId, resolve_plugin_id

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.requirement import Requires


class OrderedPluginDefinition[BaseClsT](PluginDefinition[BaseClsT]):
    """
    A definition of plugin that can declare its order with respect to other plugins.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[OrderedPluginDefinition[BaseClsT]] | None = None,
        before: Order[OrderedPluginDefinition[BaseClsT]] | None = None,
        requires: Requires = (),
        **kwargs: Any,
    ):
        super().__init__(plugin_id, requires=requires, **kwargs)
        self._after = self.__resolve_order(after)
        self._before = self.__resolve_order(before)

    def __resolve_order(self, order: Order | None) -> Callable[[MachineName], bool]:
        if order is None:
            return lambda _: False
        if isinstance(order, Set):
            order = {resolve_plugin_id(plugin) for plugin in order}
            return lambda other: other in order
        return order

    @final
    def after(self, other: MachineName, /) -> bool:
        """
        Test if this plugin comes after another plugin.
        """
        return self._after(other)

    @final
    def before(self, other: MachineName, /) -> bool:
        """
        Test if this plugin comes before another plugin.
        """
        return self._before(other)


type Order[
    OrderedPluginDefinitionT: OrderedPluginDefinition = OrderedPluginDefinition
] = Set[ResolvablePluginId[OrderedPluginDefinitionT]] | Callable[[MachineName], bool]
