"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, override

from betty.property import HasProperties, ProxyProperty, SettableProperty

if TYPE_CHECKING:
    from betty.datas.aggregate.record import FieldDefinition


class Attr[OwnerT: HasProperties, GetT, SetT](SettableProperty[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(self, field: FieldDefinition[GetT], /):
        self.field: Final[FieldDefinition[GetT]] = field
        """
        The attribute's field definition.
        """


class ProxyAttr[OwnerT: HasProperties, GetT, SetT](
    ProxyProperty[OwnerT, GetT], Attr[OwnerT, GetT, SetT]
):
    """
    An attribute that proxies another attribute.
    """

    def __init__(
        self,
        proxied: Attr[OwnerT, GetT, SetT],
        *args: Any,
        field: FieldDefinition[GetT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            proxied.field if field is None else field, *args, proxied=proxied, **kwargs
        )
        self.__proxied_attr = proxied

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_attr.set(owner, value)
