"""
Attributes with custom setters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from sphinx.util.inspect import signature

from betty.attrs.settable import SettableAttr
from betty.prop import HasProps, ProxyProp

if TYPE_CHECKING:
    from collections.abc import Callable


@final
class SetterAttr[OwnerT: HasProps, GetT, SetT](
    ProxyProp[OwnerT, GetT, SetT], SettableAttr[OwnerT, GetT, SetT]
):
    """
    An attribute with an additional setter.
    """

    def __init__[ProxiedSetT](
        self,
        proxied: SettableAttr[OwnerT, GetT, ProxiedSetT],
        setter: Callable[[SetT], ProxiedSetT] | Callable[[OwnerT, SetT], ProxiedSetT],
    ):
        super().__init__(proxied.field, proxied=proxied)
        self._proxied_setter = proxied
        self._setter: Callable[[OwnerT, SetT], ProxiedSetT] = (
            (
                lambda _, value: setter(
                    value,  # ty:ignore[invalid-argument-type]
                )  # ty:ignore[missing-argument]
            )
            if len(signature(setter).parameters) == 1
            else setter  # ty:ignore[invalid-assignment]
        )

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self._proxied_setter.set(owner, self._setter(owner, value))
