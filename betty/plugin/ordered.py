"""
Plugins that can declare their order.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, final

from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import PluginDefinition
from betty.plugin.cls import PluginClsDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.requirement import Requires


class OrderedPluginDefinition(PluginDefinition):
    """
    A plugin definition that can declare its order with respect to other plugin definitions.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[OrderedPluginDefinition] = (),
        before: Order[OrderedPluginDefinition] = (),
        requires: Requires = (),
        **kwargs: Any,
    ):
        super().__init__(plugin_id, requires=requires, **kwargs)
        self._after = self.__resolve_order(after)
        self._before = self.__resolve_order(before)

    def __resolve_order(self, order: Order) -> Callable[[MachineName], bool]:
        if callable(order):
            return order  # ty:ignore[invalid-return-type]
        order = {resolve_plugin_id(plugin) for plugin in order}
        return lambda other: other in order

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


class OrderedPluginClsDefinition[BaseClsT](
    OrderedPluginDefinition, PluginClsDefinition[BaseClsT]
):
    """
    A definition of a classed plugin that can declare its order with respect to other plugins.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[OrderedPluginClsDefinition[BaseClsT]] = (),
        before: Order[OrderedPluginClsDefinition[BaseClsT]] = (),
        requires: Requires = (),
        **kwargs: Any,
    ):
        super().__init__(
            plugin_id, after=after, before=before, requires=requires, **kwargs
        )


type Order[
    OrderedPluginDefinitionT: OrderedPluginDefinition = OrderedPluginDefinition
] = (
    Callable[[MachineName], bool]
    | Iterable[ResolvablePluginId[OrderedPluginDefinitionT]]
)
