"""
Plugins that can declare their order.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Self, final

from betty.definition.id import ResolvableId, resolve_id
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import PluginDefinition

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
        after: Order[Self] = (),
        auto: bool = False,
        before: Order[Self] = (),
        requires: Requires = (),
        **kwargs: Any,
    ):
        super().__init__(plugin_id, auto=auto, requires=requires, **kwargs)
        self.__after = self.__resolve_order(after)
        self.__before = self.__resolve_order(before)

    def __resolve_order(self, order: Order) -> Callable[[MachineName], bool]:
        if callable(order):
            return order  # ty:ignore[invalid-return-type]
        order = {resolve_id(plugin) for plugin in order}
        return lambda other: other in order

    @final
    def after(self, other: MachineName, /) -> bool:
        """
        Test if this plugin comes after another plugin.
        """
        return self.__after(other)

    @final
    def before(self, other: MachineName, /) -> bool:
        """
        Test if this plugin comes before another plugin.
        """
        return self.__before(other)


type Order[OrderedDefinitionT: OrderedPluginDefinition = OrderedPluginDefinition] = (
    Callable[[MachineName], bool] | Iterable[ResolvableId[OrderedDefinitionT]]
)
