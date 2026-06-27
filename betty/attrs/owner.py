"""
Attributes that store data in owner instance attributes.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from typing import Any, final, override

from betty.attr import Object
from betty.attrs.common import CommonAttr
from betty.attrs.default import DefaultAttr
from betty.attrs.optional import OptionalAttr
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.collection import CollectionDefinition
from betty.props.setter import SetterProp


class _Owner[
    OwnerT: Object,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](CommonAttr[OwnerT, GetT, SetT, DataDefinitionT]):
    @final
    @override
    def default(
        self, default: Callable[[], SetT] | Callable[[OwnerT], SetT], /
    ) -> CommonAttr[OwnerT, GetT, SetT, DataDefinitionT]:
        return _Default[OwnerT, GetT, SetT, DataDefinitionT](self, default)

    @final
    @override
    @property
    def optional(
        self,
    ) -> CommonAttr[OwnerT, GetT | None, SetT | None, DataDefinition[GetT | None]]:
        return _Optional(self)

    @final
    @override
    def setter[SetterSetT](
        self,
        setter: Callable[[SetterSetT], SetT] | Callable[[OwnerT, SetterSetT], SetT],
        /,
    ) -> CommonAttr[OwnerT, GetT, SetterSetT, DataDefinitionT]:
        return _Setter[OwnerT, GetT, SetterSetT, DataDefinitionT](setter, proxied=self)


class _Default[
    OwnerT: Object,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    DefaultAttr[OwnerT, GetT, SetT, DataDefinitionT],
    _Owner[OwnerT, GetT, SetT, DataDefinitionT],
):
    pass


class _Optional[OwnerT: Object, GetT, SetT](
    OptionalAttr[OwnerT, GetT, SetT],
    _Owner[OwnerT, GetT | None, SetT | None, DataDefinition[GetT | None]],
):
    pass


class _Setter[
    OwnerT: Object,
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
class OwnerAttr[OwnerT: Object, T, DataDefinitionT: DataDefinition = DataDefinition](
    _Owner[OwnerT, T, T, DataDefinitionT]
):
    """
    An object attribute that stores its data on owner instances.
    """

    @final
    @override
    def get(self, owner: OwnerT, /) -> T:
        return getattr(owner, self.prop.owner_attr)

    @override
    def set(self, owner: OwnerT, value: T, /) -> None:
        setattr(owner, self.prop.owner_attr, value)


@final
class CollectionOwnerAttr[
    OwnerT: Object,
    GetT: Collection[Any],
    SetT: Iterable,
    DataDefinitionT: CollectionDefinition = CollectionDefinition,
](_Owner[OwnerT, GetT, SetT, DataDefinitionT]):
    """
    An object attribute that stores its collection of data on owner instances.
    """

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        setattr(owner, self.prop.owner_attr, self.field.data.new())

    @override
    def normalize(self, owner: OwnerT, value: SetT, /) -> GetT:
        return self.field.data.new(value)

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return getattr(owner, self.prop.owner_attr)

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.field.data.replace(self.get(owner), value)
