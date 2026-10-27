"""
Definitions that can declare their order.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Self, final

from betty.definition.id import IdentifiableDefinition, ResolvableId, resolve_id
from betty.machine_name import MachineName

if TYPE_CHECKING:
    from collections.abc import Callable


class OrderedDefinition(IdentifiableDefinition):
    """
    A definition that can declare its order with respect to other definitions.
    """

    def __init__(
        self,
        *args: Any,
        after: Order[Self] = (),
        before: Order[Self] = (),
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__after = self.__resolve_order(after)
        self.__before = self.__resolve_order(before)

    def __resolve_order(self, order: Order) -> Callable[[MachineName], bool]:
        if callable(order):
            return order  # ty:ignore[invalid-return-type]
        order = {resolve_id(other) for other in order}
        return lambda other: other in order

    @final
    def after(self, other: MachineName, /) -> bool:
        """
        Test if this definition comes after another definition.
        """
        return self.__after(other)

    @final
    def before(self, other: MachineName, /) -> bool:
        """
        Test if this definition comes before another definition.
        """
        return self.__before(other)


type Order[OrderedDefinitionT: OrderedDefinition = OrderedDefinition] = (
    Callable[[MachineName], bool] | Iterable[ResolvableId[OrderedDefinitionT]]
)
