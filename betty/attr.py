"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, override

from betty.functools import passthrough
from betty.property import HasProperties, ProxyProperty, SettableProperty

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.datas.aggregate.record.object import AttrDefinition


class Attr[OwnerT: HasProperties, GetT, SetT](SettableProperty[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(
        self,
        attr: AttrDefinition[GetT],
        *,
        resolver: Callable[[SetT | GetT], GetT] = passthrough,
    ):
        self.attr: Final[AttrDefinition[GetT]] = attr
        """
        The attribute's data definition.
        """
        self._resolver = resolver

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        setattr(owner, f"_{self.property.name}", self._resolver(value))


class ProxyAttr[OwnerT: HasProperties, GetT, SetT](
    ProxyProperty[OwnerT, GetT], Attr[OwnerT, GetT, SetT]
):
    """
    An attribute that proxies another attribute.
    """

    def __init__(
        self,
        attr: AttrDefinition[GetT],
        *args: Any,
        proxied: Attr[OwnerT, GetT, SetT],
        **kwargs: Any,
    ):
        super().__init__(attr, *args, proxied=proxied, **kwargs)
        self.__proxied_attr = proxied

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_attr.set(owner, value)
