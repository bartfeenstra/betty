"""
Settable attributes.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from betty.attr import Attr
from betty.data import DataDefinition
from betty.prop import HasProps

if TYPE_CHECKING:
    from collections.abc import Callable


class CommonAttr[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](Attr[OwnerT, GetT, SetT, DataDefinitionT]):
    """
    An object attribute that supports common configuration operations.

    This is a helper mix-in that provides shorthand access to common features to improve Developer Experience (DX).
    """

    @abstractmethod
    def default(
        self, default: Callable[[], SetT] | Callable[[OwnerT], SetT], /
    ) -> CommonAttr[OwnerT, GetT, SetT, DataDefinitionT]:
        """
        Create a new attribute that proxies this one, and sets a default value.
        """

    @property
    @abstractmethod
    def optional(self) -> CommonAttr[OwnerT, GetT | None, SetT | None, DataDefinitionT]:
        """
        Return a new attribute like this one, but that also allows ``None``.
        """

    @abstractmethod
    def setter[SetterSetT](
        self,
        setter: Callable[[SetterSetT], SetT] | Callable[[OwnerT, SetterSetT], SetT],
        /,
    ) -> CommonAttr[OwnerT, GetT, SetterSetT, DataDefinitionT]:
        """
        Return a new attribute like this one, but with the given setter.
        """
