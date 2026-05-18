"""
Attributes that store collections of data in instance attributes.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.owner import OwnerAttr
from betty.data import ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate.record.object import AttrDefinition
from betty.property import HasProperties

if TYPE_CHECKING:
    from betty.datas.aggregate.collection import CollectionDefinition
    from betty.indicator.selector import Element
    from betty.locale.localizable import ResolvableLocalizable


@final
class CollectionAttrAttr[
    OwnerT: HasProperties,
    MutableCollectionT: Collection[Any],
    ValuesSetT: Iterable,
](OwnerAttr[OwnerT, MutableCollectionT, ValuesSetT]):
    """
    An object attribute that stores its collection of data on owner instances.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[
            CollectionDefinition[MutableCollectionT, ValuesSetT, Element[Any]]
        ],
        *,
        default: Callable[[], ValuesSetT] = tuple,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableCollectionT], bool] | None = None,
        omit_load: bool | None = None,
    ):
        super().__init__(
            AttrDefinition(
                data,
                label=label,
                description=description,
                omit_load=omit_load,
                omit_dump=omit_dump,
            ),
        )
        self.__data_collection = resolve_data_definition(data)
        self.__default_items = default

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        self._set_owner_attr(owner, self.__data_collection.new(self.__default_items()))

    @final
    @override
    def get(self, owner: OwnerT, /) -> MutableCollectionT:
        return self._get_owner_attr(owner)

    @final
    @override
    def set(self, owner: OwnerT, value: ValuesSetT, /) -> None:
        self.__data_collection.replace(self.get(owner), value)
