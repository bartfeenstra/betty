"""
Attributes that store data in owner instance attributes.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.default import DefaultCollectionAttr
from betty.attrs.settable import SettableAttr
from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.datas.aggregate.collection import CollectionDefinition
    from betty.indicator.selector import Element
    from betty.locale.localizable import ResolvableLocalizable


@final
class OwnerAttr[OwnerT: HasProps, T](SettableAttr[OwnerT, T, T]):
    """
    An object attribute that stores its data on owner instances.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[DataDefinition[T]],
        /,
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            FieldDefinition(data, label=label, description=description),
        )
        self._data = data

    @final
    @override
    def get(self, owner: OwnerT, /) -> T:
        return getattr(owner, self.prop.owner_attr)

    @override
    def set(self, owner: OwnerT, value: T, /) -> None:
        setattr(owner, self.prop.owner_attr, value)


@final
class CollectionOwnerAttr[
    OwnerT: HasProps,
    MutableCollectionT: Collection[Any],
    ValuesSetT: Iterable,
](SettableAttr[OwnerT, MutableCollectionT, ValuesSetT]):
    """
    An object attribute that stores its collection of data on owner instances.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[
            CollectionDefinition[MutableCollectionT, ValuesSetT, Element[Any]]
        ],
        *,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableCollectionT], bool]
        | Callable[[OwnerT, MutableCollectionT], bool]
        | None = None,
        omit_load: bool = False,
    ):
        super().__init__(
            FieldDefinition(
                data,
                label=label,
                description=description,
                omit_load=omit_load,
                omit_dump=omit_dump,
            ),
        )
        self._data_collection = resolve_data_definition(data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        setattr(owner, self.prop.owner_attr, self._data_collection.new())

    @override
    def get(self, owner: OwnerT, /) -> MutableCollectionT:
        return getattr(owner, self.prop.owner_attr)

    @override
    def set(self, owner: OwnerT, value: ValuesSetT, /) -> None:
        self._data_collection.replace(self.get(owner), value)

    @override
    def default(
        self, default: Callable[[], ValuesSetT] | Callable[[OwnerT], ValuesSetT]
    ) -> SettableAttr[OwnerT, MutableCollectionT, ValuesSetT]:
        return DefaultCollectionAttr(self, default)
