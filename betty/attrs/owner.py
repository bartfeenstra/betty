"""
Attributes that store data in owner instance attributes.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Any, Final, final, override

from betty.attrs.common import CommonAttr, OptionableCommonAttr
from betty.attrs.default import DefaultAttr
from betty.attrs.optional import OptionalAttr
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.collection import CollectionDefinition
from betty.freezer import is_frozen
from betty.prop import HasProps
from betty.props.setter import SetterProp

if TYPE_CHECKING:
    from betty.datas.aggregate.record import ResolvableFieldDefinition


class __Owner[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](CommonAttr[OwnerT, GetT, SetT, DataDefinitionT]):
    def __init__(
        self,
        field: ResolvableFieldDefinition[OwnerT, GetT, DataDefinitionT],
        *args: Any,
        frozen: bool = False,
        **kwargs: Any,
    ):
        super().__init__(field, *args, **kwargs)
        self._frozen: Final[bool] = frozen

    @final
    def _is_mutable(self, owner: OwnerT, /) -> bool:
        if self._frozen or is_frozen(owner):
            return not owner.is_initialized
        return True

    @final
    @override
    def is_settable(self, owner: OwnerT, /) -> bool:
        return self._is_mutable(owner)

    @final
    @override
    def is_deletable(self, owner: OwnerT, /) -> bool:
        return self._is_mutable(owner)


class _Owner[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    __Owner[OwnerT, GetT, SetT, DataDefinitionT],
    OptionableCommonAttr[OwnerT, GetT, SetT, DataDefinitionT],
):
    @final
    @override
    def default(
        self, default: Callable[[], SetT] | Callable[[OwnerT], SetT], /
    ) -> OptionableCommonAttr[OwnerT, GetT, SetT, DataDefinitionT]:
        return _Default[OwnerT, GetT, SetT, DataDefinitionT](self, default)

    @final
    @override
    def setter[SetterSetT](
        self,
        setter: Callable[[SetterSetT], SetT] | Callable[[OwnerT, SetterSetT], SetT],
        /,
    ) -> OptionableCommonAttr[OwnerT, GetT, SetterSetT, DataDefinitionT]:
        return _Setter[OwnerT, GetT, SetterSetT, DataDefinitionT](setter, proxied=self)

    @final
    @override
    @property
    def optional(
        self,
    ) -> OptionableCommonAttr[OwnerT, GetT | None, SetT | None]:
        return _Optional(self)


class _Default[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    DefaultAttr[OwnerT, GetT, SetT, DataDefinitionT],
    _Owner[OwnerT, GetT, SetT, DataDefinitionT],
):
    pass


class _Optional[OwnerT: HasProps, GetT, SetT](
    OptionalAttr[OwnerT, GetT, SetT],
    _Owner[OwnerT, GetT | None, SetT | None, DataDefinition[GetT | None]],
):
    pass


class _Setter[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    SetterProp[OwnerT, GetT, SetT],
    ProxyAttr[OwnerT, GetT, SetT, DataDefinitionT],
    _Owner[OwnerT, GetT, SetT, DataDefinitionT],
):
    pass


@final
class OwnerAttr[OwnerT: HasProps, T, DataDefinitionT: DataDefinition = DataDefinition](
    _Owner[OwnerT, T, T, DataDefinitionT]
):
    """
    An object attribute that stores its data on owner instances.
    """

    @final
    @override
    def get(self, owner: OwnerT, /) -> T:
        return self._storage.get(owner)

    @override
    def set(self, owner: OwnerT, value: T, /) -> None:
        self._storage.set(owner, value)


class _CollectionOwner[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    __Owner[OwnerT, GetT, SetT, DataDefinitionT],
    CommonAttr[OwnerT, GetT, SetT, DataDefinitionT],
):
    @final
    @override
    def default(
        self, default: Callable[[], SetT] | Callable[[OwnerT], SetT], /
    ) -> CommonAttr[OwnerT, GetT, SetT, DataDefinitionT]:
        return _CollectionDefault[OwnerT, GetT, SetT, DataDefinitionT](self, default)

    @final
    @override
    def setter[SetterSetT](
        self,
        setter: Callable[[SetterSetT], SetT] | Callable[[OwnerT, SetterSetT], SetT],
        /,
    ) -> CommonAttr[OwnerT, GetT, SetterSetT, DataDefinitionT]:
        return _CollectionSetter[OwnerT, GetT, SetterSetT, DataDefinitionT](
            setter, proxied=self
        )


class _CollectionDefault[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    DefaultAttr[OwnerT, GetT, SetT, DataDefinitionT],
    _CollectionOwner[OwnerT, GetT, SetT, DataDefinitionT],
):
    pass


class _CollectionSetter[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    SetterProp[OwnerT, GetT, SetT],
    ProxyAttr[OwnerT, GetT, SetT, DataDefinitionT],
    _CollectionOwner[OwnerT, GetT, SetT, DataDefinitionT],
):
    pass


@final
class CollectionOwnerAttr[
    OwnerT: HasProps,
    GetT: Collection[Any],
    SetT: Iterable,
    DataDefinitionT: CollectionDefinition = CollectionDefinition,
](_CollectionOwner[OwnerT, GetT, SetT, DataDefinitionT]):
    """
    An object attribute that stores its collection of data on owner instances.
    """

    @override
    def pre_init_owner(self, owner: OwnerT, /) -> None:
        super().pre_init_owner(owner)
        self._storage.set(owner, self.field.data.new())

    @override
    def normalize(self, owner: OwnerT, value: SetT, /) -> GetT:
        return self.field.data.new(value)

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self._storage.get(owner)

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.field.data.replace(self.get(owner), value)
