"""
Keyed collection properties.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, final, override

from betty.attr import AttrProperty
from betty.collection.keyed import MutableKeyedCollection
from betty.descriptor import HasDescriptors
from betty.functools import passthrough

if TYPE_CHECKING:
    from betty.data import Data
    from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
    from betty.locale.localizable import ResolvableLocalizable


class KeyedCollectionAttr[
    MutableKeyedCollectionT: MutableKeyedCollection,
    ValueSetT,
](AttrProperty[HasDescriptors, MutableKeyedCollectionT, Iterable[ValueSetT]]):
    """
    An attribute that contains an :py:class:`betty.collection.keyed.KeyedCollection`.
    """

    _data: KeyedCollectionDefinition[MutableKeyedCollectionT]

    def __init__(
        self,
        data: KeyedCollectionDefinition[MutableKeyedCollectionT]
        | type[Data[KeyedCollectionDefinition[MutableKeyedCollectionT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableKeyedCollectionT], bool] | None = None,
        resolver: Callable[
            [ValueSetT | Iterable[ValueSetT]], Iterable[ValueSetT]
        ] = passthrough,
        default: Callable[[], ValueSetT | Iterable[ValueSetT]] = list,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            default=self._new_default,
        )
        self._values_resolver = resolver
        self._default_values = default

    @final
    def _new_default(self) -> MutableKeyedCollectionT:
        new = self._data.new()
        new.add(*self._values_resolver(self._default_values()))
        return new

    @final
    @override
    def set(self, owner: Any, value: Iterable[ValueSetT], /) -> MutableKeyedCollectionT:
        data = self.get(owner)
        data.clear()
        data.add(*self._values_resolver(value))
        return data
