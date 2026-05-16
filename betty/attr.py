"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final, override

from betty.functools import passthrough
from betty.property import HasProperties, Property, ProxyProperty

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.datas.aggregate.record.object import AttrDefinition


class Attr[OwnerT: HasProperties, GetT, SetT](Property[OwnerT, GetT]):
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

    @final
    def __set__(self, instance: OwnerT, value: SetT | GetT) -> None:
        self.set(instance, value)

    def set(self, owner: OwnerT, value: SetT, /) -> GetT:
        """
        Set the value on the owner.
        """
        resolved_value = self._resolver(value)
        setattr(owner, f"_{self.property.name}", resolved_value)
        return resolved_value


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
    def set(self, owner: OwnerT, value: SetT, /) -> GetT:
        return self.__proxied_attr.set(owner, value)
