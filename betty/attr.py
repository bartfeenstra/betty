"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final, override

from betty.property import HasProperties, ProxyProperty, SettableProperty

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.datas.aggregate.record.object import AttrDefinition


class Attr[OwnerT: HasProperties, GetT, SetT](SettableProperty[OwnerT, GetT, SetT]):
    """
    An object attribute with a data definition.
    """

    def __init__(self, attr: AttrDefinition[GetT], /):
        self.attr: Final[AttrDefinition[GetT]] = attr
        """
        The attribute's data definition.
        """

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        setattr(owner, f"_{self.property.name}", value)

    @final
    def setter[SetterSetT](
        self, setter: Callable[[SetterSetT], SetT], /
    ) -> Attr[OwnerT, GetT, SetterSetT]:
        """
        Return a new attribute with the given setter.
        """
        return SetterAttr(self, setter)


class ProxyAttr[OwnerT: HasProperties, GetT, SetT](
    ProxyProperty[OwnerT, GetT], Attr[OwnerT, GetT, SetT]
):
    """
    An attribute that proxies another attribute.
    """

    def __init__(
        self,
        proxied: Attr[OwnerT, GetT, SetT],
        *,
        attr: AttrDefinition[GetT] | None = None,
    ):
        super().__init__(proxied.attr if attr is None else attr, proxied=proxied)
        self.__proxied_attr = proxied

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_attr.set(owner, value)


@final
class SetterAttr[OwnerT: HasProperties, GetT, SetT](ProxyAttr[OwnerT, GetT, SetT]):
    """
    An attribute with an additional setter.
    """

    def __init__[ProxiedSetT](
        self,
        proxied: Attr[OwnerT, GetT, ProxiedSetT],
        setter: Callable[[SetT], ProxiedSetT],
    ):
        super().__init__(proxied)
        self.__proxied_setter = proxied
        self.__setter = setter

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__proxied_setter.set(owner, self.__setter(value))
