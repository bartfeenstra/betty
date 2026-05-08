"""
Object attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final, override

from betty.data import OptionalDefinition
from betty.datas.aggregate.record.object import Attr as DataAttr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.descriptor import (
    DeletableDescriptor,
    DeletableDescriptorProxy,
    HasDescriptors,
    SettableDescriptor,
    SettableDescriptorProxy,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


class Attr[OwnerT: HasDescriptors, GetT, SetT](
    DataAttr[GetT], SettableDescriptor[OwnerT, GetT, SetT]
):
    """
    An object attribute with a data definition.
    """

    def __init__(self, attr: AttrDefinition[GetT], /):
        self.__attr = attr
        self.__owner_attr: Final[str] = f"_{self.descriptor_name}"

    @final
    @override
    @property
    def attr(self) -> AttrDefinition[GetT]:
        return self.__attr

    @final
    def _get(self, owner: OwnerT, /) -> GetT:
        return getattr(owner, self.__owner_attr)

    @final
    def _set(self, owner: OwnerT, value: SetT, /) -> None:
        setattr(owner, self.__owner_attr, value)

    @final
    def default(self, default: Callable[[OwnerT], SetT], /) -> Attr[OwnerT, GetT, SetT]:
        """
        Return a new attribute with the given default value.
        """
        return DefaultProperty(self, default)


class AttrProperty[OwnerT: HasDescriptors, T](Attr[OwnerT, T, T]):
    """
    A property value stored in an object attribute.
    """

    def __init__(
        self,
        data: DataDefinition[T] | type[Data[DataDefinition[T]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[T], bool] | None = None,
    ):
        super().__init__(
            AttrDefinition(
                data,
                label=label,
                description=description,
                omit_load=omit_load,
                omit_dump=omit_dump,
            )
        )

    @final
    @override
    def get(self, owner: OwnerT, /) -> T:
        return self._get(owner)

    @override
    def set(self, owner: OwnerT, value: T, /) -> None:
        self._set(owner, value)


# @todo A property with a default value is not necessarily settable.
# @todo Examples of this:
# @todo - collections
# @todo - read-only properties
# @todo - computed properties
# @todo
@final
class DefaultProperty[OwnerT: HasDescriptors, GetT, SetT](
    SettableDescriptorProxy[OwnerT, GetT, SetT],
    DeletableDescriptorProxy[OwnerT, GetT],
    Attr[OwnerT, GetT, SetT],
):
    """
    A property with a default value.
    """

    def __init__(
        self,
        proxied: Attr[OwnerT, GetT, SetT],
        default: Callable[[OwnerT], SetT],
        /,
    ):
        super().__init__(proxied)
        self._default = default

    @override
    def init_descriptor(self, owner: OwnerT, /) -> None:
        self._set(owner, self._default(owner))


# @todo This should be refactored into an internal exception for AttrProperty only
@final
class AttrNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.attr.Attr`.
    """


@final
class Optional[OwnerT: HasDescriptors, GetT, SetT](
    SettableDescriptorProxy[OwnerT, GetT | None, SetT | None],
    DeletableDescriptor[OwnerT, GetT | None],
    Attr[OwnerT, GetT | None, SetT | None],
):
    """
    Make another attribute optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: Attr[OwnerT, GetT, SetT], /):
        def _omit_dump(data: GetT | None) -> bool:
            if data is None:
                return True
            if proxied.attr.omit_dump is None:
                return False
            return proxied.attr.omit_dump(data)

        super().__init__(
            proxied,
            AttrDefinition(
                OptionalDefinition(proxied.attr.data),
                label=proxied.attr.label,
                description=proxied.attr.description,
                omit_load=proxied.attr.omit_load,
                omit_dump=_omit_dump,
            ),
        )

    @override
    def init_descriptor(self, owner: OwnerT, /) -> None:
        super().init_descriptor(owner)
        self._set(owner, None)

    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.set(owner, None)
