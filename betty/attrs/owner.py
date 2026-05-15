"""
Attributes that store data in instance attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.attr import Attr, ProxyAttr
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.datas.aggregate.record import FieldDefinition


class OwnerAttr[OwnerT: HasProperties, GetT, SetT](Attr[OwnerT, GetT, SetT]):
    """
    An object attribute that stores its data on owner instances.
    """

    @final
    def _owner_attr(self, attr: str) -> str:
        return f"_attr_{self.property.name}_{attr}"

    @final
    def _has_owner_attr(self, owner: OwnerT, /) -> bool:
        """
        Check if the owner has an object attribute.
        """
        return hasattr(owner, self._owner_attr("value"))

    @final
    def _get_owner_attr(self, owner: OwnerT, /) -> GetT:
        """
        Get the value from the owner's object attribute.
        """
        return getattr(owner, self._owner_attr("value"))

    @final
    def _set_owner_attr(self, owner: OwnerT, value: GetT, /) -> None:
        """
        Set the value to the owner's object attribute.
        """
        setattr(owner, self._owner_attr("value"), value)

    def default(self, default: Callable[[], SetT]) -> OwnerAttr[OwnerT, GetT, SetT]:
        """
        Create a new attribute that proxies this one, and sets a default value.
        """
        from betty.attrs.default import DefaultAttr

        return DefaultAttr(self, default)

    @property
    def optional(self) -> OwnerAttr[OwnerT, GetT | None, SetT | None]:
        """
        Return a new attribute like this one, but that also allows ``None``.
        """
        from betty.attrs.optional import Optional

        return Optional(self)

    def setter[SetterSetT](
        self, setter: Callable[[SetterSetT], SetT], /
    ) -> OwnerAttr[OwnerT, GetT, SetterSetT]:
        """
        Return a new attribute like this one, but with the given setter.
        """
        from betty.attrs.setter import SetterAttr

        return SetterAttr(self, setter)


class ProxyOwnerAttr[OwnerT: HasProperties, GetT, SetT](
    ProxyAttr[OwnerT, GetT, SetT], OwnerAttr[OwnerT, GetT, SetT]
):
    """
    An owner attribute that proxies another owner attribute.
    """

    def __init__(
        self,
        proxied: OwnerAttr[OwnerT, GetT, SetT],
        *args: Any,
        field: FieldDefinition[GetT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(proxied, *args, field=field, **kwargs)
        self.__proxied_owner_attr = proxied

    @override
    def default(self, default: Callable[[], SetT]) -> OwnerAttr[OwnerT, GetT, SetT]:
        return self.__proxied_owner_attr.default(default)

    @override
    @property
    def optional(self) -> OwnerAttr[OwnerT, GetT | None, SetT | None]:
        return self.__proxied_owner_attr.optional

    @override
    def setter[SetterSetT](
        self, setter: Callable[[SetterSetT], SetT], /
    ) -> OwnerAttr[OwnerT, GetT, SetterSetT]:
        return self.__proxied_owner_attr.setter(setter)
