"""
Settable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attr import Attr
from betty.prop import HasProps

if TYPE_CHECKING:
    from collections.abc import Callable


class SettableAttr[OwnerT: HasProps, GetT, SetT](Attr[OwnerT, GetT, SetT]):
    """
    A settable object attribute.
    """

    def default(
        self, default: Callable[[], SetT] | Callable[[OwnerT], SetT]
    ) -> SettableAttr[OwnerT, GetT, SetT]:
        """
        Create a new attribute that proxies this one, and sets a default value.
        """
        from betty.attrs.default import DefaultAttr

        return DefaultAttr(self, default)

    @property
    def optional(self) -> SettableAttr[OwnerT, GetT | None, SetT | None]:
        """
        Return a new attribute like this one, but that also allows ``None``.
        """
        from betty.attrs.optional import Optional

        return Optional(self)

    def setter[SetterSetT](
        self,
        setter: Callable[[SetterSetT], SetT] | Callable[[OwnerT, SetterSetT], SetT],
        /,
    ) -> SettableAttr[OwnerT, GetT, SetterSetT]:
        """
        Return a new attribute like this one, but with the given setter.
        """
        from betty.attrs.setter import SetterAttr

        return SetterAttr(self, setter)
