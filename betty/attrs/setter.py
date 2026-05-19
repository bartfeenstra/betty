"""
Attributes with custom setters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.attr import ProxyAttr
from betty.attrs.owner import OwnerAttr
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable


@final
class SetterAttr[OwnerT: HasProperties, GetT, SetT](
    ProxyAttr[OwnerT, GetT, SetT], OwnerAttr[OwnerT, GetT, SetT]
):
    """
    An attribute with an additional setter.
    """

    def __init__[ProxiedSetT](
        self,
        proxied: OwnerAttr[OwnerT, GetT, ProxiedSetT],
        setter: Callable[[SetT], ProxiedSetT],
    ):
        super().__init__(proxied)
        self.__proxied_setter = proxied
        self.__setter = setter

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_setter.set(owner, self.__setter(value))
