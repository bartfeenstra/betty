"""
Attributes that store data in instance attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attr import Attr
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable


class OwnerAttr[OwnerT: HasProperties, GetT, SetT](Attr[OwnerT, GetT, SetT]):
    """
    An object attribute that stores its data on owner instances.
    """

    @final
    def _owner_attr(self, attr: str) -> str:
        return f"_attr_{self.property.name}_{attr}"

    @final
    def _has_owner_attr(self, owner: OwnerT, attr: str = "value", /) -> bool:
        """
        Check if the owner has an object attribute.
        """
        return hasattr(owner, self._owner_attr(attr))

    @final
    def _get_owner_attr(self, owner: OwnerT, attr: str = "value", /) -> GetT:
        """
        Get the value from the owner's object attribute.
        """
        return getattr(owner, self._owner_attr(attr))

    @final
    def _set_owner_attr(
        self, owner: OwnerT, value: GetT, attr: str = "value", /
    ) -> None:
        """
        Set the value to the owner's object attribute.
        """
        setattr(owner, self._owner_attr(attr), value)

    @final
    @property
    def optional(self) -> OwnerAttr[OwnerT, GetT | None, SetT | None]:
        """
        Return a new attribute like this one, but that also allows ``None``.
        """
        from betty.attrs.optional import Optional

        return Optional(self)

    @final
    def setter[SetterSetT](
        self, setter: Callable[[SetterSetT], SetT], /
    ) -> OwnerAttr[OwnerT, GetT, SetterSetT]:
        """
        Return a new attribute like this one, but with the given setter.
        """
        from betty.attrs.setter import SetterAttr

        return SetterAttr(self, setter)
