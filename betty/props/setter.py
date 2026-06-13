"""
Attributes with custom setters.
"""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, final, override

from betty.prop import HasProps, Prop
from betty.props.proxy import ProxyProp

if TYPE_CHECKING:
    from collections.abc import Callable


class SetterProp[OwnerT: HasProps, GetT, SetT](ProxyProp[OwnerT, GetT, SetT]):
    """
    A property with an additional setter.
    """

    def __init__[ProxiedSetT](
        self,
        setter: Callable[[SetT], ProxiedSetT] | Callable[[OwnerT, SetT], ProxiedSetT],
        *,
        proxied: Prop[OwnerT, GetT, ProxiedSetT],
    ):
        super().__init__(proxied=proxied)
        self.__proxied_setter = proxied
        self.__setter: Callable[[OwnerT, SetT], ProxiedSetT] = (
            (
                lambda _, value: setter(
                    value,  # ty:ignore[invalid-argument-type]
                )  # ty:ignore[missing-argument]
            )
            if len(signature(setter).parameters) == 1
            else setter  # ty:ignore[invalid-assignment]
        )

    @final
    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_setter.set(owner, self.__setter(owner, value))
