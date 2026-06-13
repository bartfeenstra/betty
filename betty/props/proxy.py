"""
Proxy properties.
"""

from __future__ import annotations

from typing import Any, override

from betty.prop import HasProps, Prop


class ProxyProp[OwnerT: HasProps, GetT, SetT](Prop[OwnerT, GetT, SetT]):
    """
    A property that proxies another property.
    """

    def __init__(self, *args: Any, proxied: Prop[OwnerT, GetT, SetT], **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__proxied = proxied

    @override
    def __set_name__(self, owner: type[OwnerT], name: str):
        super().__set_name__(owner, name)
        self.__proxied.__set_name__(owner, name)

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self.__proxied.get(owner)

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        return self.__proxied.set(owner, value)

    @override
    def delete(self, owner: OwnerT, /) -> None:
        return self.__proxied.delete(owner)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.__proxied.init_owner(owner)

    @override
    def delete_owner(self, owner: OwnerT, /) -> None:
        super().delete_owner(owner)
        self.__proxied.delete_owner(owner)
