"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, override

from betty.prop import HasProps, ProxyProp, SettableProp

if TYPE_CHECKING:
    from betty.datas.aggregate.record import FieldDefinition


class Attr[OwnerT: HasProps, GetT, SetT](SettableProp[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(self, field: FieldDefinition[OwnerT, GetT], /):
        self.field: Final[FieldDefinition[OwnerT, GetT]] = field
        """
        The attribute's field definition.
        """


class ProxyAttr[OwnerT: HasProps, GetT, SetT](
    ProxyProp[OwnerT, GetT], Attr[OwnerT, GetT, SetT]
):
    """
    An attribute that proxies another attribute.
    """

    def __init__(
        self,
        proxied: Attr[OwnerT, GetT, SetT],
        *args: Any,
        field: FieldDefinition[OwnerT, GetT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            proxied.field if field is None else field, *args, proxied=proxied, **kwargs
        )
        self.__proxied_attr = proxied

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_attr.set(owner, value)
