"""
Keyed collection properties.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, final, override

from betty.attrs.attr import AttrAttr
from betty.collection.keyed import MutableKeyedCollection
from betty.property import HasProperties

if TYPE_CHECKING:
    from betty.data import ResolvableDataDefinition
    from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
    from betty.locale.localizable import ResolvableLocalizable


class KeyedCollectionAttr[
    OwnerT: HasProperties,
    MutableKeyedCollectionT: MutableKeyedCollection,
    ItemSetT,
](AttrAttr[OwnerT, MutableKeyedCollectionT, Iterable[ItemSetT]]):
    """
    An attribute that contains an :py:class:`betty.collection.keyed.KeyedCollection`.
    """

    _data: KeyedCollectionDefinition[MutableKeyedCollectionT, ItemSetT]

    def __init__(
        self,
        data: ResolvableDataDefinition[
            KeyedCollectionDefinition[MutableKeyedCollectionT, ItemSetT]
        ],
        *,
        default: Callable[[], Iterable[ItemSetT]] = tuple,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableKeyedCollectionT], bool] | None = None,
        omit_load: bool | None = None,
    ):
        super().__init__(
            data,
            default=self._new_default,
            description=description,
            label=label,
            omit_dump=omit_dump,
            omit_load=omit_load,
        )
        self.__default_items = default

    @final
    def _new_default(self) -> MutableKeyedCollectionT:
        return self._data.new(self.__default_items())

    @final
    @override
    def set(self, owner: OwnerT, value: Iterable[ItemSetT], /) -> None:
        self._data.replace(self.get(owner), value)
